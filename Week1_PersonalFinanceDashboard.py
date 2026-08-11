import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt


DATABASE = "finance.db"


# -----------------------------
# DATABASE
# -----------------------------

def initialize_database():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def add_transaction(transaction_type, amount, category, description, date):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO transactions
        (type, amount, category, description, date)
        VALUES (?, ?, ?, ?, ?)
    """, (
        transaction_type,
        amount,
        category,
        description,
        date
    ))

    connection.commit()
    connection.close()


def get_transactions():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, type, amount, category, description, date
        FROM transactions
        ORDER BY date DESC, id DESC
    """)

    transactions = cursor.fetchall()

    connection.close()

    return transactions


def delete_transaction(transaction_id):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM transactions WHERE id = ?",
        (transaction_id,)
    )

    deleted = cursor.rowcount

    connection.commit()
    connection.close()

    return deleted > 0


# -----------------------------
# ANALYTICS
# -----------------------------

def get_financial_summary():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COALESCE(
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END),
                0
            ),
            COALESCE(
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END),
                0
            )
        FROM transactions
    """)

    income, expenses = cursor.fetchone()

    connection.close()

    balance = income - expenses

    return income, expenses, balance


def get_category_spending():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT category, SUM(amount)
        FROM transactions
        WHERE type = 'expense'
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """)

    data = cursor.fetchall()

    connection.close()

    return data


def get_monthly_summary():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            substr(date, 1, 7),
            SUM(
                CASE
                    WHEN type = 'income' THEN amount
                    ELSE 0
                END
            ),
            SUM(
                CASE
                    WHEN type = 'expense' THEN amount
                    ELSE 0
                END
            )
        FROM transactions
        GROUP BY substr(date, 1, 7)
        ORDER BY substr(date, 1, 7) DESC
    """)

    data = cursor.fetchall()

    connection.close()

    return data


# -----------------------------
# DISPLAY FUNCTIONS
# -----------------------------

def show_transactions():
    transactions = get_transactions()

    if not transactions:
        print("\nNo transactions found.")
        return

    print("\n" + "=" * 60)
    print("TRANSACTIONS")
    print("=" * 60)

    for transaction in transactions:
        transaction_id, transaction_type, amount, category, description, date = transaction

        print(f"""
ID:          {transaction_id}
Type:        {transaction_type.title()}
Amount:      ${amount:.2f}
Category:    {category}
Description: {description}
Date:        {date}
{"-" * 60}
""")


def show_balance():
    income, expenses, balance = get_financial_summary()

    print("\n" + "=" * 40)
    print("FINANCIAL SUMMARY")
    print("=" * 40)

    print(f"Total Income:   ${income:.2f}")
    print(f"Total Expenses: ${expenses:.2f}")
    print(f"Balance:        ${balance:.2f}")


def show_category_spending():
    data = get_category_spending()

    if not data:
        print("\nNo expense data available.")
        return

    print("\n" + "=" * 40)
    print("SPENDING BY CATEGORY")
    print("=" * 40)

    for category, amount in data:
        print(f"{category:<20} ${amount:.2f}")


def show_monthly_summary():
    data = get_monthly_summary()

    if not data:
        print("\nNo monthly data available.")
        return

    print("\n" + "=" * 40)
    print("MONTHLY SUMMARY")
    print("=" * 40)

    for month, income, expenses in data:
        balance = income - expenses

        print(f"""
{month}
Income:   ${income:.2f}
Expenses: ${expenses:.2f}
Balance:  ${balance:.2f}
""")


def show_spending_chart():
    data = get_category_spending()

    if not data:
        print("\nNo expense data available.")
        return

    categories = [item[0] for item in data]
    amounts = [item[1] for item in data]

    plt.figure(figsize=(9, 5))

    plt.bar(categories, amounts)

    plt.title("Spending by Category")
    plt.xlabel("Category")
    plt.ylabel("Amount")

    plt.xticks(rotation=30)
    plt.tight_layout()

    plt.show()


# -----------------------------
# INPUT FUNCTIONS
# -----------------------------

def add_transaction_menu():

    print("\n" + "=" * 40)
    print("ADD TRANSACTION")
    print("=" * 40)

    while True:
        transaction_type = input(
            "Type (income/expense): "
        ).strip().lower()

        if transaction_type in ["income", "expense"]:
            break

        print("Please enter 'income' or 'expense'.")

    while True:
        try:
            amount = float(input("Amount: "))

            if amount <= 0:
                print("Amount must be greater than 0.")
                continue

            break

        except ValueError:
            print("Please enter a valid number.")

    category = input("Category: ").strip()
    description = input("Description: ").strip()

    date = input(
        "Date (YYYY-MM-DD, press Enter for today): "
    ).strip()

    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    add_transaction(
        transaction_type,
        amount,
        category,
        description,
        date
    )

    print("\n✓ Transaction added successfully.")


def delete_transaction_menu():

    show_transactions()

    try:
        transaction_id = int(
            input("Enter transaction ID to delete: ")
        )

    except ValueError:
        print("Invalid ID.")
        return

    if delete_transaction(transaction_id):
        print("\n✓ Transaction deleted successfully.")

    else:
        print("\nTransaction not found.")


# -----------------------------
# MAIN MENU
# -----------------------------

def main():

    initialize_database()

    while True:

        print("\n")
        print("=" * 45)
        print("       PERSONAL FINANCE DASHBOARD")
        print("=" * 45)

        print("""
1. Add Transaction
2. View Transactions
3. Delete Transaction
4. View Balance
5. Spending by Category
6. Monthly Summary
7. Spending Chart
8. Exit
""")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_transaction_menu()

        elif choice == "2":
            show_transactions()

        elif choice == "3":
            delete_transaction_menu()

        elif choice == "4":
            show_balance()

        elif choice == "5":
            show_category_spending()

        elif choice == "6":
            show_monthly_summary()

        elif choice == "7":
            show_spending_chart()

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