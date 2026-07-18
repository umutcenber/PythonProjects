import random

choices = ["rock", "paper", "scissors"]

print("🎮 Rock Paper Scissors!")

while True:

    user = input("\nChoose rock, paper, or scissors (or type quit): ").lower()

    if user == "quit":
        print("👋 Goodbye!")
        break

    if user not in choices:
        print("❌ Invalid choice.")
        continue

    computer = random.choice(choices)

    print(f"You chose: {user}")
    print(f"Computer chose: {computer}")

    if user == computer:
        print("🤝 It's a tie!")

    elif (
        (user == "rock" and computer == "scissors") or
        (user == "paper" and computer == "rock") or
        (user == "scissors" and computer == "paper")
    ):
        print("🎉 You win!")

    else:
        print("💀 Computer wins!")