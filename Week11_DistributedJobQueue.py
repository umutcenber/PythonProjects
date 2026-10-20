
import argparse
import asyncio
import json
import logging
import sqlite3
import time
import uuid

from datetime import datetime, timezone
from typing import Any


DATABASE = "taskforge.db"
WORKER_COUNT = 3
MAX_RETRIES = 3
POLL_INTERVAL = 0.5
JOB_TIMEOUT = 15

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("taskforge")


# ============================================================
# UTILITIES
# ============================================================

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect():
    con = sqlite3.connect(DATABASE, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout = 10000")
    return con


# ============================================================
# PERSISTENT JOB STORE
# ============================================================

class JobStore:

    def initialize(self):
        with connect() as con:
            con.execute("PRAGMA journal_mode = WAL")

            con.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER NOT NULL DEFAULT 5,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 3,
                    result TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    available_at REAL NOT NULL,
                    worker_id TEXT
                )
            """)

            con.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_ready
                ON jobs(status, available_at, priority)
            """)

            # Recover jobs left running after an unexpected shutdown.
            con.execute("""
                UPDATE jobs
                SET status = 'pending',
                    worker_id = NULL,
                    started_at = NULL,
                    available_at = ?
                WHERE status = 'running'
            """, (time.time(),))

    def enqueue(
        self,
        job_type: str,
        payload: dict,
        priority: int = 5,
        max_retries: int = MAX_RETRIES,
    ) -> str:

        job_id = str(uuid.uuid4())

        with connect() as con:
            con.execute("""
                INSERT INTO jobs (
                    id, job_type, payload, status, priority,
                    max_retries, created_at, available_at
                )
                VALUES (?, ?, ?, 'pending', ?, ?, ?, ?)
            """, (
                job_id,
                job_type,
                json.dumps(payload),
                priority,
                max_retries,
                utc_now(),
                time.time(),
            ))

        return job_id

    def claim(self, worker_id: str):
        """
        Atomically claim one available job.
        BEGIN IMMEDIATE serializes competing SQLite writers.
        """

        con = connect()

        try:
            con.execute("BEGIN IMMEDIATE")

            row = con.execute("""
                SELECT *
                FROM jobs
                WHERE status = 'pending'
                  AND available_at <= ?
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
            """, (time.time(),)).fetchone()

            if row is None:
                con.commit()
                return None

            cursor = con.execute("""
                UPDATE jobs
                SET status = 'running',
                    attempts = attempts + 1,
                    started_at = ?,
                    worker_id = ?
                WHERE id = ? AND status = 'pending'
            """, (utc_now(), worker_id, row["id"]))

            if cursor.rowcount != 1:
                con.rollback()
                return None

            claimed = con.execute(
                "SELECT * FROM jobs WHERE id = ?",
                (row["id"],),
            ).fetchone()

            con.commit()
            return dict(claimed)

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    def complete(self, job_id: str, result: Any):
        with connect() as con:
            con.execute("""
                UPDATE jobs
                SET status = 'completed',
                    result = ?,
                    error = NULL,
                    finished_at = ?,
                    worker_id = NULL
                WHERE id = ? AND status = 'running'
            """, (
                json.dumps(result),
                utc_now(),
                job_id,
            ))

    def fail(self, job: dict, error: str):
        should_retry = job["attempts"] <= job["max_retries"]

        if should_retry:
            delay = min(2 ** job["attempts"], 60)

            with connect() as con:
                con.execute("""
                    UPDATE jobs
                    SET status = 'pending',
                        error = ?,
                        available_at = ?,
                        worker_id = NULL,
                        started_at = NULL
                    WHERE id = ? AND status = 'running'
                """, (
                    error[:2000],
                    time.time() + delay,
                    job["id"],
                ))

            logger.warning(
                "Retrying job %s in %ss",
                job["id"][:8],
                delay,
            )

        else:
            with connect() as con:
                con.execute("""
                    UPDATE jobs
                    SET status = 'failed',
                        error = ?,
                        finished_at = ?,
                        worker_id = NULL
                    WHERE id = ? AND status = 'running'
                """, (
                    error[:2000],
                    utc_now(),
                    job["id"],
                ))

            logger.error(
                "Job %s permanently failed",
                job["id"][:8],
            )

    def get(self, job_id: str):
        with connect() as con:
            row = con.execute(
                "SELECT * FROM jobs WHERE id = ?",
                (job_id,),
            ).fetchone()

        return dict(row) if row else None

    def list_jobs(self, limit: int = 20):
        with connect() as con:
            rows = con.execute("""
                SELECT id, job_type, status, priority,
                       attempts, created_at, error
                FROM jobs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()

        return [dict(row) for row in rows]

    def statistics(self):
        with connect() as con:
            rows = con.execute("""
                SELECT status, COUNT(*) AS count
                FROM jobs
                GROUP BY status
            """).fetchall()

        stats = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
        }

        for row in rows:
            stats[row["status"]] = row["count"]

        stats["total"] = sum(stats.values())
        return stats


# ============================================================
# JOB HANDLERS
# ============================================================

async def job_sum(payload: dict):
    numbers = payload.get("numbers")

    if not isinstance(numbers, list) or not numbers:
        raise ValueError("'numbers' must be a non-empty list")

    if any(
        isinstance(number, bool)
        or not isinstance(number, (int, float))
        for number in numbers
    ):
        raise ValueError("All numbers must be numeric")

    await asyncio.sleep(0.2)

    return {
        "operation": "sum",
        "count": len(numbers),
        "result": sum(numbers),
    }


async def job_text_analysis(payload: dict):
    text = payload.get("text")

    if not isinstance(text, str):
        raise ValueError("'text' must be a string")

    words = text.split()

    await asyncio.sleep(0.2)

    return {
        "characters": len(text),
        "words": len(words),
        "unique_words": len(set(word.lower() for word in words)),
        "average_word_length": (
            round(sum(len(word) for word in words) / len(words), 2)
            if words else 0
        ),
    }


async def job_wait(payload: dict):
    seconds = payload.get("seconds", 1)

    if (
        isinstance(seconds, bool)
        or not isinstance(seconds, (int, float))
        or not 0 <= seconds <= 30
    ):
        raise ValueError("'seconds' must be between 0 and 30")

    await asyncio.sleep(seconds)

    return {"waited_seconds": seconds}


async def job_simulated_failure(payload: dict):
    """
    Demonstrates retry behavior.
    Fails a configurable number of times before succeeding.
    """

    fail_times = payload.get("fail_times", 2)
    attempt = payload.get("_attempt", 1)

    if not isinstance(fail_times, int) or not 0 <= fail_times <= 10:
        raise ValueError("'fail_times' must be an integer from 0 to 10")

    if attempt <= fail_times:
        raise RuntimeError(f"Intentional test failure on attempt {attempt}")

    return {"message": "Eventually succeeded", "attempt": attempt}


HANDLERS = {
    "sum": job_sum,
    "text_analysis": job_text_analysis,
    "wait": job_wait,
    "simulated_failure": job_simulated_failure,
}


# ============================================================
# ASYNC WORKERS
# ============================================================

class Worker:

    def __init__(self, store: JobStore, worker_number: int):
        self.store = store
        self.worker_id = f"worker-{worker_number}"

    async def execute(self, job: dict):
        job_type = job["job_type"]
        handler = HANDLERS.get(job_type)

        if handler is None:
            self.store.fail(
                job,
                f"Unknown job type: {job_type}",
            )
            return

        payload = json.loads(job["payload"])

        if job_type == "simulated_failure":
            payload["_attempt"] = job["attempts"]

        logger.info(
            "%s executing %s (%s)",
            self.worker_id,
            job_type,
            job["id"][:8],
        )

        try:
            result = await asyncio.wait_for(
                handler(payload),
                timeout=JOB_TIMEOUT,
            )

            self.store.complete(job["id"], result)

            logger.info(
                "%s completed %s",
                self.worker_id,
                job["id"][:8],
            )

        except Exception as error:
            self.store.fail(
                job,
                f"{type(error).__name__}: {error}",
            )

    async def run(self, stop_event: asyncio.Event):
        while not stop_event.is_set():
            job = await asyncio.to_thread(
                self.store.claim,
                self.worker_id,
            )

            if job is None:
                try:
                    await asyncio.wait_for(
                        stop_event.wait(),
                        timeout=POLL_INTERVAL,
                    )
                except asyncio.TimeoutError:
                    pass

                continue

            await self.execute(job)


# ============================================================
# JOB QUEUE SERVICE
# ============================================================

class JobQueue:
    def __init__(self):
        self.store = JobStore()
        self.store.initialize()

    def submit(self, job_type, payload, priority=5, retries=MAX_RETRIES):
        if job_type not in HANDLERS:
            raise ValueError(
                f"Unknown job type. Available: {', '.join(HANDLERS)}"
            )

        if not 1 <= priority <= 10:
            raise ValueError("Priority must be between 1 and 10")

        if not 0 <= retries <= 10:
            raise ValueError("Retries must be between 0 and 10")

        return self.store.enqueue(
            job_type,
            payload,
            priority,
            retries,
        )

    async def run_workers(self, worker_count=WORKER_COUNT):
        stop_event = asyncio.Event()

        workers = [
            Worker(self.store, number)
            for number in range(1, worker_count + 1)
        ]

        tasks = [
            asyncio.create_task(worker.run(stop_event))
            for worker in workers
        ]

        logger.info("Started %s workers", worker_count)

        try:
            await asyncio.gather(*tasks)
        finally:
            stop_event.set()

            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)


# ============================================================
# CLI
# ============================================================

def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        description="TaskForge: persistent asynchronous job queue"
    )

    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("worker", help="Start asynchronous workers")
    commands.add_parser("stats", help="Show queue statistics")
    commands.add_parser("list", help="List recent jobs")

    status_parser = commands.add_parser("status", help="Inspect a job")
    status_parser.add_argument("job_id")

    submit_parser = commands.add_parser("submit", help="Submit a job")
    submit_parser.add_argument("job_type", choices=HANDLERS.keys())
    submit_parser.add_argument(
        "--payload",
        default="{}",
        help='JSON payload, e.g. \'{"numbers":[1,2,3]}\'',
    )
    submit_parser.add_argument("--priority", type=int, default=5)
    submit_parser.add_argument("--retries", type=int, default=MAX_RETRIES)

    args = parser.parse_args()
    queue = JobQueue()

    if args.command == "worker":
        try:
            asyncio.run(queue.run_workers())
        except KeyboardInterrupt:
            logger.info("Worker shutdown requested")

    elif args.command == "submit":
        try:
            payload = json.loads(args.payload)

            if not isinstance(payload, dict):
                raise ValueError("Payload must be a JSON object")

            job_id = queue.submit(
                args.job_type,
                payload,
                args.priority,
                args.retries,
            )

            print_json({
                "job_id": job_id,
                "status": "pending",
            })

        except (json.JSONDecodeError, ValueError) as error:
            parser.error(str(error))

    elif args.command == "status":
        job = queue.store.get(args.job_id)

        if job is None:
            print("Job not found.")
        else:
            print_json(job)

    elif args.command == "list":
        print_json(queue.store.list_jobs())

    elif args.command == "stats":
        print_json(queue.store.statistics())


if __name__ == "__main__":
    main()
