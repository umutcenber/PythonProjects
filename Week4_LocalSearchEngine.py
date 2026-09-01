import os
import re
from collections import Counter


DOCUMENT_FOLDER = "documents"


# -----------------------------
# DOCUMENT MANAGEMENT
# -----------------------------

def create_sample_documents():
    os.makedirs(DOCUMENT_FOLDER, exist_ok=True)

    sample_documents = {
        "python.txt": """
Python is a high-level programming language.
Python is widely used for web development, automation,
data science, artificial intelligence, and software development.
""",
        "data_science.txt": """
Data science combines statistics, programming, and machine learning.
Python is one of the most popular languages for data science.
Data analysis helps people understand large datasets.
""",
        "web_development.txt": """
Web development involves building websites and web applications.
Python can be used for backend web development with frameworks
such as Flask and FastAPI.
""",
        "machine_learning.txt": """
Machine learning allows computers to learn patterns from data.
Python provides many machine learning libraries.
Machine learning is widely used in artificial intelligence.
"""
    }

    for filename, content in sample_documents.items():
        filepath = os.path.join(DOCUMENT_FOLDER, filename)

        if not os.path.exists(filepath):
            with open(filepath, "w") as file:
                file.write(content.strip())


def load_documents():
    documents = {}

    for filename in os.listdir(DOCUMENT_FOLDER):

        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(DOCUMENT_FOLDER, filename)

        try:
            with open(filepath, "r") as file:
                documents[filename] = file.read()

        except OSError:
            print(f"Could not read {filename}.")

    return documents


# -----------------------------
# TEXT PROCESSING
# -----------------------------

def tokenize(text):
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

    stop_words = {
        "the", "is", "a", "an", "and", "or", "of",
        "to", "for", "in", "with", "from", "can",
        "be", "one", "used", "such", "as"
    }

    return [
        word
        for word in words
        if word not in stop_words
    ]


# -----------------------------
# SEARCH ENGINE
# -----------------------------

def build_index(documents):
    index = {}

    for filename, content in documents.items():

        words = tokenize(content)
        word_counts = Counter(words)

        for word, count in word_counts.items():

            if word not in index:
                index[word] = {}

            index[word][filename] = count

    return index


def search(index, documents, query):
    query_words = tokenize(query)

    if not query_words:
        return []

    scores = {}

    for word in query_words:

        if word not in index:
            continue

        for filename, frequency in index[word].items():
            scores[filename] = scores.get(filename, 0) + frequency

    results = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return results


# -----------------------------
# DISPLAY
# -----------------------------

def show_search_results(results, documents):

    if not results:
        print("\nNo results found.")
        return

    print("\n" + "=" * 60)
    print("SEARCH RESULTS")
    print("=" * 60)

    for rank, (filename, score) in enumerate(results, start=1):

        print(f"\n#{rank}  {filename}")
        print(f"Relevance Score: {score}")

        preview = documents[filename].strip().replace("\n", " ")

        if len(preview) > 120:
            preview = preview[:120] + "..."

        print(f"Preview: {preview}")

        print("-" * 60)


def show_index_statistics(index, documents):

    total_words = sum(
        len(tokenize(content))
        for content in documents.values()
    )

    unique_words = len(index)

    print("\n" + "=" * 45)
    print("SEARCH ENGINE STATISTICS")
    print("=" * 45)

    print(f"Documents:    {len(documents)}")
    print(f"Total words:  {total_words}")
    print(f"Unique words: {unique_words}")


def show_most_common_words(index):

    word_counter = Counter()

    for word, documents in index.items():
        for frequency in documents.values():
            word_counter[word] += frequency

    print("\n" + "=" * 45)
    print("MOST COMMON WORDS")
    print("=" * 45)

    for word, count in word_counter.most_common(10):
        print(f"{word:<20} {count}")


# -----------------------------
# MAIN MENU
# -----------------------------

def main():

    create_sample_documents()

    documents = load_documents()
    index = build_index(documents)

    while True:

        print("\n" + "=" * 45)
        print("           LOCAL SEARCH ENGINE")
        print("=" * 45)

        print("""
1. Search Documents
2. View Statistics
3. Most Common Words
4. List Documents
5. Exit
""")

        choice = input("Choose an option: ").strip()

        if choice == "1":

            query = input("\nSearch: ").strip()

            results = search(
                index,
                documents,
                query
            )

            show_search_results(results, documents)

        elif choice == "2":

            show_index_statistics(
                index,
                documents
            )

        elif choice == "3":

            show_most_common_words(index)

        elif choice == "4":

            print("\n" + "=" * 45)
            print("DOCUMENTS")
            print("=" * 45)

            for filename in documents:
                print(f"• {filename}")

        elif choice == "5":

            print("\nGoodbye! 👋")
            break

        else:

            print("\nInvalid choice. Please select 1-5.")


# -----------------------------
# START PROGRAM
# -----------------------------

if __name__ == "__main__":
    main()