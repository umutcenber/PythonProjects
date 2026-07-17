expenses = []

print("💰 Expense Tracker")

while True:
    print("\n1. Add Expense")
    print("2. View Expenses")
    print("3. Show Total")
    print("4. Exit")

    choice = input("Choose an option: ")

    if choice == "1":
        name = input("Expense name: ")
        amount = float(input("Amount: $"))

        expenses.append([name, amount])

        print("✅ Expense added!")

    elif choice == "2":

        if len(expenses) == 0:
            print("No expenses yet.")

        else:
            print("\nYour Expenses:")

            for expense in expenses:
                print(f"{expense[0]} - ${expense[1]:.2f}")

    elif choice == "3":

        total = 0

        for expense in expenses:
            total += expense[1]

        print(f"\n💸 Total Spent: ${total:.2f}")

    elif choice == "4":
        print("Goodbye!")
        break

    else:
        print("Invalid option.")