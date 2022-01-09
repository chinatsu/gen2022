import json
try:
    import secret
except ImportError:
    pass
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from argparse import ArgumentParser
import os
from thefuzz import fuzz, process

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


def search_and_add_song(artist, title, list_id):
    search = sp.search(f"{artist} - {title}".lower(), type="album")
    for item in search["albums"]["items"]:
        artist_score = process.extractOne(artist.lower(), [a["name"].lower() for a in item["artists"]])[-1]
        title_score = fuzz.partial_ratio(title.lower(), item["name"].lower())
        score = artist_score + title_score
        if score > 180 and item["release_date"].startswith("2022"):
            return add_album_to_playlist(item["id"], list_id)
        
    return False


def add_album_to_playlist(album_id, list_id):
    album = sp.album(album_id)
    artist = album["artists"][0]["name"]
    title = album["name"]
    term = f"{artist} - {title}"
    if term in added_titles:
        print(f"Album {term} should already be added")
        return False
    tracks = [f"spotify:track:{x['id']}" for x in album["tracks"]["items"]]
    sp.playlist_add_items(playlist_id=list_id, items=tracks)
    added_titles.append(term)
    print(f"Added {term} ({', '.join(album['genres'])})")
    return True


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
                if search_and_add_song(artist, title, playlist_id):
                    pass
                elif "urls" in album and "spotify" in album["urls"]:
                    # backup for the RYM dataset if no album was found by searching
                    album_id = album["urls"]["spotify"].split("?")[0].split("/")[-1]
                    add_album_to_playlist(album_id, playlist_id)
                
print(f"Added {len(added_titles)} albums to Spotify playlist")
