import os
import csv
import json
import requests
import progressbar
import configparser
from colorama import Fore
from colorama import Style

config = configparser.ConfigParser()
module_dir = os.path.dirname(__file__)
config_path = os.path.join(module_dir, 'config.ini')
config.read(config_path)

youtube_api_key = config.get('apikey', 'youtube')
path = config.get('params', 'path')
playlists = json.loads(config.get('params', 'playlists'))

def fetch_playlist_name(playlist_id):
    url = f"https://www.googleapis.com/youtube/v3/playlists"
    params = {
        "key": youtube_api_key,
        "id": playlist_id,
        "part": "snippet",
        "maxResults": "1"
    }
    res = requests.get(url, params).json()

    return res["items"][0]["snippet"]["title"]

def fetch_playlist_page(playlist_id, page_token=None):
    url = f"https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "key": youtube_api_key,
        "pageToken": page_token,
        "playlistId": playlist_id,
        "part": "snippet",
        "maxResults": "50"
    }
    res = requests.get(url, params).json()

    items = { i["snippet"]["resourceId"]["videoId"]: i["snippet"]["title"] for i in res["items"] }
    next_page = res["nextPageToken"] if "nextPageToken" in res else None
    count = res["pageInfo"]["totalResults"]

    return (items, next_page, count)

def fetch_playlist(playlist_id):
    (fetched, next, count) = fetch_playlist_page(playlist_id)

    if count > 100:
        progress = progressbar.ProgressBar(max_value=count)

    while next != None:
        if count > 100:
            progress.update(len(fetched))

        (items, next, count) = fetch_playlist_page(playlist_id, next)
        fetched.update(items)

    if count > 100:
        progress.update(len(fetched))
        progress.finish()

    return fetched

def read_playlist_file(playlist_id):
    try:
        fpath = os.path.join(path, f"{playlist_id}.ipl")

        with open(fpath, 'r') as file:
            reader = csv.reader(file)
            next(reader)
            items = [row for row in reader]

        return items
    except:
        return []

def write_playlist_file(rows, playlist_id):
    fpath = os.path.join(path, f"{playlist_id}.ipl")
    header = ["#IPL", "1.1", "YOUTUBE", len(rows), playlist_id]

    with open(fpath, 'w+') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)

def print_info_rename(old, new, id):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.BLUE}i{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Song was renamed from {Fore.BLUE}{old}{Style.RESET_ALL} to {Fore.BLUE}{new}{Style.RESET_ALL}"
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print("  ", p0, p1, p2)

def print_info_filenotfound(file):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.YELLOW}!{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Could not find file {Fore.YELLOW}{file}{Style.RESET_ALL}"
    print("  ", p0, p1)

def print_info_createfile(file):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.YELLOW}!{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Creating new file {Fore.YELLOW}{file}{Style.RESET_ALL}"
    print("  ", p0, p1)

def print_info_writingfile(file):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.YELLOW}!{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Writing to file {Fore.YELLOW}{file}{Style.RESET_ALL}"
    print("  ", p0, p1)

def print_info_missing(title, id):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.RED}×{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}{Fore.RED}{title}{Style.RESET_ALL} is missing from the playlist{Style.RESET_ALL}"
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print("  ", p0, p1, p2)

def print_info_added(title, id):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.GREEN}+{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}New song {Fore.GREEN}{title}{Style.RESET_ALL} found"
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print("  ", p0, p1, p2)

for pl in playlists:
    name = fetch_playlist_name(pl)

    p0 = f"{Style.RESET_ALL}{Fore.RED}▶{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Fetching playlist {Fore.RED}{name}{Style.RESET_ALL}..."
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{pl}]{Style.RESET_ALL}"
    print(p0, "{:60}".format(p1), p2)

    out = read_playlist_file(pl)
    old = { i[1]: i for i in out }
    new = fetch_playlist(pl)

    fname = f"{pl}.ipl"
    fpath = os.path.join(path, fname)
    if not os.path.exists(fpath):
        print_info_filenotfound(fname)

    dirty = changed = False

    added = []
    for id, title in new.items():
        if id not in old:
            print_info_added(title, id)
            added.append(["", id, title])
            dirty = changed = True
    out = added + out

    for i, [flag, id, title] in enumerate(out):
        if id not in new and flag != "!":
            print_info_missing(title, id)
            out[i][0] = "!"
            dirty = changed = True

    for [_, id, title] in out:
        if id in new and title != new[id]:
            print_info_rename(title, new[id], id)
            changed = True

    if dirty:
        if not os.path.exists(fpath):
            print_info_createfile(fname)
        print_info_writingfile(fname)
        write_playlist_file(out, pl)
    elif not changed:
        print("  (no changes)")

    print()
