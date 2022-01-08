# gen(2022)

some scripts to generate a spotify playlist based on data from various sources

## requirements

install poetry and run `poetry install`

## running

you may use data from a tracker or rateyourmusic, or both in combination.

### fetch_from_tracker

```
poetry run python fetch_from_tracker.py [-h] [--apikey APIKEY] tracker_url target
```

the command requires

- `tracker_url`, e.g. "https://mytracker.com/"
- `target`, e.g. "data/tracker_albums.json"

`--apikey` is also required, although it's probably better to create a file named `secret.py` with the following contents:

```py
apikey = "your_api_key_here"
```

### parse_rym_html

```
poetry run python parse_rym_html.py [-h] dir target
```

first, you'll need a populated rym_html folder.

#### populating the rym_html directory

since rateyourmusic prohibits automated tools, we have to fetch data manually.
i only know how to do this with firefox, but the process might be similar in other browsers.

1. browse to https://rateyourmusic.com/charts/popular/album/2022/ or https://rateyourmusic.com/charts/daily/popular/album/2022/ if you're a premium user
2. for every page in the chart, hit ctrl+s to save the webpage, save as "Web Page HTML only" into the `rym_html` directory.

---

the command requires

- `dir`, e.g. "rym_html/"
- `target`, e.g. "data/rym_albums.json"


### generate_playlist

```
poetry run python generate_playlist.py [-h] data_dir playlist_url
```

this command should be run after some data has been generated in `data/`

first, set these environment variables:

- `SPOTIPY_CLIENT_ID`
- `SPOTIPY_CLIENT_SECRET`
- `SPOTIPY_REDIRECT_URI`

you can find the values for these in https://developer.spotify.com/dashboard/applications

the command requires

- `data_dir`, e.g. "data/"
- `playlist_url`, it's best to create a new empty playlist, right click it and select share -> copy link to playlist. use this as the argument

