import re

print("=" * 45)
print("     PASSWORD STRENGTH CHECKER")
print("=" * 45)

password = input("Enter a password: ")

score = 0
suggestions = []

# Length
if len(password) >= 12:
    score += 1
else:
    suggestions.append("Use at least 12 characters.")

# Uppercase
if re.search(r"[A-Z]", password):
    score += 1
else:
    suggestions.append("Add uppercase letters.")

# Lowercase
if re.search(r"[a-z]", password):
    score += 1
else:
    suggestions.append("Add lowercase letters.")

# Numbers
if re.search(r"\d", password):
    score += 1
else:
    suggestions.append("Add numbers.")

# Symbols
if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
    score += 1
else:
    suggestions.append("Add special characters.")

# Result
if score <= 2:
    strength = "Weak"
elif score == 3 or score == 4:
    strength = "Medium"
else:
    strength = "Strong"

print("\n" + "=" * 45)
print(f"Strength : {strength}")
print(f"Score    : {score}/5")

if suggestions:
    print("\nSuggestions:")
    for suggestion in suggestions:
        print(f"- {suggestion}")

print("=" * 45)