import os
import io
import sys
import csv
import json
import httplib2
import requests
import datetime
import argparse
import progressbar
import configparser
from colorama import Fore
from colorama import Style
from oauth2client.file import Storage
from oauth2client.tools import argparser
from oauth2client.tools import run_flow
from oauth2client.client import flow_from_clientsecrets

parser = argparse.ArgumentParser(description='Flags to change the running behavior of the youtube diff script.')
parser.add_argument('-r', '--reauth', action='store_true', help='force the script to reauthenticate.')
parser.add_argument('-v', '--verbose', action='store_true', help='output all verbose messages.')
parser.add_argument('-t', '--test', action='store_true', help='read params from config_test.ini.')
args = parser.parse_args()

REAUTH_FLAG = args.reauth
VERBOSE_FLAG = args.verbose
TEST_FLAG = args.test

MISSING_FLAG = "!"
PROGRESS_THRESHOLD = 100

config = configparser.ConfigParser()
module_dir = os.path.dirname(__file__)
config_file = 'config_test.ini' if TEST_FLAG else 'config.ini'
config_path = os.path.join(module_dir, config_file)
config.read(config_path)

api_key = config.get('keys', 'api')
path = config.get('params', 'path')
client_secret = config.get('params', 'secret_path')
playlists = json.loads(config.get('params', 'playlists'))

def auth():
    scope = ["https://www.googleapis.com/auth/youtube.readonly"]
    storage_path = os.path.join(module_dir, 'credentials.storage')

    if not VERBOSE_FLAG:
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

    storage = Storage(storage_path)
    credentials = storage.get()
    print_verbose_message("Refreshing stored credentials.")
    credentials.refresh(httplib2.Http())

    credentials_empty = credentials is None
    credentials_expired = \
        credentials.__dict__["token_expiry"] < datetime.datetime.now() or \
        credentials.invalid

    print_verbose_message("Could not find credentials from storage.", condition=credentials_empty)
    print_verbose_message("Could not find credentials from storage.", condition=credentials_expired)
    print_verbose_message("Forcing reauthentication.", condition=REAUTH_FLAG)

    if credentials_empty or credentials_expired or REAUTH_FLAG:
        print_verbose_message("Starting new oauth2 authentication flow.")
        flow = flow_from_clientsecrets(client_secret, scope=scope)
        flags = argparser.parse_args(args=[])
        credentials = run_flow(flow, storage, flags=flags)

    token = credentials.__dict__["access_token"]
    print_verbose_message(f"Using access token '{token}'")

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    return token

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

    if count > PROGRESS_THRESHOLD:
        progress = progressbar.ProgressBar(max_value=count)

    while next != None:
        if count > PROGRESS_THRESHOLD:
            progress.update(len(fetched))

        (items, next, count) = fetch_playlist_page(playlist_id, token, next)
        fetched.update(items)

    if count > PROGRESS_THRESHOLD:
        progress.update(len(fetched))
        progress.finish()

    print_verbose_message(f"Fetched {len(fetched)} item(s) from playlist {playlist_id}")

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

def print_verbose_message(msg, condition=True):
    if not VERBOSE_FLAG or not condition:
        return

    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.WHITE}»{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}{msg}"
    print(p0, p1)

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

        print_verbose_message(f"Read {len(items)} row(s) from '{playlist_id}.ipl'")

        if VERBOSE_FLAG:
            missing = 0
            for item in items:
                if item[0] == MISSING_FLAG:
                    missing += 1
            print_verbose_message(f"{missing} item(s) already marked as missing.")

        return items
    except Error as err:
        print_verbose_message(err)
        return []

def write_playlist_file(rows, playlist_id, name):
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
    header = ["#IPL", "1.1", "YOUTUBE", len(rows), playlist_id, name]

    print_verbose_message(f"Writing {len(rows)} row(s) to '{playlist_id}.ipl'")
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
    master : list
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
            print_verbose_message(f"Found unrecognized id {id} - {title}")
            added.append((id, title))
            master.insert(index, ["", id, title])
            index += 1

    print_verbose_message("No unrecognized ids found. ", condition=is_empty(added))
    print_verbose_message(f"{len(added)} unrecognized id(s) found. ", condition=not is_empty(added))

    return added

def find_missing_items(master, new_items):
    """Compares the items from the new_items list and master list,
    and finds all the missing items.

    Parameters
    ----------
    master : list
        list of all items, formatted as [flag, video_id, title]
    new_items : dict
        list of new items, formatted as { video_id : [flag, video_id, title] }

    Returns
    -------
    list
        a list of all the missing songs, formatted as (video_id, title)
    """
    missing = []
    for i, [flag, id, title] in enumerate(master):
        if id not in new_items and flag != MISSING_FLAG:
            print_verbose_message(f"Found missing id at position {i}, {master[i]}")
            master[i][0] = MISSING_FLAG
            missing.append((id, title))

    print_verbose_message("No missing ids found. ", condition=is_empty(missing))
    print_verbose_message(f"{len(missing)} missing id(s) found. ", condition=not is_empty(missing))

    return missing

def find_renamed_items(master, new_items):
    """Compares the items from the new_items list and master list,
    and finds all the renamed items.

    Parameters
    ----------
    master : list
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
            print_verbose_message(f"Found renamed item {id}, {title} > {new_items[id]}")
            renamed.append((id, title, new_items[id]))

    print_verbose_message("No renamed items found. ", condition=is_empty(renamed))
    print_verbose_message(f"{len(renamed)} renamed item(s) found.", condition=not is_empty(renamed))

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
            write_playlist_file(master, playlist, name)

        elif is_empty(renamed):
            print_info_nochanges()

        print()

if __name__ == "__main__":
    main()
