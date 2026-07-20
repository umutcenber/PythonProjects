print("=== Text Encryptor ===")

text = input("Enter text: ")
shift = int(input("Enter shift number: "))

encrypted = ""

for char in text:
    if char.isalpha():
        if char.islower():
            encrypted += chr((ord(char) - ord('a') + shift) % 26 + ord('a'))
        else:
            encrypted += chr((ord(char) - ord('A') + shift) % 26 + ord('A'))
    else:
        encrypted += char

print("Encrypted text:", encrypted)