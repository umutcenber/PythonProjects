
"""
WEEK 14 — CHRONOS
Distributed Event Processing Engine

Single-file asynchronous event processing system.

Install:
    pip install

Run:
    python Week14_DistributedEventProcessingEngine.py

Custom workers:
    python Week14_DistributedEventProcessingEngine.py --workers 8

Inspect:
    python Week14_DistributedEventProcessingEngine.py --inspect

Export:
    python Week14_DistributedEventProcessingEngine.py --export json

WARNING:
    This is an educational single-machine simulation of a distributed
    event-processing architecture, not a production distributed cluster.
"""

import argparse
import asyncio
import csv
import hashlib
import json
import logging
import random
import sqlite3
import statistics
import time
import uuid

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DATABASE = Path("chronos.db")

MAX_RETRIES = 4
BASE_RETRY_DELAY = 1.0
QUEUE_SIZE = 1000
RATE_LIMIT = 20

PRIORITIES = {
    "critical": 0,
    "high": 1,
    "normal": 2,
    "low": 3,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("Chronos")


# ============================================================
# DATABASE
# ============================================================

class Storage:

    def __init__(self, path=DATABASE):
        self.path = str(path)
        self.initialize()

    def connect(self):
        connection = sqlite3.connect(
            self.path,
            timeout=30,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialize(self):
        with self.connect() as db:

            db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    created_at REAL NOT NULL,
                    started_at REAL,
                    completed_at REAL,
                    next_retry_at REAL,
                    worker_id TEXT,
                    error TEXT,
                    idempotency_key TEXT UNIQUE
                )
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_status
                ON events(status, priority, created_at)
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS event_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    created_at REAL NOT NULL
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_id TEXT NOT NULL,
                    event_id TEXT,
                    processing_time REAL,
                    success INTEGER,
                    created_at REAL NOT NULL
                )
            """)

    def log(self, event_id, action, details=None):
        with self.connect() as db:
            db.execute("""
                INSERT INTO event_logs(
                    event_id, action, details, created_at
                )
                VALUES (?, ?, ?, ?)
            """, (
                event_id,
                action,
                json.dumps(details) if details is not None else None,
                time.time(),
            ))

    def create_event(
        self,
        event_type,
        payload,
        priority="normal",
        idempotency_key=None,
    ):
        if priority not in PRIORITIES:
            raise ValueError("Invalid priority.")

        event_id = str(uuid.uuid4())

        try:
            with self.connect() as db:
                db.execute("""
                    INSERT INTO events(
                        id, event_type, payload, priority,
                        status, created_at, idempotency_key
                    )
                    VALUES (?, ?, ?, ?, 'pending', ?, ?)
                """, (
                    event_id,
                    event_type,
                    json.dumps(payload),
                    PRIORITIES[priority],
                    time.time(),
                    idempotency_key,
                ))

        except sqlite3.IntegrityError:
            if idempotency_key:
                with self.connect() as db:
                    existing = db.execute(
                        "SELECT id FROM events WHERE idempotency_key = ?",
                        (idempotency_key,),
                    ).fetchone()

                if existing:
                    return existing["id"]

            raise

        self.log(event_id, "created", {
            "event_type": event_type,
            "priority": priority,
        })

        return event_id

    def get_event(self, event_id):
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM events WHERE id = ?",
                (event_id,),
            ).fetchone()

        return dict(row) if row else None

    def claim_event(self, worker_id):
        """
        Atomically claim one pending event.
        SQLite transaction prevents two workers from claiming
        the same event.
        """
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")

            row = db.execute("""
                SELECT id
                FROM events
                WHERE status = 'pending'
                  AND (next_retry_at IS NULL OR next_retry_at <= ?)
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
            """, (time.time(),)).fetchone()

            if not row:
                return None

            event_id = row["id"]

            result = db.execute("""
                UPDATE events
                SET status = 'processing',
                    started_at = ?,
                    worker_id = ?
                WHERE id = ? AND status = 'pending'
            """, (
                time.time(),
                worker_id,
                event_id,
            ))

            if result.rowcount != 1:
                return None

            event = db.execute(
                "SELECT * FROM events WHERE id = ?",
                (event_id,),
            ).fetchone()

        self.log(event_id, "claimed", {"worker_id": worker_id})

        return dict(event)

    def complete_event(self, event_id):
        with self.connect() as db:
            db.execute("""
                UPDATE events
                SET status = 'completed',
                    completed_at = ?,
                    error = NULL
                WHERE id = ?
            """, (time.time(), event_id))

        self.log(event_id, "completed")

    def fail_event(self, event, error):
        attempts = event["attempts"] + 1

        if attempts >= MAX_RETRIES:
            status = "dead"
            retry_at = None
        else:
            status = "pending"
            delay = BASE_RETRY_DELAY * (2 ** (attempts - 1))
            delay += random.uniform(0, 0.25)
            retry_at = time.time() + delay

        with self.connect() as db:
            db.execute("""
                UPDATE events
                SET status = ?,
                    attempts = ?,
                    error = ?,
                    next_retry_at = ?
                WHERE id = ?
            """, (
                status,
                attempts,
                str(error)[:1000],
                retry_at,
                event["id"],
            ))

        self.log(event["id"], "failed", {
            "attempt": attempts,
            "status": status,
            "error": str(error),
        })

    def record_metric(
        self,
        worker_id,
        event_id,
        duration,
        success,
    ):
        with self.connect() as db:
            db.execute("""
                INSERT INTO metrics(
                    worker_id, event_id,
                    processing_time, success, created_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                worker_id,
                event_id,
                duration,
                int(success),
                time.time(),
            ))

    def stats(self):
        with self.connect() as db:
            rows = db.execute("""
                SELECT status, COUNT(*) AS total
                FROM events
                GROUP BY status
            """).fetchall()

            metrics = db.execute("""
                SELECT
                    COUNT(*) AS total,
                    AVG(processing_time) AS avg_time,
                    MAX(processing_time) AS max_time,
                    SUM(success) AS successful
                FROM metrics
            """).fetchone()

            workers = db.execute("""
                SELECT worker_id, COUNT(*) AS processed
                FROM metrics
                GROUP BY worker_id
            """).fetchall()

        status_counts = {
            row["status"]: row["total"]
            for row in rows
        }

        return {
            "statuses": status_counts,
            "metrics": dict(metrics),
            "workers": [dict(row) for row in workers],
        }

    def list_dead_events(self):
        with self.connect() as db:
            rows = db.execute("""
                SELECT *
                FROM events
                WHERE status = 'dead'
                ORDER BY created_at DESC
            """).fetchall()

        return [dict(row) for row in rows]

    def retry_dead_event(self, event_id):
        with self.connect() as db:
            result = db.execute("""
                UPDATE events
                SET status = 'pending',
                    attempts = 0,
                    error = NULL,
                    next_retry_at = NULL,
                    worker_id = NULL
                WHERE id = ? AND status = 'dead'
            """, (event_id,))

        if result.rowcount:
            self.log(event_id, "manually_requeued")

        return result.rowcount == 1

    def export(self, format_name):
        with self.connect() as db:
            rows = db.execute("""
                SELECT *
                FROM events
                ORDER BY created_at
            """).fetchall()

        records = [dict(row) for row in rows]

        if format_name == "json":
            Path("chronos_export.json").write_text(
                json.dumps(records, indent=4),
                encoding="utf-8",
            )

        elif format_name == "csv":
            if not records:
                Path("chronos_export.csv").write_text(
                    "",
                    encoding="utf-8",
                )
                return

            with open(
                "chronos_export.csv",
                "w",
                newline="",
                encoding="utf-8",
            ) as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=records[0].keys(),
                )
                writer.writeheader()
                writer.writerows(records)

        else:
            raise ValueError("Export format must be json or csv.")


# ============================================================
# EVENT HANDLERS
# ============================================================

class EventHandlers:

    def __init__(self):
        self.handlers = {
            "user.created": self.user_created,
            "payment.processed": self.payment_processed,
            "analytics.recorded": self.analytics_recorded,
            "system.alert": self.system_alert,
            "demo.unstable": self.unstable_event,
        }

    async def execute(self, event):
        handler = self.handlers.get(event["event_type"])

        if handler is None:
            raise ValueError(
                f"Unknown event type: {event['event_type']}"
            )

        payload = json.loads(event["payload"])

        await handler(payload)

    async def user_created(self, payload):
        await asyncio.sleep(random.uniform(0.1, 0.4))
        logger.info("User created: %s", payload.get("username"))

    async def payment_processed(self, payload):
        await asyncio.sleep(random.uniform(0.2, 0.6))
        logger.info(
            "Payment processed: %s",
            payload.get("transaction_id"),
        )

    async def analytics_recorded(self, payload):
        await asyncio.sleep(random.uniform(0.05, 0.2))
        logger.info(
            "Analytics event: %s",
            payload.get("metric"),
        )

    async def system_alert(self, payload):
        await asyncio.sleep(0.1)
        logger.warning(
            "SYSTEM ALERT: %s",
            payload.get("message"),
        )

    async def unstable_event(self, payload):
        await asyncio.sleep(0.2)

        failure_probability = payload.get(
            "failure_probability",
            0.7,
        )

        if random.random() < failure_probability:
            raise RuntimeError("Simulated temporary processing failure")

        logger.info("Unstable event eventually succeeded.")


# ============================================================
# RATE LIMITER
# ============================================================

class TokenBucket:

    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate
        self.updated_at = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()

            elapsed = now - self.updated_at

            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate,
            )

            self.updated_at = now

            if self.tokens < 1:
                return False

            self.tokens -= 1
            return True


# ============================================================
# WORKER
# ============================================================

class Worker:

    def __init__(
        self,
        worker_id,
        storage,
        handlers,
        rate_limiter,
    ):
        self.worker_id = worker_id
        self.storage = storage
        self.handlers = handlers
        self.rate_limiter = rate_limiter

        self.running = True
        self.processed = 0
        self.failed = 0

    async def process(self, event):
        started = time.perf_counter()
        success = False

        try:
            await self.handlers.execute(event)

            self.storage.complete_event(event["id"])

            self.processed += 1
            success = True

        except Exception as error:
            self.failed += 1

            logger.error(
                "[%s] Event %s failed: %s",
                self.worker_id,
                event["id"],
                error,
            )

            self.storage.fail_event(event, error)

        finally:
            duration = time.perf_counter() - started

            self.storage.record_metric(
                self.worker_id,
                event["id"],
                duration,
                success,
            )

    async def run(self):
        logger.info("%s started.", self.worker_id)

        while self.running:
            allowed = await self.rate_limiter.acquire()

            if not allowed:
                await asyncio.sleep(0.05)
                continue

            event = self.storage.claim_event(self.worker_id)

            if event is None:
                await asyncio.sleep(0.1)
                continue

            await self.process(event)

        logger.info("%s stopped.", self.worker_id)

    def stop(self):
        self.running = False


# ============================================================
# EVENT PROCESSING ENGINE
# ============================================================

class Chronos:

    def __init__(self, worker_count=4):
        self.storage = Storage()
        self.handlers = EventHandlers()

        self.worker_count = worker_count

        self.rate_limiter = TokenBucket(
            capacity=RATE_LIMIT,
            refill_rate=RATE_LIMIT,
        )

        self.workers = [
            Worker(
                f"worker-{index + 1}",
                self.storage,
                self.handlers,
                self.rate_limiter,
            )
            for index in range(worker_count)
        ]

        self.tasks = []

    def publish(
        self,
        event_type,
        payload,
        priority="normal",
        idempotency_key=None,
    ):
        return self.storage.create_event(
            event_type,
            payload,
            priority,
            idempotency_key,
        )

    def publish_batch(self, events):
        identifiers = []

        for event in events:
            identifier = self.publish(
                event["type"],
                event["payload"],
                event.get("priority", "normal"),
                event.get("idempotency_key"),
            )

            identifiers.append(identifier)

        return identifiers

    async def start(self):
        self.tasks = [
            asyncio.create_task(worker.run())
            for worker in self.workers
        ]

        logger.info(
            "Chronos running with %s workers.",
            self.worker_count,
        )

    async def stop(self):
        for worker in self.workers:
            worker.stop()

        await asyncio.gather(
            *self.tasks,
            return_exceptions=True,
        )

        logger.info("Chronos shutdown complete.")

    async def wait_until_idle(self, timeout=30):
        """
        Wait until no pending or processing events remain.
        Dead events are considered finished.
        """
        started = time.monotonic()

        while time.monotonic() - started < timeout:
            with self.storage.connect() as db:
                row = db.execute("""
                    SELECT COUNT(*) AS total
                    FROM events
                    WHERE status IN ('pending', 'processing')
                """).fetchone()

            if row["total"] == 0:
                return True

            await asyncio.sleep(0.2)

        return False

    def dashboard(self):
        stats = self.storage.stats()

        statuses = stats["statuses"]
        metrics = stats["metrics"]

        print("\n" + "=" * 55)
        print("                CHRONOS DASHBOARD")
        print("=" * 55)

        for status in [
            "pending",
            "processing",
            "completed",
            "dead",
        ]:
            print(
                f"{status.upper():15} "
                f"{statuses.get(status, 0):>8}"
            )

        print("-" * 55)

        print(
            "Average processing time: "
            f"{metrics['avg_time'] or 0:.4f}s"
        )

        print(
            "Maximum processing time: "
            f"{metrics['max_time'] or 0:.4f}s"
        )

        print(
            "Successful attempts: "
            f"{metrics['successful'] or 0}"
        )

        print("\nWORKER PERFORMANCE")

        for worker in stats["workers"]:
            print(
                f"{worker['worker_id']:15} "
                f"{worker['processed']} events"
            )

        print("=" * 55)


# ============================================================
# DEMONSTRATION
# ============================================================

def generate_demo_events(count=100):
    event_types = [
        "user.created",
        "payment.processed",
        "analytics.recorded",
        "system.alert",
        "demo.unstable",
    ]

    priorities = [
        "critical",
        "high",
        "normal",
        "low",
    ]

    events = []

    for index in range(count):
        event_type = random.choice(event_types)

        payload = {
            "event_number": index,
            "username": f"user_{index}",
            "transaction_id": str(uuid.uuid4()),
            "metric": "page_views",
            "message": f"Demo event {index}",
            "failure_probability": 0.65,
        }

        events.append({
            "type": event_type,
            "payload": payload,
            "priority": random.choices(
                priorities,
                weights=[5, 15, 60, 20],
            )[0],
            "idempotency_key": f"demo-event-{index}",
        })

    return events


async def run_demo(worker_count):
    engine = Chronos(worker_count)

    events = generate_demo_events(100)

    print(f"\nPublishing {len(events)} events...")

    engine.publish_batch(events)

    await engine.start()

    finished = await engine.wait_until_idle(timeout=90)

    if not finished:
        logger.warning(
            "Processing did not finish before the timeout."
        )

    engine.dashboard()

    dead_events = engine.storage.list_dead_events()

    print(f"\nDead Letter Queue: {len(dead_events)} event(s)")

    await engine.stop()


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Chronos Distributed Event Processing Engine"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--inspect",
        action="store_true",
    )

    parser.add_argument(
        "--export",
        choices=["json", "csv"],
    )

    parser.add_argument(
        "--retry-dead",
        type=str,
    )

    args = parser.parse_args()

    if not 1 <= args.workers <= 32:
        parser.error("Workers must be between 1 and 32.")

    storage = Storage()

    if args.inspect:
        engine = Chronos(args.workers)
        engine.dashboard()

    elif args.export:
        storage.export(args.export)
        print(f"Export completed: chronos_export.{args.export}")

    elif args.retry_dead:
        success = storage.retry_dead_event(args.retry_dead)

        if success:
            print("Event successfully returned to the queue.")
        else:
            print("Event not found or is not in the dead queue.")

    else:
        asyncio.run(run_demo(args.workers))


if __name__ == "__main__":
    main()
