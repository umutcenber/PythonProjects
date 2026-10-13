
import hashlib
import hmac
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header, Query
from pydantic import BaseModel, Field


# ============================================================
# CONFIGURATION
# ============================================================

DATABASE = "projectflow.db"
TOKEN_HOURS = 12

app = FastAPI(
    title="ProjectFlow API",
    description="A project and task management platform",
    version="1.0.0",
)


# ============================================================
# DATABASE
# ============================================================

@contextmanager
def db():
    connection = sqlite3.connect(DATABASE, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tokens (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id)
                ON DELETE CASCADE,
            expires_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL REFERENCES users(id)
                ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id)
                ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'todo',
            priority TEXT NOT NULL DEFAULT 'medium',
            due_date TEXT,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_projects_owner
            ON projects(owner_id);

        CREATE INDEX IF NOT EXISTS idx_tasks_project
            ON tasks(project_id);

        CREATE INDEX IF NOT EXISTS idx_tasks_status
            ON tasks(status);

        CREATE INDEX IF NOT EXISTS idx_tokens_expiry
            ON tokens(expires_at);
        """)


# ============================================================
# SECURITY
# ============================================================

def hash_password(password: str, salt: str) -> str:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=bytes.fromhex(salt),
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    ).hex()


def issue_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expiry = datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)

    with db() as con:
        con.execute(
            "DELETE FROM tokens WHERE expires_at < ?",
            (datetime.now(timezone.utc).isoformat(),),
        )
        con.execute(
            "INSERT INTO tokens VALUES (?, ?, ?)",
            (token_hash, user_id, expiry.isoformat()),
        )

    return token


def current_user(
    authorization: Optional[str] = Header(default=None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Provide a Bearer token")

    token = authorization[7:].strip()
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    with db() as con:
        row = con.execute("""
            SELECT users.id, users.username, tokens.expires_at
            FROM tokens
            JOIN users ON users.id = tokens.user_id
            WHERE tokens.token_hash = ?
        """, (token_hash,)).fetchone()

    if not row:
        raise HTTPException(401, "Invalid token")

    if datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc):
        with db() as con:
            con.execute(
                "DELETE FROM tokens WHERE token_hash = ?",
                (token_hash,),
            )
        raise HTTPException(401, "Token expired")

    return {"id": row["id"], "username": row["username"]}


def require_project(project_id: int, user_id: int):
    with db() as con:
        row = con.execute(
            "SELECT * FROM projects WHERE id = ? AND owner_id = ?",
            (project_id, user_id),
        ).fetchone()

    if not row:
        raise HTTPException(404, "Project not found")

    return row


def require_task(task_id: int, user_id: int):
    with db() as con:
        row = con.execute("""
            SELECT tasks.*, projects.owner_id
            FROM tasks
            JOIN projects ON projects.id = tasks.project_id
            WHERE tasks.id = ? AND projects.owner_id = ?
        """, (task_id, user_id)).fetchone()

    if not row:
        raise HTTPException(404, "Task not found")

    return row


# ============================================================
# REQUEST MODELS
# ============================================================

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str = Field(max_length=128)


class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=2000)


class TaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=3000)
    priority: str = "medium"
    due_date: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=3000)
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None


# ============================================================
# AUTHENTICATION
# ============================================================

@app.post("/auth/register", status_code=201)
def register(data: RegisterRequest):
    salt = secrets.token_hex(16)
    password_hash = hash_password(data.password, salt)

    try:
        with db() as con:
            cursor = con.execute("""
                INSERT INTO users (username, password_hash, salt, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                data.username,
                password_hash,
                salt,
                datetime.now(timezone.utc).isoformat(),
            ))
            user_id = cursor.lastrowid

    except sqlite3.IntegrityError:
        raise HTTPException(409, "Username already exists")

    return {"id": user_id, "username": data.username}


@app.post("/auth/login")
def login(data: LoginRequest):
    with db() as con:
        user = con.execute(
            "SELECT * FROM users WHERE username = ?",
            (data.username,),
        ).fetchone()

    if not user:
        raise HTTPException(401, "Invalid username or password")

    candidate = hash_password(data.password, user["salt"])

    if not hmac.compare_digest(candidate, user["password_hash"]):
        raise HTTPException(401, "Invalid username or password")

    token = issue_token(user["id"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_hours": TOKEN_HOURS,
    }


@app.post("/auth/logout")
def logout(user=Depends(current_user),
           authorization: str = Header()):
    token = authorization[7:].strip()
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    with db() as con:
        con.execute(
            "DELETE FROM tokens WHERE token_hash = ?",
            (token_hash,),
        )

    return {"message": "Logged out"}


@app.get("/auth/me")
def me(user=Depends(current_user)):
    return user


# ============================================================
# PROJECTS
# ============================================================

@app.post("/projects", status_code=201)
def create_project(data: ProjectRequest, user=Depends(current_user)):
    with db() as con:
        cursor = con.execute("""
            INSERT INTO projects (owner_id, name, description, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            user["id"],
            data.name,
            data.description,
            datetime.now(timezone.utc).isoformat(),
        ))

        project_id = cursor.lastrowid

    return {"id": project_id, **data.model_dump()}


@app.get("/projects")
def list_projects(user=Depends(current_user)):
    with db() as con:
        rows = con.execute("""
            SELECT p.*,
                COUNT(t.id) AS total_tasks,
                SUM(CASE WHEN t.status = 'done' THEN 1 ELSE 0 END)
                    AS completed_tasks
            FROM projects p
            LEFT JOIN tasks t ON t.project_id = p.id
            WHERE p.owner_id = ?
            GROUP BY p.id
            ORDER BY p.id DESC
        """, (user["id"],)).fetchall()

    return {"projects": [dict(row) for row in rows]}


@app.get("/projects/{project_id}")
def get_project(project_id: int, user=Depends(current_user)):
    project = require_project(project_id, user["id"])
    return dict(project)


@app.patch("/projects/{project_id}")
def update_project(
    project_id: int,
    data: ProjectRequest,
    user=Depends(current_user),
):
    require_project(project_id, user["id"])

    with db() as con:
        con.execute("""
            UPDATE projects SET name = ?, description = ?
            WHERE id = ? AND owner_id = ?
        """, (
            data.name,
            data.description,
            project_id,
            user["id"],
        ))

    return {"message": "Project updated"}


@app.delete("/projects/{project_id}")
def delete_project(project_id: int, user=Depends(current_user)):
    require_project(project_id, user["id"])

    with db() as con:
        con.execute(
            "DELETE FROM projects WHERE id = ? AND owner_id = ?",
            (project_id, user["id"]),
        )

    return {"message": "Project and its tasks deleted"}


# ============================================================
# TASKS
# ============================================================

VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_STATUSES = {"todo", "in_progress", "done"}


def validate_task_fields(priority, due_date):
    if priority not in VALID_PRIORITIES:
        raise HTTPException(
            422,
            f"Priority must be one of {sorted(VALID_PRIORITIES)}",
        )

    if due_date is not None:
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(422, "due_date must use YYYY-MM-DD")


@app.post("/projects/{project_id}/tasks", status_code=201)
def create_task(
    project_id: int,
    data: TaskRequest,
    user=Depends(current_user),
):
    require_project(project_id, user["id"])
    validate_task_fields(data.priority, data.due_date)

    with db() as con:
        cursor = con.execute("""
            INSERT INTO tasks
            (project_id, title, description, priority, due_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            data.title,
            data.description,
            data.priority,
            data.due_date,
            datetime.now(timezone.utc).isoformat(),
        ))

        task_id = cursor.lastrowid

    return {"id": task_id, "project_id": project_id, **data.model_dump(),
            "status": "todo"}


@app.get("/projects/{project_id}/tasks")
def list_tasks(
    project_id: int,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = Query(default=None, max_length=100),
    user=Depends(current_user),
):
    require_project(project_id, user["id"])

    sql = "SELECT * FROM tasks WHERE project_id = ?"
    params = [project_id]

    if status:
        if status not in VALID_STATUSES:
            raise HTTPException(422, "Invalid status")
        sql += " AND status = ?"
        params.append(status)

    if priority:
        if priority not in VALID_PRIORITIES:
            raise HTTPException(422, "Invalid priority")
        sql += " AND priority = ?"
        params.append(priority)

    if search:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    sql += """
        ORDER BY
        CASE priority
            WHEN 'critical' THEN 1
            WHEN 'high' THEN 2
            WHEN 'medium' THEN 3
            ELSE 4
        END,
        due_date IS NULL,
        due_date ASC,
        id DESC
    """

    with db() as con:
        rows = con.execute(sql, params).fetchall()

    return {"count": len(rows), "tasks": [dict(row) for row in rows]}


@app.patch("/tasks/{task_id}")
def update_task(
    task_id: int,
    data: TaskUpdate,
    user=Depends(current_user),
):
    require_task(task_id, user["id"])
    updates = data.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(400, "No fields provided")

    if "status" in updates and updates["status"] not in VALID_STATUSES:
        raise HTTPException(422, "Invalid status")

    if "priority" in updates and updates["priority"] not in VALID_PRIORITIES:
        raise HTTPException(422, "Invalid priority")

    if "due_date" in updates and updates["due_date"] is not None:
        try:
            datetime.strptime(updates["due_date"], "%Y-%m-%d")
        except ValueError:
            raise HTTPException(422, "due_date must use YYYY-MM-DD")

    allowed = {"title", "description", "status", "priority", "due_date"}
    fields = [key for key in updates if key in allowed]

    assignments = ", ".join(f"{field} = ?" for field in fields)
    values = [updates[field] for field in fields]

    with db() as con:
        con.execute(
            f"UPDATE tasks SET {assignments} WHERE id = ?",
            (*values, task_id),
        )

    return {"message": "Task updated", "fields": fields}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, user=Depends(current_user)):
    require_task(task_id, user["id"])

    with db() as con:
        con.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    return {"message": "Task deleted"}


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/dashboard")
def dashboard(user=Depends(current_user)):
    with db() as con:
        project_count = con.execute(
            "SELECT COUNT(*) FROM projects WHERE owner_id = ?",
            (user["id"],),
        ).fetchone()[0]

        task_stats = con.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN t.status = 'todo' THEN 1 ELSE 0 END) AS todo,
                SUM(CASE WHEN t.status = 'in_progress' THEN 1 ELSE 0 END)
                    AS in_progress,
                SUM(CASE WHEN t.status = 'done' THEN 1 ELSE 0 END) AS done,
                SUM(CASE
                    WHEN t.due_date < ? AND t.status != 'done'
                    THEN 1 ELSE 0
                END) AS overdue
            FROM tasks t
            JOIN projects p ON p.id = t.project_id
            WHERE p.owner_id = ?
        """, (
            datetime.now(timezone.utc).date().isoformat(),
            user["id"],
        )).fetchone()

    stats = dict(task_stats)

    for key, value in stats.items():
        stats[key] = value or 0

    total = stats["total"]
    stats["completion_rate"] = (
        round(stats["done"] / total * 100, 2) if total else 0
    )

    return {
        "username": user["username"],
        "projects": project_count,
        "tasks": stats,
    }


# ============================================================
# ENTRY POINT
# ============================================================

@app.get("/")
def home():
    return {
        "application": "ProjectFlow",
        "version": "1.0.0",
        "documentation": "/docs",
    }


initialize_database()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
