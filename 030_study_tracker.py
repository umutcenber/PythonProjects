import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime


# ---------------- DATABASE ----------------

connection = sqlite3.connect("study_tracker.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    minutes INTEGER NOT NULL,
    date TEXT NOT NULL
)
""")

connection.commit()


# ---------------- FUNCTIONS ----------------

def add_session():
    subject = subject_entry.get().strip()
    minutes_text = minutes_entry.get().strip()

    if not subject or not minutes_text:
        messagebox.showerror("Error", "Please fill in all fields.")
        return

    try:
        minutes = int(minutes_text)

        if minutes <= 0:
            raise ValueError

    except ValueError:
        messagebox.showerror(
            "Error",
            "Minutes must be a positive number."
        )
        return

    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    cursor.execute(
        """
        INSERT INTO sessions (subject, minutes, date)
        VALUES (?, ?, ?)
        """,
        (subject, minutes, date)
    )

    connection.commit()

    subject_entry.delete(0, tk.END)
    minutes_entry.delete(0, tk.END)

    refresh_table()
    update_stats()

    messagebox.showinfo(
        "Success",
        "Study session added!"
    )


def refresh_table():
    for item in table.get_children():
        table.delete(item)

    cursor.execute(
        """
        SELECT subject, minutes, date
        FROM sessions
        ORDER BY id DESC
        """
    )

    for session in cursor.fetchall():
        table.insert("", tk.END, values=session)


def update_stats():
    cursor.execute(
        "SELECT COALESCE(SUM(minutes), 0) FROM sessions"
    )

    total_minutes = cursor.fetchone()[0]

    hours = total_minutes // 60
    minutes = total_minutes % 60

    total_label.config(
        text=f"Total study time: {hours}h {minutes}m"
    )


def show_subject_stats():
    cursor.execute("""
        SELECT subject, SUM(minutes)
        FROM sessions
        GROUP BY subject
        ORDER BY SUM(minutes) DESC
    """)

    stats = cursor.fetchall()

    if not stats:
        messagebox.showinfo(
            "Statistics",
            "No study sessions yet."
        )
        return

    text = "Study Time by Subject\n\n"

    for subject, minutes in stats:
        hours = minutes // 60
        remaining = minutes % 60

        text += (
            f"{subject}: "
            f"{hours}h {remaining}m\n"
        )

    messagebox.showinfo("Statistics", text)


# ---------------- GUI ----------------

root = tk.Tk()
root.title("Study Tracker")
root.geometry("750x550")
root.resizable(False, False)


title = tk.Label(
    root,
    text="📚 Study Tracker",
    font=("Arial", 24, "bold")
)

title.pack(pady=20)


form_frame = tk.Frame(root)
form_frame.pack(pady=10)


tk.Label(
    form_frame,
    text="Subject:"
).grid(row=0, column=0, padx=5)


subject_entry = tk.Entry(
    form_frame,
    width=25
)

subject_entry.grid(row=0, column=1, padx=5)


tk.Label(
    form_frame,
    text="Minutes:"
).grid(row=0, column=2, padx=5)


minutes_entry = tk.Entry(
    form_frame,
    width=10
)

minutes_entry.grid(row=0, column=3, padx=5)


add_button = tk.Button(
    form_frame,
    text="Add Session",
    command=add_session
)

add_button.grid(row=0, column=4, padx=10)


# ---------------- TABLE ----------------

table_frame = tk.Frame(root)
table_frame.pack(pady=20)


columns = (
    "Subject",
    "Minutes",
    "Date"
)

table = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings",
    height=12
)

for column in columns:
    table.heading(column, text=column)

table.column("Subject", width=200)
table.column("Minutes", width=100)
table.column("Date", width=200)

table.pack()


# ---------------- STATS ----------------

total_label = tk.Label(
    root,
    text="Total study time: 0h 0m",
    font=("Arial", 14, "bold")
)

total_label.pack(pady=10)


stats_button = tk.Button(
    root,
    text="View Subject Statistics",
    command=show_subject_stats
)

stats_button.pack()


refresh_table()
update_stats()


# ---------------- START ----------------

root.mainloop()


# Close database when application exits
connection.close()