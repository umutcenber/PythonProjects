import os
from datetime import datetime

NOTES_FOLDER = "notes"


def create_folder():
    os.makedirs(NOTES_FOLDER, exist_ok=True)


def create_note():
    title = input("Note title: ").strip()

    if not title:
        print("❌ Title cannot be empty.")
        return

    print("Write your note. Type 'END' on a new line to finish.")

    lines = []

    while True:
        line = input()

        if line == "END":
            break

        lines.append(line)

    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    filename = title.lower().replace(" ", "_") + ".md"
    path = os.path.join(NOTES_FOLDER, filename)

    content = f"# {title}\n\n"
    content += f"*Created: {date}*\n\n"
    content += "\n".join(lines)

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"\n✅ Note saved: {path}")


def list_notes():
    files = os.listdir(NOTES_FOLDER)
    notes = [file for file in files if file.endswith(".md")]

    if not notes:
        print("\nNo notes found.")
        return

    print("\nYour notes:")

    for number, note in enumerate(notes, start=1):
        print(f"{number}. {note}")


def read_note():
    list_notes()

    files = [
        file for file in os.listdir(NOTES_FOLDER)
        if file.endswith(".md")
    ]

    if not files:
        return

    try:
        choice = int(input("\nChoose note number: "))

        if choice < 1 or choice > len(files):
            print("❌ Invalid choice.")
            return

        path = os.path.join(NOTES_FOLDER, files[choice - 1])

        with open(path, "r", encoding="utf-8") as file:
            print("\n" + file.read())

    except ValueError:
        print("❌ Please enter a number.")


def main():
    create_folder()

    while True:
        print("\n" + "=" * 35)
        print("       MARKDOWN NOTE TAKER")
        print("=" * 35)
        print("1. Create note")
        print("2. List notes")
        print("3. Read note")
        print("4. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            create_note()
        elif choice == "2":
            list_notes()
        elif choice == "3":
            read_note()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("❌ Invalid option.")


if __name__ == "__main__":
    main()