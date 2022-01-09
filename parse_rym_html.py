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
                    if not "2022" in release_date:
                        continue
                    albums.append(
                        {
                            "title": title,
                            "artist": artist,
                            "genres": genres,
                            "release_date": release_date,
                            "urls": urls,
                        }
                    )
    for filename in filenames:
        if filename == "newmusic.html":
            # special case :)
            # i put it here after the first loop to ensure that these entries are at the end of the list
            # the reason is that the data here is slightly worse than above, and we prefer the better data
            #
            # i go to https://rateyourmusic.com/new-music/
            # and sort by date under all new releases,
            # then i load everything until i hit a 2021 release,
            # open the inspector and copy the entire DOM by selecting the html tag
            # and pressing ctrl+c. i then save that into newmusic.html
            # this branch should then handle each entry in that list
            fname = os.path.join(root, filename)
            with open(fname, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                releases = soup.find_all(class_="newreleases_text_stats_container")
                for release in releases:
                    release_date = release.find(class_="newreleases_item_releasedate").text.strip()
                    if not "2022" in release_date:
                        continue
                    title = release.find(class_="album").text.strip()
                    artist = release.find(class_="artist").text.strip()
                    genres = [x.text.strip() for x in release.find_all(class_="newreleases_item_genres")]
                    albums.append(
                        {
                            "title": title,
                            "artist": artist,
                            "genres": genres,
                            "release_date": release_date
                        }
                    )

with open(args.target, "w", encoding="utf-8") as f:
    unique_albums = []
    for album in albums:
        term = album["artist"]+album["title"]+album["release_date"]
        if not term in [x["artist"]+x["title"]+x["release_date"] for x in unique_albums]:
            unique_albums.append(album)
    print(f"Saving {len(unique_albums)} albums to {args.target}")
    json.dump(unique_albums, f, ensure_ascii=False, indent=2, sort_keys=True)
