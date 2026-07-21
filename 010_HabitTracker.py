import json
import os

FILE_NAME = "habits.json"


def load_habits():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            return json.load(file)
    return {}


def save_habits(habits):
    with open(FILE_NAME, "w") as file:
        json.dump(habits, file, indent=4)


def add_habit(habits):
    habit = input("Enter a habit: ")

    if habit in habits:
        print("Habit already exists.")
    else:
        habits[habit] = 0
        print("Habit added successfully.")


def complete_habit(habits):
    habit = input("Which habit did you complete? ")

    if habit in habits:
        habits[habit] += 1
        print("Progress saved!")
    else:
        print("Habit not found.")


def view_habits(habits):
    if not habits:
        print("No habits found.")
        return

    print("\nYour Habits:")
    for habit, streak in habits.items():
        print(f"- {habit}: {streak} day(s)")


def delete_habit(habits):
    habit = input("Enter habit to delete: ")

    if habit in habits:
        del habits[habit]
        print("Habit deleted.")
    else:
        print("Habit not found.")


def main():
    habits = load_habits()

    while True:
        print("\n=== Habit Tracker ===")
        print("1. Add Habit")
        print("2. Complete Habit")
        print("3. View Habits")
        print("4. Delete Habit")
        print("5. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_habit(habits)

        elif choice == "2":
            complete_habit(habits)

        elif choice == "3":
            view_habits(habits)

        elif choice == "4":
            delete_habit(habits)

        elif choice == "5":
            save_habits(habits)
            print("Goodbye!")
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()