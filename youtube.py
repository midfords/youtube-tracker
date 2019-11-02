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

def auth():
    scope = ["https://www.googleapis.com/auth/youtube.readonly"]
    storage_path = os.path.join(module_dir, 'credentials.storage')

    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    storage = Storage(storage_path)
    credentials = storage.get()
    credentials.refresh(httplib2.Http())

    if credentials is None or credentials.invalid or credentials.__dict__["token_expiry"] < datetime.datetime.now():
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
    THRESHOLD = 100
    (fetched, next, count) = fetch_playlist_page(playlist_id, token)

    if count > THRESHOLD:
        progress = progressbar.ProgressBar(max_value=count)

    while next != None:
        if count > THRESHOLD:
            progress.update(len(fetched))

        (items, next, count) = fetch_playlist_page(playlist_id, token, next)
        fetched.update(items)

    if count > THRESHOLD:
        progress.update(len(fetched))
        progress.finish()

    return fetched

def print_head_signin(username):
    p0 = f"{Style.RESET_ALL}{Fore.RED}👤{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Signed in as {Fore.MAGENTA}{username}{Style.RESET_ALL}"
    print(p0, p1)

def print_head_fetching(id, title):
    p0 = f"{Style.RESET_ALL}{Fore.RED}▶{Style.RESET_ALL}"
    p1 = "{:60}".format(f"{Style.RESET_ALL}Fetching {Fore.RED}{title}{Style.RESET_ALL} playlist...")
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print(p0, p1, p2)

def print_err_plnotfound(id):
    p0 = f"{Style.RESET_ALL}{Fore.RED}▶{Style.RESET_ALL}"
    p1 = "{:60}".format(f"{Style.RESET_ALL}Could not access {Fore.RED}Unknown{Style.RESET_ALL} playlist.")
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print(p0, p1, p2)

def print_info_added(id, title):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.GREEN}+{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}New song {Fore.GREEN}{title}{Style.RESET_ALL} found"
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print("  ", p0, p1, p2)

def print_info_rename(id, old, new):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.BLUE}i{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Song was renamed from {Fore.BLUE}{old}{Style.RESET_ALL} to {Fore.BLUE}{new}{Style.RESET_ALL}"
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print("  ", p0, p1, p2)

def print_info_missing(id, title):
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

def is_empty(list):
    return len(list) == 0

def read_playlist_file(playlist_id):
    """Reads in a csv file of playlist information.

    If there is no file, or the file is empty, the function
    will return an empty list.The header of the file is 
    always the first row and formatted as:
    #file_type, version_id, playlist_origin, count, playlist_id

    Parameters
    ----------
    playlist_id : str
        The playlist id, used to find the csv file on disk.

    Returns
    -------
    list
        a list of all the song items, formatted as [flag, video_id, title]
    """
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
    """Writes in a csv file the playlist information and songs.

    If there is no file, the function will create a new file. The
    header of the file is always the first row and formatted as:
    #file_type, version_id, playlist_origin, count, playlist_id

    Parameters
    ----------
    rows : list
        The songs to write to the file, formatted as: [flag, video_id, title]
    playlist_id : str
        The playlist id, used to find the csv file on disk.
    """
    fpath = os.path.join(path, f"{playlist_id}.ipl")
    header = ["#IPL", "1.1", "YOUTUBE", len(rows), playlist_id]

    with open(fpath, 'w+') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)

def find_added_items(master, new_items):
    """Compares the items from the new_items list and master list,
    and finds all the added items.

    Parameters
    ----------
    master: list
        list of all items, formatted as [flag, video_id, title]
    new_items : dict
        list of new items, formatted as { video_id : [flag, video_id, title] }

    Returns
    -------
    list
        a list of all the added songs, formatted as (video_id, title)
    """
    added = []
    index = 0
    old_items = { i[1]: i for i in master }
    for id, title in new_items.items():
        if id not in old_items:
            added.append((id, title))
            master.insert(index, ["", id, title])
            index += 1

    return added

def find_missing_items(master, new_items):
    """Compares the items from the new_items list and master list,
    and finds all the missing items.

    Parameters
    ----------
    master: list
        list of all items, formatted as [flag, video_id, title]
    new_items : dict
        list of new items, formatted as { video_id : [flag, video_id, title] }

    Returns
    -------
    list
        a list of all the missing songs, formatted as (video_id, title)
    """
    MISSING_FLAG = "!"
    missing = []
    for i, [flag, id, title] in enumerate(master):
        if id not in new_items and flag != MISSING_FLAG:
            master[i][0] = MISSING_FLAG
            missing.append((id, title))

    return missing

def find_renamed_items(master, new_items):
    """Compares the items from the new_items list and master list,
    and finds all the renamed items.

    Parameters
    ----------
    master: list
        list of all items, formatted as [flag, video_id, title]
    new_items : dict
        list of new items, formatted as { video_id : [flag, video_id, title] }

    Returns
    -------
    list
        a list of all the renamed songs, formatted as (video_id, old_title, new_title)
    """
    renamed = []
    for [_, id, title] in master:
        if id in new_items and title != new_items[id]:
            renamed.append((id, title, new_items[id]))

    return renamed

def main():
    token = auth()
    user = fetch_username(token)
    print_head_signin(user)
    print()

    for playlist in playlists:
        try:
            name = fetch_playlist_name(playlist, token)
            print_head_fetching(playlist, name)
        except:
            print_err_plnotfound(playlist)
            continue

        master = read_playlist_file(playlist)
        new = fetch_playlist(playlist, token)

        fname = f"{playlist}.ipl"
        fpath = os.path.join(path, fname)
        if not os.path.exists(fpath):
            print_warn_filenotfound(fname)

        added = find_added_items(master, new)
        missing = find_missing_items(master, new)
        renamed = find_renamed_items(master, new)

        for item in added:
            id = item[0]
            title = item[1]
            print_info_added(id, title)

        for item in missing:
            id = item[0]
            title = item[1]
            print_info_missing(id, title)

        for item in renamed:
            id = item[0]
            old_title = item[1]
            new_title = item[2]
            print_info_rename(id, old_title, new_title)

        if not is_empty(added) or not is_empty(missing):
            if not os.path.exists(fpath):
                print_warn_createfile(fname)
            print_warn_writingfile(fname)
            write_playlist_file(master, playlist)

        elif is_empty(renamed):
            print_info_nochanges()

        print()

if __name__ == "__main__":
    main()
