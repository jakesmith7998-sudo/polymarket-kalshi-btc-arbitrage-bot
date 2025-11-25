import requests
import json

def fetch_markets():
    url = "https://clob.polymarket.com/markets"
    try:
        response = requests.get(url, params={"limit": 5})
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

def fetch_event(slug):
    url = "https://gamma-api.polymarket.com/events"
    try:
        response = requests.get(url, params={"slug": slug})
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error fetching event: {e}")

if __name__ == "__main__":
    print("Fetching markets...")
    fetch_markets()
    print("\nFetching event...")
    fetch_event("bitcoin-up-or-down-november-25-6pm-et")
