contacts = []

print("📖 Contact Book")

while True:

    print("\n1. Add Contact")
    print("2. View Contacts")
    print("3. Search Contact")
    print("4. Exit")

    choice = input("Choose an option: ")

    if choice == "1":

        name = input("Name: ")
        phone = input("Phone Number: ")

        contacts.append([name, phone])

        print("✅ Contact added!")

    elif choice == "2":

        if len(contacts) == 0:
            print("No contacts found.")

        else:
            print("\n📋 Contacts:")

            for contact in contacts:
                print(f"{contact[0]} - {contact[1]}")

    elif choice == "3":

        search = input("Enter a name: ").lower()

        found = False

        for contact in contacts:

            if contact[0].lower() == search:
                print(f"📞 {contact[0]} - {contact[1]}")
                found = True

        if not found:
            print("❌ Contact not found.")

    elif choice == "4":

        print("👋 Goodbye!")
        break

    else:
        print("❌ Invalid option.")