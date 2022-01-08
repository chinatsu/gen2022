import requests
import time
import json
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("tracker_url")
parser.add_argument("target")
parser.add_argument("--apikey", type=str)
args = parser.parse_args()


if not parser.apikey:
    try:
        import secret
    except ImportError:
        print("apikey was not passed as argument, and secret.py was not found")
    api_key = secret.apikey
else:
    api_key = parser.apikey

base_url = args.tracker_url
if not base_url.endswith("/"):
    base_url += "/"


def req(page):
    request_url = f"ajax.php?action=browse&page={page}&year=2022"
    headers = {
        "authorization": api_key
    }
    r = requests.get(base_url + request_url, headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        print(r)

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
        if "category" in release and release["category"] in ["Audiobooks"]:
            continue
        total_releases.append(dict(
            title=release["groupName"],
            artist=release["artist"],
            release_type=release["releaseType"],
            genres=release["tags"]
        ))
    time.sleep(5)
    page += 1

with open(args.target, "w", encoding="utf-8") as f:
    json.dump(total_releases, f, indent=2, sort_keys=True, ensure_ascii=False)
