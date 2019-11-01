import os
import io
import sys
import csv
import json
import httplib2
import requests
import datetime
import progressbar
import configparser
from colorama import Fore
from colorama import Style
from oauth2client.file import Storage
from oauth2client.tools import run_flow
from oauth2client.client import flow_from_clientsecrets

config = configparser.ConfigParser()
module_dir = os.path.dirname(__file__)
config_path = os.path.join(module_dir, 'config.ini')
config.read(config_path)

api_key = config.get('keys', 'api')
path = config.get('params', 'path')
client_secret = config.get('params', 'secret_path')
playlists = json.loads(config.get('params', 'playlists'))

def auth(new_auth=False):
    scope = ["https://www.googleapis.com/auth/youtube.readonly"]
    storage_path = os.path.join(module_dir, 'credentials.storage')

    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    storage = Storage(storage_path)
    credentials = storage.get()
    credentials.refresh(httplib2.Http())

    if credentials is None or credentials.invalid or credentials.__dict__["token_expiry"] < datetime.datetime.now() or new_auth:
        flow = flow_from_clientsecrets(client_secret, scope=scope)
        credentials = run_flow(flow, storage)

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    return credentials.__dict__["access_token"]

def fetch_username(token):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "key": api_key,
        "mine": "true",
        "part": "snippet",
        "maxResults": "1"
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    res = requests.get(url, params=params, headers=headers).json()

    return res["items"][0]["snippet"]["title"]

def fetch_playlist_name(playlist_id, token=None):
    url = "https://www.googleapis.com/youtube/v3/playlists"
    params = {
        "key": api_key,
        "id": playlist_id,
        "part": "snippet",
        "maxResults": "1"
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    if token == None:
        res = requests.get(url, params=params).json()
    else:
        res = requests.get(url, params=params, headers=headers).json()

    return res["items"][0]["snippet"]["title"]

def fetch_playlist_page(playlist_id, token=None, page_token=None):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "key": api_key,
        "pageToken": page_token,
        "playlistId": playlist_id,
        "part": "snippet",
        "maxResults": "50"
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    if token == None:
        res = requests.get(url, params=params).json()
    else:
        res = requests.get(url, params=params, headers=headers).json()

    items = { i["snippet"]["resourceId"]["videoId"]: i["snippet"]["title"] for i in res["items"] }
    next_page = res["nextPageToken"] if "nextPageToken" in res else None
    count = res["pageInfo"]["totalResults"]

    return (items, next_page, count)

def fetch_playlist(playlist_id, token=None):
    (fetched, next, count) = fetch_playlist_page(playlist_id, token)

    if count > 100:
        progress = progressbar.ProgressBar(max_value=count)

    while next != None:
        if count > 100:
            progress.update(len(fetched))

        (items, next, count) = fetch_playlist_page(playlist_id, token, next)
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

def print_head_signin(username):
    p0 = f"{Style.RESET_ALL}{Fore.RED}👤{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Signed in as {Fore.MAGENTA}{username}{Style.RESET_ALL}"
    print(p0, p1)

def print_head_fetching(title, id):
    p0 = f"{Style.RESET_ALL}{Fore.RED}▶{Style.RESET_ALL}"
    p1 = "{:60}".format(f"{Style.RESET_ALL}Fetching {Fore.RED}{title}{Style.RESET_ALL} playlist...")
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print(p0, p1, p2)

def print_err_plnotfound(id):
    p0 = f"{Style.RESET_ALL}{Fore.RED}▶{Style.RESET_ALL}"
    p1 = "{:60}".format(f"{Style.RESET_ALL}Could not access {Fore.RED}Unknown{Style.RESET_ALL} playlist.")
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print(p0, p1, p2)

def print_info_added(title, id):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.GREEN}+{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}New song {Fore.GREEN}{title}{Style.RESET_ALL} found"
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print("  ", p0, p1, p2)

def print_info_rename(old, new, id):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.BLUE}i{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Song was renamed from {Fore.BLUE}{old}{Style.RESET_ALL} to {Fore.BLUE}{new}{Style.RESET_ALL}"
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print("  ", p0, p1, p2)

def print_info_missing(title, id):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.RED}×{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}{Fore.RED}{title}{Style.RESET_ALL} is missing from the playlist{Style.RESET_ALL}"
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print("  ", p0, p1, p2)

def print_info_nochanges():
    print("  (no changes)")

def print_warn_filenotfound(file):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.YELLOW}!{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Could not find file {Fore.YELLOW}{file}{Style.RESET_ALL}"
    print("  ", p0, p1)

def print_warn_createfile(file):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.YELLOW}!{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Creating new file {Fore.YELLOW}{file}{Style.RESET_ALL}"
    print("  ", p0, p1)

def print_warn_writingfile(file):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.YELLOW}!{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Writing to file {Fore.YELLOW}{file}{Style.RESET_ALL}"
    print("  ", p0, p1)

new_auth = len(sys.argv) > 1 and sys.argv[1] == '--auth'
token = auth(new_auth)
user = fetch_username(token)
print_head_signin(user)
print()

for pl in playlists:
    try:
        name = fetch_playlist_name(pl, token)
        print_head_fetching(name, pl)
    except:
        print_err_plnotfound(pl)
        continue

    out = read_playlist_file(pl)
    old = { i[1]: i for i in out }
    new = fetch_playlist(pl, token)

    fname = f"{pl}.ipl"
    fpath = os.path.join(path, fname)
    if not os.path.exists(fpath):
        print_warn_filenotfound(fname)

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
            print_warn_createfile(fname)
        print_warn_writingfile(fname)
        write_playlist_file(out, pl)
    elif not changed:
        print_info_nochanges()

    print()
