import os
import hashlib

print("=" * 40)
print("    DUPLICATE FILE FINDER")
print("=" * 40)

folder = input("Enter folder path: ").strip()

if not os.path.exists(folder):
    print("❌ Folder not found.")
    exit()


def get_file_hash(file_path):
    hasher = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(4096):
            hasher.update(chunk)

    return hasher.hexdigest()


duplicates = {}

for root, dirs, files in os.walk(folder):

    for file in files:

        path = os.path.join(root, file)

        try:
            file_hash = get_file_hash(path)

            duplicates.setdefault(file_hash, []).append(path)

        except:
            pass

found = False

print("\nDuplicate Files:\n")

for file_hash, paths in duplicates.items():

    if len(paths) > 1:

        found = True

        print("-" * 40)

        for path in paths:
            print(path)

if not found:
    print("✅ No duplicate files found.")