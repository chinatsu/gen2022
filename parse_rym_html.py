import os
from argparse import ArgumentParser
from bs4 import BeautifulSoup
import json
import ast

parser = ArgumentParser()
parser.add_argument("dir")
parser.add_argument("target")
args = parser.parse_args()

if not os.path.isdir(args.dir):
    print("That's not a directory")
    exit()

albums = []

for root, _, filenames in os.walk(args.dir):
    for filename in filenames:
        if filename.endswith(".htm"):
            fname = os.path.join(root, filename)
            with open(fname, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                releases = soup.find_all(class_="chart_item_release")
                for release in releases:
                    title = release.find(class_="release").text.strip()
                    artist = release.find(class_="topcharts_item_artist").text.strip()
                    genres = [x.text.strip() for x in release.find_all(class_="genre")]
                    release_date = release.find(
                        class_="topcharts_item_releasedate"
                    ).text.strip()
                    urls = ast.literal_eval(
                        release.find(class_="linkfire_container")["data-track-urls"]
                    )
                    albums.append(
                        {
                            "title": title,
                            "artist": artist,
                            "genres": genres,
                            "release_date": release_date,
                            "urls": urls,
                        }
                    )

with open(args.target, "w", encoding="utf-8") as f:
    albums = [ast.literal_eval(el1) for el1 in set([str(el2) for el2 in albums])]
    json.dump(albums, f, ensure_ascii=False, indent=2, sort_keys=True)
