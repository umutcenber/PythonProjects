import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


# -----------------------------
# WEB SCRAPER
# -----------------------------

def fetch_page(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as error:
        print(f"\nCould not access website: {error}")
        return None


def extract_page_data(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else "No title"

    headings = []

    for heading in soup.find_all(["h1", "h2", "h3"]):
        text = heading.get_text(" ", strip=True)

        if text:
            headings.append(text)

    links = []

    for link in soup.find_all("a", href=True):
        href = urljoin(base_url, link["href"])
        text = link.get_text(" ", strip=True)

        links.append({
            "text": text if text else "No text",
            "url": href
        })

    return title, headings, links


# -----------------------------
# DISPLAY
# -----------------------------

def show_page_info(title, headings, links):

    print("\n" + "=" * 60)
    print("PAGE INFORMATION")
    print("=" * 60)

    print(f"\nTitle:\n{title}")

    print("\nHEADINGS")
    print("-" * 60)

    if headings:
        for number, heading in enumerate(headings, start=1):
            print(f"{number}. {heading}")
    else:
        print("No headings found.")

    print("\nLINKS")
    print("-" * 60)

    if links:
        for number, link in enumerate(links, start=1):
            print(f"{number}. {link['text']}")
            print(f"   {link['url']}")

    else:
        print("No links found.")


def save_results(title, headings, links):

    with open("scraped_data.txt", "w", encoding="utf-8") as file:

        file.write("WEB SCRAPER RESULTS\n")
        file.write("=" * 50 + "\n\n")

        file.write(f"TITLE:\n{title}\n\n")

        file.write("HEADINGS:\n")

        for heading in headings:
            file.write(f"- {heading}\n")

        file.write("\nLINKS:\n")

        for link in links:
            file.write(f"- {link['text']}\n")
            file.write(f"  {link['url']}\n")

    print("\n✓ Results saved to scraped_data.txt")


# -----------------------------
# MAIN
# -----------------------------

def main():

    print("=" * 45)
    print("           WEB SCRAPER")
    print("=" * 45)

    url = input("\nEnter website URL: ").strip()

    if not url.startswith(("http://", "https://")):
        print("\nPlease enter a valid URL starting with http:// or https://")
        return

    html = fetch_page(url)

    if html is None:
        return

    title, headings, links = extract_page_data(
        html,
        url
    )

    show_page_info(
        title,
        headings,
        links
    )

    save_choice = input(
        "\nSave results to file? (y/n): "
    ).strip().lower()

    if save_choice == "y":
        save_results(
            title,
            headings,
            links
        )

    print("\nDone! 👋")


# -----------------------------
# START PROGRAM
# -----------------------------

if __name__ == "__main__":
    main()