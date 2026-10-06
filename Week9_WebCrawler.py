import sqlite3
import requests
import threading
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime


DATABASE = "crawler.db"

MAX_WORKERS = 5
MAX_PAGES = 50
REQUEST_TIMEOUT = 8


# ============================================================
# DATABASE
# ============================================================

def init_database():
    connection = sqlite3.connect(DATABASE)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            status_code INTEGER,
            word_count INTEGER,
            links_found INTEGER,
            crawled_at TEXT
        )
    """)

    connection.commit()
    connection.close()


def save_page(data):
    connection = sqlite3.connect(DATABASE)

    connection.execute("""
        INSERT OR REPLACE INTO pages
        (url, title, status_code, word_count, links_found, crawled_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["url"],
        data["title"],
        data["status_code"],
        data["word_count"],
        data["links_found"],
        datetime.now().isoformat()
    ))

    connection.commit()
    connection.close()


# ============================================================
# URL UTILITIES
# ============================================================

def normalize_url(url):
    url, _ = urldefrag(url)

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return None

    if not parsed.netloc:
        return None

    return url.rstrip("/")


def same_domain(url, base_domain):
    return urlparse(url).netloc == base_domain


# ============================================================
# CRAWLER
# ============================================================

class WebCrawler:

    def __init__(self, start_url, max_pages=50):
        self.start_url = normalize_url(start_url)
        self.max_pages = max_pages

        self.domain = urlparse(self.start_url).netloc

        self.queue = deque([self.start_url])

        self.visited = set()
        self.lock = threading.Lock()

        self.pages_crawled = 0
        self.errors = 0

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "EducationalWebCrawler/1.0"
        })

    def get_next_url(self):

        with self.lock:

            while self.queue:

                url = self.queue.popleft()

                if url not in self.visited:
                    self.visited.add(url)
                    return url

        return None

    def add_url(self, url):

        url = normalize_url(url)

        if not url:
            return

        if not same_domain(url, self.domain):
            return

        with self.lock:

            if url not in self.visited:
                self.queue.append(url)

    def crawl_page(self, url):

        try:

            response = self.session.get(
                url,
                timeout=REQUEST_TIMEOUT
            )

            content_type = response.headers.get(
                "Content-Type",
                ""
            )

            if "text/html" not in content_type:
                return

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            title = (
                soup.title.string.strip()
                if soup.title and soup.title.string
                else "No title"
            )

            text = soup.get_text(
                " ",
                strip=True
            )

            word_count = len(text.split())

            links = set()

            for tag in soup.find_all("a", href=True):

                absolute_url = urljoin(
                    url,
                    tag["href"]
                )

                absolute_url = normalize_url(
                    absolute_url
                )

                if (
                    absolute_url
                    and same_domain(
                        absolute_url,
                        self.domain
                    )
                ):
                    links.add(absolute_url)

                    self.add_url(
                        absolute_url
                    )

            save_page({
                "url": url,
                "title": title,
                "status_code": response.status_code,
                "word_count": word_count,
                "links_found": len(links)
            })

            with self.lock:
                self.pages_crawled += 1

                current = self.pages_crawled

            print(
                f"[{current}/{self.max_pages}] "
                f"{response.status_code} | "
                f"{title[:50]} | "
                f"{url}"
            )

        except requests.RequestException as error:

            with self.lock:
                self.errors += 1

            print(
                f"[ERROR] {url} -> {error}"
            )

        except Exception as error:

            with self.lock:
                self.errors += 1

            print(
                f"[ERROR] {url} -> {error}"
            )

    def worker(self):

        while True:

            with self.lock:
                if self.pages_crawled >= self.max_pages:
                    return

            url = self.get_next_url()

            if url is None:
                return

            self.crawl_page(url)

    def start(self):

        print("\nStarting crawler...")
        print(f"Domain: {self.domain}")
        print(f"Maximum pages: {self.max_pages}")
        print("-" * 70)

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as executor:

            futures = [
                executor.submit(self.worker)
                for _ in range(MAX_WORKERS)
            ]

            for future in futures:
                future.result()

        print("\n" + "=" * 70)
        print("CRAWL COMPLETE")
        print("=" * 70)

        print(f"Pages crawled : {self.pages_crawled}")
        print(f"Errors        : {self.errors}")
        print(f"URLs discovered: {len(self.visited)}")


# ============================================================
# DATABASE STATISTICS
# ============================================================

def show_statistics():

    connection = sqlite3.connect(DATABASE)

    total = connection.execute(
        "SELECT COUNT(*) FROM pages"
    ).fetchone()[0]

    average_words = connection.execute(
        "SELECT AVG(word_count) FROM pages"
    ).fetchone()[0]

    average_links = connection.execute(
        "SELECT AVG(links_found) FROM pages"
    ).fetchone()[0]

    most_linked = connection.execute("""
        SELECT url, links_found
        FROM pages
        ORDER BY links_found DESC
        LIMIT 10
    """).fetchall()

    connection.close()

    print("\n" + "=" * 70)
    print("CRAWLER STATISTICS")
    print("=" * 70)

    print(f"Total pages: {total}")

    if average_words:
        print(
            f"Average words/page: "
            f"{average_words:.2f}"
        )

    if average_links:
        print(
            f"Average links/page: "
            f"{average_links:.2f}"
        )

    print("\nPages with most discovered links:")

    for index, (url, links) in enumerate(
        most_linked,
        1
    ):
        print(
            f"{index}. {links} links | {url}"
        )


# ============================================================
# SEARCH CRAWLED PAGES
# ============================================================

def search_pages():

    query = input(
        "\nSearch title or URL: "
    ).strip().lower()

    connection = sqlite3.connect(DATABASE)

    results = connection.execute("""
        SELECT
            title,
            url,
            word_count,
            links_found
        FROM pages
        WHERE LOWER(title) LIKE ?
           OR LOWER(url) LIKE ?
        ORDER BY word_count DESC
    """, (
        f"%{query}%",
        f"%{query}%"
    )).fetchall()

    connection.close()

    if not results:
        print("No matching pages found.")
        return

    print("\nSearch results:")

    for title, url, words, links in results:

        print("\n" + "-" * 60)
        print(f"Title: {title}")
        print(f"URL: {url}")
        print(f"Words: {words}")
        print(f"Links: {links}")


# ============================================================
# SHOW CRAWLED PAGES
# ============================================================

def show_pages():

    connection = sqlite3.connect(DATABASE)

    rows = connection.execute("""
        SELECT
            title,
            url,
            status_code,
            word_count
        FROM pages
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    if not rows:
        print("No pages crawled yet.")
        return

    print("\n" + "=" * 70)
    print("CRAWLED PAGES")
    print("=" * 70)

    for title, url, status, words in rows:

        print(
            f"{status} | "
            f"{words} words | "
            f"{title[:40]}"
        )

        print(f"  {url}")


# ============================================================
# MAIN
# ============================================================

def main():

    init_database()

    while True:

        print("\n" + "=" * 70)
        print("                 MINI WEB CRAWLER")
        print("=" * 70)

        print("1. Start new crawl")
        print("2. Show crawled pages")
        print("3. Search crawled pages")
        print("4. Show statistics")
        print("5. Exit")

        choice = input("\nChoose: ").strip()

        if choice == "1":

            url = input(
                "\nEnter starting URL: "
            ).strip()

            if not url.startswith(
                ("http://", "https://")
            ):
                print(
                    "URL must start with "
                    "http:// or https://"
                )
                continue

            try:
                limit = int(
                    input(
                        "Maximum pages to crawl "
                        f"(default {MAX_PAGES}): "
                    ) or MAX_PAGES
                )

                if limit <= 0:
                    raise ValueError

            except ValueError:
                print("Invalid page limit.")
                continue

            crawler = WebCrawler(
                url,
                min(limit, MAX_PAGES)
            )

            crawler.start()

        elif choice == "2":
            show_pages()

        elif choice == "3":
            search_pages()

        elif choice == "4":
            show_statistics()

        elif choice == "5":
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()