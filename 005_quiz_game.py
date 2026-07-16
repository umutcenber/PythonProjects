score = 0

print("🧠 Welcome to the Python Quiz!\n")

answer = input("1. What is the capital of France? ")

if answer.lower() == "paris":
    print("✅ Correct!\n")
    score += 1
else:
    print("❌ Wrong! The answer is Paris.\n")

answer = input("2. Which planet is known as the Red Planet? ")

if answer.lower() == "mars":
    print("✅ Correct!\n")
    score += 1
else:
    print("❌ Wrong! The answer is Mars.\n")

answer = input("3. How many days are there in a week? ")

if answer == "7":
    print("✅ Correct!\n")
    score += 1
else:
    print("❌ Wrong! The answer is 7.\n")

print("🎉 Quiz Finished!")
print(f"Your score: {score}/3")