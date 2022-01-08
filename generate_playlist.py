import json
try:
    import secret
except ImportError:
    pass
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from argparse import ArgumentParser
import os

parser = ArgumentParser()
parser.add_argument("data_dir")
parser.add_argument("playlist_url")
args = parser.parse_args()

if not os.path.isdir(args.data_dir):
    print("That's not a directory")
    exit()

scope = "playlist-modify-private playlist-modify-public"
sp = Spotify(auth_manager=SpotifyOAuth(scope=scope))

playlist_id = args.playlist_url.split("?")[0].split("/")[-1]
added_titles = []


def search_and_add_song(term, list_id):
    search = sp.search(term, type="album")
    for item in search["albums"]["items"]:
        # this might be a bit too fuzzy
        # todo: add fuzzy matching on album name. i think that should be sufficient
        if item["release_date"].startswith("2022"): 
            add_album_to_playlist(item["id"], list_id)
            return True
    return False


def add_album_to_playlist(album_id, list_id):
    album = sp.album(album_id)
    tracks = [f"spotify:track:{x['id']}" for x in album["tracks"]["items"]]
    sp.playlist_add_items(playlist_id=list_id, items=tracks)


for root, _, filenames in os.walk(args.data_dir):
    for filename in filenames:
        if filename.endswith(".json"):
            fname = os.path.join(root, filename)
            with open(fname, "r", encoding="utf-8") as f:
                albums = json.load(f)
            for album in albums:
                if "release_type" in album and album["release_type"] not in [
                    "EP",
                    "Album",
                ]:
                    continue
                artist = album["artist"]
                title = album["title"]
                term = f"{artist} - {title}"
                if term in added_titles:
                    continue
                if search_and_add_song(term, playlist_id):
                    added_titles.append(term)
                    print(f"Added {term} ({', '.join(album['genres'])})")
                elif "urls" in album and "spotify" in album["urls"]:
                    album_id = album["urls"]["spotify"].split("?")[0].split("/")[-1]
                    add_album_to_playlist(album_id, playlist_id)
                    added_titles.append(term)
                    print(f"Added {term} ({', '.join(album['genres'])})")
                
print(f"Added {len(added_titles)} albums to Spotify playlist")
