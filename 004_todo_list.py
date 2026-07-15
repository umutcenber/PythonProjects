tasks = []

print("📋 Welcome to your To-Do List!")

while True:
    print("\n1. Add Task")
    print("2. View Tasks")
    print("3. Delete Task")
    print("4. Exit")

    choice = input("Choose an option (1-4): ")

    if choice == "1":
        task = input("Enter a new task: ")
        tasks.append(task)
        print("✅ Task added!")

    elif choice == "2":
        if len(tasks) == 0:
            print("📭 No tasks yet.")
        else:
            print("\nYour Tasks:")
            for i, task in enumerate(tasks, start=1):
                print(f"{i}. {task}")

    elif choice == "3":
        if len(tasks) == 0:
            print("📭 No tasks to delete.")
        else:
            for i, task in enumerate(tasks, start=1):
                print(f"{i}. {task}")

            delete = int(input("Enter task number to delete: "))

            if 1 <= delete <= len(tasks):
                removed = tasks.pop(delete - 1)
                print(f"🗑️ '{removed}' deleted!")
            else:
                print("❌ Invalid number.")

    elif choice == "4":
        print("👋 Goodbye!")
        break

    else:
        print("❌ Invalid choice.")