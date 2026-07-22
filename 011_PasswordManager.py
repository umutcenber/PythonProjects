import json
import os

FILE_NAME = "passwords.json"


def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            return json.load(file)
    return {}


def save_data(data):
    with open(FILE_NAME, "w") as file:
        json.dump(data, file, indent=4)


def add_password(data):
    website = input("Website: ")
    username = input("Username: ")
    password = input("Password: ")

    data[website] = {
        "username": username,
        "password": password
    }

    print("Password saved.")


def view_passwords(data):
    if not data:
        print("No passwords saved.")
        return

    print("\nSaved Passwords:\n")

    for website, info in data.items():
        print(f"Website : {website}")
        print(f"Username: {info['username']}")
        print(f"Password: {info['password']}")
        print("-" * 25)


def delete_password(data):
    website = input("Website to delete: ")

    if website in data:
        del data[website]
        print("Deleted successfully.")
    else:
        print("Website not found.")


def main():
    data = load_data()

    while True:
        print("\n=== Password Manager ===")
        print("1. Add Password")
        print("2. View Passwords")
        print("3. Delete Password")
        print("4. Exit")

        choice = input("Choose: ")

        if choice == "1":
            add_password(data)

        elif choice == "2":
            view_passwords(data)

        elif choice == "3":
            delete_password(data)

        elif choice == "4":
            save_data(data)
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()