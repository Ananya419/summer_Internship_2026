import requests

def fetch_live_nav(amfi_code="125497"):
    url = f"https://api.mfapi.in/mf/{amfi_code}"
    print(f"Fetching data from: {url}")
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        meta = data.get('meta', {})
        print("\n--- Fund Details ---")
        print(f"Fund House: {meta.get('fund_house')}")
        print(f"Scheme Name: {meta.get('scheme_name')}")
        print(f"Scheme Category: {meta.get('scheme_category')}")
        print("\nSuccessfully fetched live API data!")
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")

if __name__ == "__main__":
    fetch_live_nav()
