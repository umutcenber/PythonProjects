import os
import shutil

FILE_TYPES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".ppt", ".pptx", ".xls", ".xlsx"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov"],
    "Music": [".mp3", ".wav", ".flac"],
    "Python": [".py"],
    "Archives": [".zip", ".rar", ".7z"]
}


def organize_folder(folder_path):
    if not os.path.exists(folder_path):
        print("❌ Folder not found.")
        return

    moved_files = 0

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)

        if os.path.isdir(file_path):
            continue

        _, extension = os.path.splitext(file_name)
        extension = extension.lower()

        destination_folder = "Others"

        for folder, extensions in FILE_TYPES.items():
            if extension in extensions:
                destination_folder = folder
                break

        destination_path = os.path.join(folder_path, destination_folder)

        os.makedirs(destination_path, exist_ok=True)

        shutil.move(file_path, os.path.join(destination_path, file_name))

        moved_files += 1
        print(f"Moved: {file_name} ➜ {destination_folder}")

    print(f"\n✅ Finished! {moved_files} file(s) organized.")


def main():
    print("=" * 40)
    print("      FILE ORGANIZER")
    print("=" * 40)

    folder = input("Enter folder path: ").strip()

    organize_folder(folder)


if __name__ == "__main__":
    main()