import re
from collections import Counter


LOG_FILE = "server.log"


# -----------------------------
# LOG FILE
# -----------------------------

def create_sample_log():
    sample_logs = [
        "2026-08-25 09:15:22 INFO User logged in",
        "2026-08-25 09:16:03 INFO User opened dashboard",
        "2026-08-25 09:17:45 WARNING High memory usage",
        "2026-08-25 09:18:12 ERROR Database connection failed",
        "2026-08-25 09:20:33 INFO User logged out",
        "2026-08-25 09:21:10 ERROR File not found",
        "2026-08-25 09:22:48 WARNING Slow response time",
        "2026-08-25 09:23:55 INFO User logged in",
        "2026-08-25 09:25:31 ERROR Database connection failed",
        "2026-08-25 09:27:02 INFO User updated profile",
        "2026-08-25 09:28:41 WARNING High memory usage",
        "2026-08-25 09:30:15 ERROR Timeout",
        "2026-08-25 09:31:22 INFO User logged out",
        "2026-08-25 09:32:17 ERROR File not found",
        "2026-08-25 09:33:45 INFO User logged in",
    ]

    with open(LOG_FILE, "w") as file:
        for log in sample_logs:
            file.write(log + "\n")


def read_logs():
    try:
        with open(LOG_FILE, "r") as file:
            return file.readlines()

    except FileNotFoundError:
        print("Log file not found.")
        return []


# -----------------------------
# LOG PARSING
# -----------------------------

def parse_log(log):
    pattern = r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}) (\w+) (.+)"

    match = re.match(pattern, log.strip())

    if match:
        date, time, level, message = match.groups()

        return {
            "date": date,
            "time": time,
            "level": level,
            "message": message
        }

    return None


def parse_all_logs(logs):
    parsed_logs = []

    for log in logs:
        parsed = parse_log(log)

        if parsed:
            parsed_logs.append(parsed)

    return parsed_logs


# -----------------------------
# ANALYSIS
# -----------------------------

def count_log_levels(logs):
    levels = Counter(
        log["level"]
        for log in logs
    )

    return levels


def count_errors(logs):
    errors = Counter(
        log["message"]
        for log in logs
        if log["level"] == "ERROR"
    )

    return errors


def get_error_rate(logs):
    if not logs:
        return 0

    error_count = sum(
        1
        for log in logs
        if log["level"] == "ERROR"
    )

    return (error_count / len(logs)) * 100


def get_logs_by_level(logs, level):
    return [
        log
        for log in logs
        if log["level"].lower() == level.lower()
    ]


# -----------------------------
# DISPLAY
# -----------------------------

def show_summary(logs):
    levels = count_log_levels(logs)
    error_rate = get_error_rate(logs)

    print("\n" + "=" * 45)
    print("              LOG ANALYZER")
    print("=" * 45)

    print(f"\nTotal Entries: {len(logs)}")

    print("\nLOG LEVELS")
    print("-" * 30)

    print(f"INFO:    {levels.get('INFO', 0)}")
    print(f"WARNING: {levels.get('WARNING', 0)}")
    print(f"ERROR:   {levels.get('ERROR', 0)}")

    print(f"\nERROR RATE: {error_rate:.2f}%")


def show_top_errors(logs):
    errors = count_errors(logs)

    print("\n" + "=" * 45)
    print("              TOP ERRORS")
    print("=" * 45)

    if not errors:
        print("\nNo errors found.")
        return

    for message, count in errors.most_common(5):
        print(f"{message:<35} {count}")


def show_logs_by_level(logs):
    level = input(
        "\nEnter log level (INFO/WARNING/ERROR): "
    ).strip()

    filtered_logs = get_logs_by_level(logs, level)

    if not filtered_logs:
        print("\nNo matching logs found.")
        return

    print("\n" + "=" * 60)
    print(f"{level.upper()} LOGS")
    print("=" * 60)

    for log in filtered_logs:
        print(
            f"{log['date']} "
            f"{log['time']} "
            f"{log['message']}"
        )


def show_all_logs(logs):
    print("\n" + "=" * 60)
    print("ALL LOGS")
    print("=" * 60)

    for log in logs:
        print(
            f"{log['date']} "
            f"{log['time']} "
            f"{log['level']:<8} "
            f"{log['message']}"
        )


# -----------------------------
# MAIN MENU
# -----------------------------

def main():

    create_sample_log()

    raw_logs = read_logs()
    logs = parse_all_logs(raw_logs)

    if not logs:
        print("No valid logs found.")
        return

    while True:

        print("\n" + "=" * 45)
        print("              LOG ANALYZER")
        print("=" * 45)

        print("""
1. Show Summary
2. Show Top Errors
3. Filter by Log Level
4. Show All Logs
5. Exit
""")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            show_summary(logs)

        elif choice == "2":
            show_top_errors(logs)

        elif choice == "3":
            show_logs_by_level(logs)

        elif choice == "4":
            show_all_logs(logs)

        elif choice == "5":
            print("\nGoodbye! 👋")
            break

        else:
            print("\nInvalid choice. Please select 1-5.")


# -----------------------------
# START PROGRAM
# -----------------------------

if __name__ == "__main__":
    main()