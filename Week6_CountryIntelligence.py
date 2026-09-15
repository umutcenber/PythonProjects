import requests

API_URL = "https://restcountries.com/v3.1/all"

def get_countries():
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def show_country(country):
    name = country.get("name", {}).get("common", "Unknown")
    official = country.get("name", {}).get("official", "Unknown")
    capital = ", ".join(country.get("capital", ["Unknown"]))
    region = country.get("region", "Unknown")
    subregion = country.get("subregion", "Unknown")
    population = country.get("population", 0)
    area = country.get("area", 0)
    currencies = country.get("currencies", {})
    languages = country.get("languages", {})

    currency_names = ", ".join(
        data.get("name", code) for code, data in currencies.items()
    ) or "Unknown"

    language_names = ", ".join(languages.values()) or "Unknown"

    print("\n" + "=" * 50)
    print(f"Country: {name}")
    print(f"Official Name: {official}")
    print(f"Capital: {capital}")
    print(f"Region: {region}")
    print(f"Subregion: {subregion}")
    print(f"Population: {population:,}")
    print(f"Area: {area:,.0f} km²")
    print(f"Currency: {currency_names}")
    print(f"Languages: {language_names}")
    print("=" * 50)


def search_country(countries):
    query = input("Enter country name: ").strip().lower()

    matches = [
        country for country in countries
        if query in country.get("name", {}).get("common", "").lower()
    ]

    if not matches:
        print("No country found.")
        return

    for country in matches:
        show_country(country)


def largest_population(countries):
    countries = sorted(
        countries,
        key=lambda c: c.get("population", 0),
        reverse=True
    )

    print("\nTop 10 Most Populous Countries:")
    for i, country in enumerate(countries[:10], 1):
        name = country.get("name", {}).get("common", "Unknown")
        population = country.get("population", 0)
        print(f"{i}. {name}: {population:,}")


def largest_area(countries):
    countries = sorted(
        countries,
        key=lambda c: c.get("area", 0),
        reverse=True
    )

    print("\nTop 10 Largest Countries by Area:")
    for i, country in enumerate(countries[:10], 1):
        name = country.get("name", {}).get("common", "Unknown")
        area = country.get("area", 0)
        print(f"{i}. {name}: {area:,.0f} km²")


def region_statistics(countries):
    regions = {}

    for country in countries:
        region = country.get("region", "Unknown")
        regions[region] = regions.get(region, 0) + 1

    print("\nCountries by Region:")
    for region, count in sorted(regions.items()):
        print(f"{region}: {count}")


def main():
    print("Loading country data...")

    try:
        countries = get_countries()
    except requests.RequestException as error:
        print(f"Could not fetch data: {error}")
        return

    print(f"Loaded {len(countries)} countries.")

    while True:
        print("\n===== COUNTRY INTELLIGENCE DASHBOARD =====")
        print("1. Search country")
        print("2. Top 10 by population")
        print("3. Top 10 by area")
        print("4. Countries by region")
        print("5. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            search_country(countries)

        elif choice == "2":
            largest_population(countries)

        elif choice == "3":
            largest_area(countries)

        elif choice == "4":
            region_statistics(countries)

        elif choice == "5":
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()