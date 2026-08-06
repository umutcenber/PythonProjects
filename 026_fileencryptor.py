from cryptography.fernet import Fernet
import os


def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)


def load_key():
    return open("secret.key", "rb").read()


if not os.path.exists("secret.key"):
    generate_key()

key = load_key()
cipher = Fernet(key)

print("=" * 40)
print("      FILE ENCRYPTOR")
print("=" * 40)

file_path = input("Enter file path: ").strip()

if not os.path.exists(file_path):
    print("❌ File not found.")
    exit()

choice = input("\nEncrypt or Decrypt? (E/D): ").strip().upper()

try:

    with open(file_path, "rb") as file:
        data = file.read()

    if choice == "E":

        encrypted = cipher.encrypt(data)

        output = file_path + ".enc"

        with open(output, "wb") as file:
            file.write(encrypted)

        print(f"\n✅ Encrypted file saved as:\n{output}")

    elif choice == "D":

        decrypted = cipher.decrypt(data)

        if file_path.endswith(".enc"):
            output = file_path[:-4]
        else:
            output = "decrypted_" + os.path.basename(file_path)

        with open(output, "wb") as file:
            file.write(decrypted)

        print(f"\n✅ Decrypted file saved as:\n{output}")

    else:
        print("❌ Invalid option.")

except Exception as e:
    print(f"\n❌ Error: {e}")