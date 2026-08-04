import os
import shutil

print("=" * 40)
print("      FOLDER BACKUP TOOL")
print("=" * 40)

source = input("Source folder: ").strip()
destination = input("Backup location: ").strip()

if not os.path.exists(source):
    print("❌ Source folder does not exist.")
    exit()

backup_name = os.path.basename(source.rstrip("\\/"))
backup_path = os.path.join(destination, backup_name)

try:
    shutil.copytree(source, backup_path, dirs_exist_ok=True)

    print("\n✅ Backup completed successfully!")
    print(f"Backup Location: {backup_path}")

except Exception as e:
    print(f"\n❌ Error: {e}")