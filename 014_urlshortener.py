import requests


def shorten_url(url):
    api_url = f"https://tinyurl.com/api-create.php?url={url}"

    try:
        response = requests.get(api_url, timeout=10)

        if response.status_code == 200:
            return response.text
        else:
            return None

    except requests.exceptions.RequestException:
        return None


def main():
    print("=" * 35)
    print("        URL SHORTENER")
    print("=" * 35)

    while True:
        print("\n1. Shorten URL")
        print("2. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":
            long_url = input("\nEnter your URL: ").strip()

            if not long_url.startswith(("http://", "https://")):
                print("\n❌ Please enter a valid URL starting with http:// or https://")
                continue

            print("\nGenerating short URL...")

            short_url = shorten_url(long_url)

            if short_url:
                print("\n✅ Shortened URL:")
                print(short_url)
            else:
                print("\n❌ Failed to shorten the URL.")

        elif choice == "2":
            print("\nGoodbye!")
            break

        else:
            print("\n❌ Invalid choice.")


if __name__ == "__main__":
    main()