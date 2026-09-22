import os
import shutil
from collections import Counter
from datetime import datetime


def scan_folder(folder):
    files = []

    for root, _, filenames in os.walk(folder):
        for filename in filenames:
            path = os.path.join(root, filename)

            try:
                size = os.path.getsize(path)
                modified = os.path.getmtime(path)

                files.append({
                    "name": filename,
                    "path": path,
                    "size": size,
                    "extension": os.path.splitext(filename)[1].lower() or "[no extension]",
                    "modified": datetime.fromtimestamp(modified)
                })
            except OSError:
                pass

    return files


def format_size(size):
    if size < 1024:
        return f"{size} B"
    if size < 1024 ** 2:
        return f"{size / 1024:.2f} KB"
    if size < 1024 ** 3:
        return f"{size / (1024 ** 2):.2f} MB"
    return f"{size / (1024 ** 3):.2f} GB"


def show_statistics(files):
    if not files:
        print("No files found.")
        return

    total_size = sum(file["size"] for file in files)
    extensions = Counter(file["extension"] for file in files)

    print("\n===== FOLDER INTELLIGENCE =====")
    print(f"Total files: {len(files)}")
    print(f"Total size: {format_size(total_size)}")

    print("\nFile types:")
    for extension, count in extensions.most_common():
        print(f"{extension}: {count}")


def show_largest(files):
    if not files:
        print("No files found.")
        return

    print("\n===== 10 LARGEST FILES =====")

    for i, file in enumerate(
        sorted(files, key=lambda x: x["size"], reverse=True)[:10],
        1
    ):
        print(f"{i}. {file['name']}")
        print(f"   Size: {format_size(file['size'])}")
        print(f"   Path: {file['path']}")


def find_duplicates(files):
    hashes = {}
    duplicates = []

    import hashlib

    for file in files:
        try:
            hasher = hashlib.md5()

            with open(file["path"], "rb") as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)

            file_hash = hasher.hexdigest()

            if file_hash in hashes:
                duplicates.append(
                    (hashes[file_hash], file["path"])
                )
            else:
                hashes[file_hash] = file["path"]

        except (OSError, PermissionError):
            pass

    print("\n===== DUPLICATE FILES =====")

    if not duplicates:
        print("No duplicates found.")
        return

    for original, duplicate in duplicates:
        print(f"\nOriginal:  {original}")
        print(f"Duplicate: {duplicate}")


def find_old_files(files):
    print("\n===== FILES NOT MODIFIED FOR 180+ DAYS =====")

    now = datetime.now()
    found = False

    for file in files:
        days = (now - file["modified"]).days

        if days >= 180:
            found = True
            print(
                f"{file['name']} | "
                f"{days} days old | "
                f"{file['path']}"
            )

    if not found:
        print("No old files found.")


def organize_files(files, destination):
    os.makedirs(destination, exist_ok=True)

    moved = 0

    for file in files:
        extension = file["extension"].replace(".", "")

        if extension == "[no extension]":
            folder_name = "Other"
        else:
            folder_name = extension.upper()

        target_folder = os.path.join(destination, folder_name)
        os.makedirs(target_folder, exist_ok=True)

        target_path = os.path.join(
            target_folder,
            file["name"]
        )

        if os.path.abspath(file["path"]) == os.path.abspath(target_path):
            continue

        if os.path.exists(target_path):
            continue

        try:
            shutil.copy2(file["path"], target_path)
            moved += 1
        except OSError:
            pass

    print(f"\nOrganized {moved} files into:")
    print(destination)


def main():
    print("===== AUTOMATED FILE INTELLIGENCE =====")

    folder = input(
        "\nEnter folder path to analyze: "
    ).strip()

    if not os.path.isdir(folder):
        print("Invalid folder path.")
        return

    print("\nScanning folder...")
    files = scan_folder(folder)

    while True:
        print("\n===== MENU =====")
        print("1. Folder statistics")
        print("2. Show largest files")
        print("3. Find duplicate files")
        print("4. Find files older than 180 days")
        print("5. Organize files into categories")
        print("6. Rescan folder")
        print("7. Exit")

        choice = input("\nChoose: ").strip()

        if choice == "1":
            show_statistics(files)

        elif choice == "2":
            show_largest(files)

        elif choice == "3":
            find_duplicates(files)

        elif choice == "4":
            find_old_files(files)

        elif choice == "5":
            destination = input(
                "Enter destination folder: "
            ).strip()

            if destination:
                organize_files(files, destination)

        elif choice == "6":
            print("Rescanning...")
            files = scan_folder(folder)
            print(f"Found {len(files)} files.")

        elif choice == "7":
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()