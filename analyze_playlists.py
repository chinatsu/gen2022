try:
    import secret
except ImportError:
    pass
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import json

scope = "playlist-modify-private playlist-modify-public"
sp = Spotify(auth_manager=SpotifyOAuth(scope=scope))

def format_album(song):
    title = song["track"]["album"]["name"]
    artist = song["track"]["album"]["artists"][0]["name"]
    return f"{artist} - {title}"

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

def get_albums_in_playlist(playlist_id):
    total = -1
    offset = 0
    songs = []
    albums = {}
    while len(songs) != total:
        playlist = sp.playlist_items(playlist_id, offset=offset*100, fields="total,items.track.album(id,name,artists,release_date,type)")
        if total < 0:
            total = playlist["total"]
        songs += playlist["items"]
        for item in playlist["items"]:
            album = item["track"]["album"]
            album_title = format_album(item)
            if album_title in albums:
                continue
            for i, artist in enumerate(album["artists"]):
                a = sp.artist(artist["id"])
                album["artists"][i] = dict(
                    popularity = a["popularity"],
                    genres = a["genres"],
                    name = artist["name"],
                    id = artist["id"],
                    type = artist["type"],
                )
            albums[album_title] = album
        offset += 1
    return sorted(albums.values(), key=lambda x: x["release_date"])

def get_week_playlists():
    p = get_all_playlists()
    playlists = {}
    for x in range(1, 52):
        target = f"gen(2022): week {x}"
        found = False
        for playlist in p:
            if playlist["name"] == target:
                playlists[f"{x}"] = {
                    "releases": get_albums_in_playlist(playlist["id"]),
                    "id": playlist["id"]
                }
                found = True
        if not found:
            print(f"Couldn't find playlist for week {x}")
            continue
    return playlists

for k,playlist in get_week_playlists().items():
    if len(playlist["releases"]) == 0:
        continue
    fname = f"reports/week_{k}.json"
    with open(fname, 'w', encoding="utf-8") as f:
        print(f"Creating report json: {fname}")
        json.dump(playlist, f, ensure_ascii=False, sort_keys=True, indent=2)
