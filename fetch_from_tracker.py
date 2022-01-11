import requests
import time
import json
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("tracker_url")
parser.add_argument("target")
parser.add_argument("--apikey", type=str)
args = parser.parse_args()

if not args.apikey:
    try:
        import secret
    except ImportError:
        print("apikey was not passed as argument, and secret.py was not found")
        exit()
    try:
        api_key = secret.apikey
    except:
        print("apikey variable seems to not exist in secret.py")
        exit()

else:
    api_key = args.apikey

base_url = args.tracker_url
if not base_url.endswith("/"):
    base_url += "/"


def req(page):
    request_url = f"ajax.php?action=browse&page={page}&year=2022"
    headers = {"authorization": api_key}
    r = requests.get(base_url + request_url, headers=headers)
    if r.status_code == 200:
        return r.json()


page = 1
total_pages = 0
total_releases = []

while page != total_pages:
    r = req(page)
    if not r:
        break
    if not total_pages:
        total_pages = r["response"]["pages"]
    releases = r["response"]["results"]
    for release in releases:
        if "category" in release and release["category"] in ["Audiobooks", "Comedy"]:
            continue
        total_releases.append(
            dict(
                title=release["groupName"],
                artist=release["artist"],
                release_type=release["releaseType"],
                genres=release["tags"],
            )
        )
    print(f"Iterating page {page}/{total_pages}, sleeping for 5 seconds")
    time.sleep(5)
    page += 1


with open(args.target, "w", encoding="utf-8") as f:
    print(f"Saving {len(total_releases)} albums to {args.target}")
    json.dump(total_releases, f, indent=2, sort_keys=True, ensure_ascii=False)
