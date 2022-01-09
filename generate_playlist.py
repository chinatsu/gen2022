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
parser.add_argument("--genre-file")
args = parser.parse_args()

if not os.path.isdir(args.data_dir):
    print("That's not a directory")
    exit()

scope = "playlist-modify-private playlist-modify-public"
sp = Spotify(auth_manager=SpotifyOAuth(scope=scope))

playlist_id = args.playlist_url.split("?")[0].split("/")[-1]
added_titles = []
allowed_genres = []

if args.genre_file:
    with open(args.genre_file) as f:
        allowed_genres = json.load(f)


def search_and_add_song(artist, title, list_id):
    search = sp.search(f"{artist} - {title}".lower(), type="album")
    for item in search["albums"]["items"]:
        artist_score = process.extractOne(artist.lower(), [a["name"].lower() for a in item["artists"]])[-1]
        title_score = fuzz.partial_ratio(title.lower(), item["name"].lower())
        score = artist_score + title_score
        if score > 180:
            return add_album_to_playlist(item["id"], list_id)
        
    return False


def add_album_to_playlist(album_id, list_id):
    album = sp.album(album_id)
    artist = album["artists"][0]["name"]
    title = album["name"]
    term = f"{artist} - {title}"
    if term in added_titles:
        print(f"!!! Album {term} should already be added")
        return False
    if not album["release_date"].startswith("2022"):
        print(f"!!! {term} appears to have been released in {album['release_date']}, skipping")
        return False

    def ok(genres):
        for genre in genres:
            for allowed in allowed_genres:
                if allowed in genre:
                    return True
        return False
    if len(allowed_genres) > 0:
        sp_artist = sp.artist(album["artists"][0]["id"])
        ok = ok(sp_artist["genres"])
        if not ok:
            return False
        print(f"Adding {term} ({', '.join(sp_artist['genres'])})")
    else:
        print(f"Adding {term}")
        ok = True
    
    tracks = [f"spotify:track:{x['id']}" for x in album["tracks"]["items"]]
    sp.playlist_add_items(playlist_id=list_id, items=tracks)
    added_titles.append(term)
    
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
