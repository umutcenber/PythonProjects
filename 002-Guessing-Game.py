import random

secret = random.randint(1, 100)

attempts = 0
max_attempts = 10

print("🎮 Welcome to the Guessing Game!")
print("You have 10 attempts.")

while attempts < max_attempts:

    guess = int(input("Guess a number (1-100): "))
    attempts += 1

    if guess < secret:
        print("📈 Too low!")

    elif guess > secret:
        print("📉 Too high!")

    else:
        print("🎉 Congratulations!")
        print(f"You found the number in {attempts} attempts!")
        break

    print(f"You have {max_attempts - attempts} attempts left.")

if attempts == max_attempts and guess != secret:
    print("💀 Game Over!")
    print(f"The correct number was {secret}.")
