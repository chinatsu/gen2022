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
from datetime import date, datetime

parser = ArgumentParser()
parser.add_argument("data_dir")
parser.add_argument("--genre-file")
args = parser.parse_args()

if not os.path.isdir(args.data_dir):
    print("That's not a directory")
    exit()

scope = "playlist-modify-private playlist-modify-public"
sp = Spotify(auth_manager=SpotifyOAuth(scope=scope))

def get_all_playlists():
    total = -1
    offset = 0
    playlists = []
    while total != len(playlists):
        p = sp.current_user_playlists(offset=offset*50)
        if total < 0:
            total = p["total"]
        playlists+= p["items"]
        offset+=1
    return playlists

def create_playlist(name, description):
    playlist = sp.user_playlist_create(sp.me()["id"], name, True, False, description)
    return playlist["id"]

def get_albums_in_playlist(playlist_id):
    total = -1
    offset = 0
    songs = []
    while len(songs) != total:
        playlist = sp.playlist_items(playlist_id, offset=offset*100, fields="total,items.track.album(name,artists,release)")
        if total < 0:
            total = playlist["total"]
        songs += playlist["items"]
        offset += 1
    albums = list(set([format_album(x) for x in songs]))
    return albums

def get_week_playlists():
    p = get_all_playlists()
    playlist_ids = {}
    for x in range(1, date.today().isocalendar()[1]+3):
        target = f"gen(2022): week {x}"
        found = False
        for playlist in p:
            if playlist["name"] == target:
                playlist_ids[f"{x}"] = {
                    "titles": get_albums_in_playlist(playlist["id"]),
                    "id": playlist["id"]
                }
                found = True
        if not found:
            playlist_ids[f"{x}"] = {
                "titles": [],
                "id": create_playlist(target, f"all songs released in week {x} of 2022")
            }
    return playlist_ids

def format_album(song):
    title = song["track"]["album"]["name"]
    artist = song["track"]["album"]["artists"][0]["name"]
    return f"{artist} - {title}"

week_playlists = get_week_playlists()

allowed_genres = []

if args.genre_file:
    with open(args.genre_file) as f:
        allowed_genres = json.load(f)

def is_already_in_playlist(album, playlists):
    # it's just a maybe-check, but it should help with some speed anyway
    term = f"{album['artist']} - {album['title']}"
    if "release_date" in album:
        try:
            rls = album['release_date'].split(" ")
            if len(rls[0]) == 1 and rls[0].isdigit():
                rls[0] = f"{rls[0]:0>2}"
            if rls[0] in ["01", "02"] and rls[1] == "January":
                week = "1"
                if term in playlists[week]["titles"]:
                    print(f"!!! Album {term} should already be added")
                    return True
            week = datetime.strptime(" ".join(rls), "%d %B %Y").date().isocalendar().week
            if term in playlists[f"{week}"]["titles"]:
                print(f"!!! Album {term} should already be added")
                return True
        except:
            pass
    return False

def search_and_add_album(album, playlists):
    term = f"{album['artist']} - {album['title']}"
    search = sp.search(term.lower(), type="album")
    for item in search["albums"]["items"]:
        artist_score = process.extractOne(album['artist'].lower(), [a["name"].lower() for a in item["artists"]])[-1]
        title_score = fuzz.partial_ratio(album['title'].lower(), item["name"].lower())
        score = artist_score + title_score
        if score > 180:
            return add_album_to_playlist(item["id"], playlists)
    return False


def ok(genres):
    for genre in genres:
        for allowed in allowed_genres:
            if allowed in genre:
                return True
    return False

def add_album_to_playlist(album_id, playlists):
    album = sp.album(album_id)
    artist = album["artists"][0]["name"]
    title = album["name"]
    term = f"{artist} - {title}"
    release_date = album["release_date"]
    if not release_date.startswith("2022"):
        print(f"!!! {term} appears to have been released in {album['release_date']}, skipping")
        return False
    week = datetime.strptime(release_date, "%Y-%m-%d").date().isocalendar().week
    if len(release_date) != 10:
        print(release_date)
    if release_date in ["2022-01-01", "2022-01-02"]:
        week = 1 # lol
    if not f"{week}" in playlists:
        print(f"{release_date}, weird")
        return False
    playlist = playlists[f"{week}"]
    if term in playlist["titles"]:
        print(f"!!! Album {term} should already be added")
        return False
    if len(allowed_genres) > 0:
        sp_artist = sp.artist(album["artists"][0]["id"])
        if not ok(sp_artist["genres"]):
            return False
        print(f"Adding {term} ({', '.join(sp_artist['genres'])})")
    else:
        print(f"Adding {term}")
    tracks = [f"spotify:track:{x['id']}" for x in album["tracks"]["items"]]
    sp.playlist_add_items(playlist_id=playlist["id"], items=tracks)
    playlist["titles"].append(term)
    
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
                if is_already_in_playlist(album, week_playlists):
                    continue
                if search_and_add_album(album, week_playlists):
                    pass
                elif "urls" in album and "spotify" in album["urls"]:
                    # backup for the RYM dataset if no album was found by searching
                    album_id = album["urls"]["spotify"].split("?")[0].split("/")[-1]
                    add_album_to_playlist(album_id, week_playlists)
                
print(f"Done :)")
