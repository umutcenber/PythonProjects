import os

print("=" * 40)
print("      BATCH FILE RENAMER")
print("=" * 40)

folder = input("Enter folder path: ").strip()

if not os.path.exists(folder):
    print("❌ Folder not found.")
    exit()

prefix = input("Enter new filename prefix: ").strip()

if prefix == "":
    prefix = "File"

files = []

for file in os.listdir(folder):
    path = os.path.join(folder, file)

    if os.path.isfile(path):
        files.append(file)

files.sort()

counter = 1

for file in files:

    old_path = os.path.join(folder, file)

    extension = os.path.splitext(file)[1]

    new_name = f"{prefix}_{counter}{extension}"

    new_path = os.path.join(folder, new_name)

    while os.path.exists(new_path):
        counter += 1
        new_name = f"{prefix}_{counter}{extension}"
        new_path = os.path.join(folder, new_name)

    os.rename(old_path, new_path)

    print(f"{file} ➜ {new_name}")

    counter += 1

print("\n✅ All files renamed successfully!")