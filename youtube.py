import os
import csv
import json
import requests
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

def map_playlist_item(item):
    return {
        "id": item["snippet"]["resourceId"]["videoId"],
        "title": item["snippet"]["title"]
    }

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
    page_token = res["nextPageToken"] if "nextPageToken" in res else None

    return (list(map(map_playlist_item, res["items"])), page_token)

def fetch_playlist(playlist_id):
    (total, next) = fetch_playlist_page(playlist_id)

    while next != None:
        (items, next) = fetch_playlist_page(playlist_id, next)
        total.extend(items)

    return total

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
    fname = f"{pl}.ipl"
    fpath = os.path.join(path, fname)

    p0 = f"{Style.RESET_ALL}{Fore.RED}▶{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Fetching playlist {Fore.RED}{name}{Style.RESET_ALL}..."
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{pl}]{Style.RESET_ALL}"
    print(p0, "{:60}".format(p1), p2)

    if not os.path.exists(fpath):
        print_info_filenotfound(fname)

    old_l = read_playlist_file(pl)
    old_d = { i[1]: i for i in old_l }

    new_l = fetch_playlist(pl)
    new_d = { i["id"]: i for i in new_l }

    dirty = False
    none = True
    upd = old_l.copy()

    p = 0
    for i in new_l:
        if i["id"] not in old_d:
            print_info_added(i["title"], i["id"])
            upd.insert(p, ["", i["id"], i["title"]])
            p += 1
            dirty = True
            none = False

    for (k, v) in old_d.items():
        if k not in new_d and v[0] != "!":
            print_info_missing(v[2], v[1])
            for i in upd:
                if i[1] == k:
                    i[0] = "!"
            dirty = True
            none = False
        if k in new_d and v[2] != new_d[k]["title"]:
            print_info_rename(v[2], new_d[k]["title"], k)
            none = False

    if dirty:
        if not os.path.exists(fpath):
            print_info_createfile(fname)
        print_info_writingfile(fname)
        write_playlist_file(upd, pl)

    elif none:
        print("  (no changes)")

    print()
