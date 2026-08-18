import json
from datetime import datetime


FILE_NAME = "tasks.json"


# -----------------------------
# DATA MANAGEMENT
# -----------------------------

def load_tasks():
    try:
        with open(FILE_NAME, "r") as file:
            return json.load(file)

    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_tasks(tasks):
    with open(FILE_NAME, "w") as file:
        json.dump(tasks, file, indent=4)


# -----------------------------
# TASK FUNCTIONS
# -----------------------------

def add_task(tasks):
    print("\n" + "=" * 40)
    print("ADD TASK")
    print("=" * 40)

    title = input("Task title: ").strip()

    if not title:
        print("Task title cannot be empty.")
        return

    while True:
        priority = input(
            "Priority (low/medium/high): "
        ).strip().lower()

        if priority in ["low", "medium", "high"]:
            break

        print("Please choose low, medium, or high.")

    while True:
        due_date = input(
            "Due date (YYYY-MM-DD): "
        ).strip()

        try:
            datetime.strptime(due_date, "%Y-%m-%d")
            break

        except ValueError:
            print("Invalid date. Use YYYY-MM-DD.")

    task = {
        "id": get_next_id(tasks),
        "title": title,
        "priority": priority,
        "due_date": due_date,
        "completed": False
    }

    tasks.append(task)
    save_tasks(tasks)

    print("\n✓ Task added successfully.")


def get_next_id(tasks):
    if not tasks:
        return 1

    return max(task["id"] for task in tasks) + 1


def display_task(task):
    status = "x" if task["completed"] else " "

    print(
        f"[{status}] {task['id']}. {task['title']}"
    )

    print(f"    Priority: {task['priority'].upper()}")
    print(f"    Due:      {task['due_date']}")


def view_tasks(tasks):
    if not tasks:
        print("\nNo tasks found.")
        return

    print("\n" + "=" * 50)
    print("TASKS")
    print("=" * 50)

    for task in tasks:
        display_task(task)
        print("-" * 50)


def complete_task(tasks):
    if not tasks:
        print("\nNo tasks available.")
        return

    view_tasks(tasks)

    try:
        task_id = int(input("Enter task ID to complete: "))

    except ValueError:
        print("Invalid ID.")
        return

    for task in tasks:
        if task["id"] == task_id:

            if task["completed"]:
                print("\nTask is already completed.")
                return

            task["completed"] = True
            save_tasks(tasks)

            print("\n✓ Task completed!")
            return

    print("\nTask not found.")


def delete_task(tasks):
    if not tasks:
        print("\nNo tasks available.")
        return

    view_tasks(tasks)

    try:
        task_id = int(input("Enter task ID to delete: "))

    except ValueError:
        print("Invalid ID.")
        return

    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            save_tasks(tasks)

            print("\n✓ Task deleted.")
            return

    print("\nTask not found.")


# -----------------------------
# SEARCH & FILTER
# -----------------------------

def search_tasks(tasks):
    keyword = input(
        "\nSearch for: "
    ).strip().lower()

    results = [
        task
        for task in tasks
        if keyword in task["title"].lower()
    ]

    if not results:
        print("\nNo matching tasks found.")
        return

    print("\n" + "=" * 50)
    print("SEARCH RESULTS")
    print("=" * 50)

    for task in results:
        display_task(task)
        print("-" * 50)


def filter_by_priority(tasks):
    priority = input(
        "\nPriority (low/medium/high): "
    ).strip().lower()

    if priority not in ["low", "medium", "high"]:
        print("Invalid priority.")
        return

    results = [
        task
        for task in tasks
        if task["priority"] == priority
    ]

    if not results:
        print(f"\nNo {priority}-priority tasks found.")
        return

    print(f"\n--- {priority.upper()} PRIORITY TASKS ---")

    for task in results:
        display_task(task)
        print("-" * 50)


def show_overdue_tasks(tasks):
    today = datetime.now().date()

    overdue_tasks = []

    for task in tasks:

        if task["completed"]:
            continue

        due_date = datetime.strptime(
            task["due_date"],
            "%Y-%m-%d"
        ).date()

        if due_date < today:
            overdue_tasks.append(task)

    if not overdue_tasks:
        print("\nNo overdue tasks. Slay. 💅")
        return

    print("\n" + "=" * 50)
    print("OVERDUE TASKS")
    print("=" * 50)

    for task in overdue_tasks:
        display_task(task)
        print("-" * 50)


# -----------------------------
# SORTING
# -----------------------------

def sort_tasks(tasks):
    priority_order = {
        "high": 1,
        "medium": 2,
        "low": 3
    }

    return sorted(
        tasks,
        key=lambda task: (
            task["completed"],
            priority_order[task["priority"]],
            task["due_date"]
        )
    )


# -----------------------------
# MAIN MENU
# -----------------------------

def main():

    tasks = load_tasks()

    while True:

        tasks = sort_tasks(tasks)

        print("\n")
        print("=" * 45)
        print("           TASK MANAGER")
        print("=" * 45)

        print("""
1. Add Task
2. View Tasks
3. Complete Task
4. Delete Task
5. Search Tasks
6. Filter by Priority
7. Show Overdue Tasks
8. Exit
""")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_task(tasks)

        elif choice == "2":
            view_tasks(tasks)

        elif choice == "3":
            complete_task(tasks)

        elif choice == "4":
            delete_task(tasks)

        elif choice == "5":
            search_tasks(tasks)

        elif choice == "6":
            filter_by_priority(tasks)

        elif choice == "7":
            show_overdue_tasks(tasks)

        elif choice == "8":
            print("\nGoodbye! 👋")
            break

        else:
            print("\nInvalid choice. Please select 1-8.")


# -----------------------------
# START PROGRAM
# -----------------------------

if __name__ == "__main__":
    main()