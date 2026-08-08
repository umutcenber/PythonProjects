import hashlib
import os


def file_hash(file_path):
    hasher = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(8192):
            hasher.update(chunk)

    return hasher.hexdigest()


def find_duplicates(folder):
    hashes = {}
    duplicates = []

    for root, _, files in os.walk(folder):
        for filename in files:
            path = os.path.join(root, filename)

            try:
                file_hash_value = file_hash(path)

                if file_hash_value in hashes:
                    duplicates.append((path, hashes[file_hash_value]))
                else:
                    hashes[file_hash_value] = path

            except (PermissionError, OSError):
                print(f"Skipped: {path}")

    return duplicates


print("=" * 45)
print("        DUPLICATE FILE FINDER")
print("=" * 45)

folder = input("Enter folder path: ").strip()

if not os.path.isdir(folder):
    print("❌ Folder not found.")
    exit()

duplicates = find_duplicates(folder)

if not duplicates:
    print("\n✅ No duplicate files found.")
else:
    print(f"\n⚠️ Found {len(duplicates)} duplicate(s):\n")

    for duplicate, original in duplicates:
        print(f"Duplicate: {duplicate}")
        print(f"Original : {original}")
        print("-" * 45)