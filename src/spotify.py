import argparse
import configparser
import csv
import datetime
import io
import json
import logging
import os
import progressbar
import spotipy
import sys
from colorama import Fore
from colorama import Style
from spotipy.oauth2 import SpotifyOAuth

# Setup paths

src_dir = os.path.dirname(__file__)
module_dir = os.path.join(src_dir, '..')
config_path = os.path.join(module_dir, 'config/config-spotify.ini')

# Setup logging

timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
log_name = f"application-spotify-{timestamp}.log"
log_path = os.path.join(module_dir, "logs")
log_file = os.path.join(log_path, log_name)

if not os.path.exists(log_path):
    os.makedirs(log_path)

logging.basicConfig(filename=log_file)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Setup CLI arguments and flags

parser = argparse.ArgumentParser(description='Flags to change the running behavior of the spotify diff script.')
parser.add_argument('-r', '--reauth', action='store_true', help='force the script to reauthenticate.')
parser.add_argument('-v', '--verbose', action='store_true', help='output all verbose messages.')
parser.add_argument('-c', '--config', help='run script using specific config file.')
args = parser.parse_args()

REAUTH_FLAG = args.reauth
VERBOSE_FLAG = args.verbose
config_path = args.config if args.config is not None else config_path

log.info(f"Running with config file located at {config_path}.")

MAX_LIMIT = 50
MISSING_FLAG = "!"
UNAVAILABLE_FLAG = "u"
PROGRESS_THRESHOLD = 200

# Setup config

config = configparser.ConfigParser()
config.read(config_path)

playlists = json.loads(config.get('params', 'playlists'))
market = config.get('params', 'market')
path = config.get('params', 'path')
creds_path = config.get('params', 'secret_path')
cache_path = config.get('params', 'cache_path')

if not os.path.exists(path):
    log.warning(f"Could not find path {path}, creating directories.")
    os.makedirs(path)

def auth():
    with open(creds_path, 'r') as file:
        creds = json.loads(file.read())

    if not VERBOSE_FLAG and not REAUTH_FLAG:
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

    if REAUTH_FLAG and os.path.exists(cache_path):
        print_verbose_and_log(f"Forcing reauthentication by removing {cache_path}.")
        os.remove(cache_path)

    print_verbose_and_log("Refreshing stored credentials.")

    client = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope=creds['scope'],
        client_id=creds['client_id'],
        client_secret=creds['client_secret'],
        redirect_uri=creds['redirect_uri'],
        cache_path=cache_path
    ))

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    return client

def fetch_username(client):
    return client.current_user()['display_name']

def fetch_playlist_name(client, id):
    return client.playlist(playlist_id=id)['name']

def fetch_playlist_page(client, id, offset=0):
    resp = client.playlist_items(playlist_id=id, limit=100, offset=offset)
    items = filter(lambda i: not i['track']['is_local'], resp['items'])

    items = { i['track']['id']: f"{i['track']['artists'][0]['name']} - {i['track']['name']}" for i in items }
    count = resp['offset'] + len(resp['items'])
    total = resp['total']

    return (items, count, total)

def fetch_playlist(client, id):
    (fetched, count, total) = fetch_playlist_page(client, id)

    if total > PROGRESS_THRESHOLD:
        progress = progressbar.ProgressBar(max_value=total)

    while count < total:
        if total > PROGRESS_THRESHOLD:
            progress.update(count)

        (items, count, total) = fetch_playlist_page(client, id, count)
        fetched.update(items)

    if total > PROGRESS_THRESHOLD:
        progress.update(len(fetched))
        progress.finish()

    print_verbose_and_log(f"Fetched {len(fetched)} item(s) from playlist {id}")

    return fetched

def fetch_library_page(client, offset=0):
    resp = client.current_user_saved_tracks(limit=MAX_LIMIT, offset=offset)
    items = filter(lambda i: not i['track']['is_local'], resp['items'])

    items = { i['track']['id']: f"{i['track']['artists'][0]['name']} - {i['track']['name']}" for i in resp['items'] }
    count = resp['offset'] + len(resp['items'])
    total = resp['total']

    return (items, count, total)

def fetch_library(client):
    (fetched, count, total) = fetch_library_page(client)

    if total > PROGRESS_THRESHOLD:
        progress = progressbar.ProgressBar(max_value=total)

    while count < total:
        if total > PROGRESS_THRESHOLD:
            progress.update(count)

        (items, count, total) = fetch_library_page(client, count)
        fetched.update(items)

    if total > PROGRESS_THRESHOLD:
        progress.update(len(fetched))
        progress.finish()

    print_verbose_and_log(f"Fetched {len(fetched)} item(s) from user's library")

    return fetched

def print_head_signin(username):
    p0 = f"{Style.RESET_ALL}{Fore.RED}👤{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}Signed in to {Fore.GREEN}Spotify{Style.RESET_ALL} as {Fore.MAGENTA}{username}{Style.RESET_ALL}"
    print(p0, p1)

def print_head_fetching(id, title):
    out = title if len(title) < 60 else title[0:59] + "…"
    p0 = f"{Style.RESET_ALL}{Fore.GREEN}▶{Style.RESET_ALL}"
    p1 = "{:60}".format(f"{Style.RESET_ALL}Fetching {Fore.GREEN}{out}{Style.RESET_ALL} playlist from {Fore.GREEN}Spotify{Style.RESET_ALL}...")
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print(p0, p1, p2)

def print_err_plnotfound(id):
    p0 = f"{Style.RESET_ALL}{Fore.GREEN}▶{Style.RESET_ALL}"
    p1 = "{:60}".format(f"{Style.RESET_ALL}Could not access {Fore.GREEN}Unknown{Style.RESET_ALL} playlist.")
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print(p0, p1, p2)

def print_info_added(id, title):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.GREEN}+{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}New song {Fore.GREEN}{title}{Style.RESET_ALL} found"
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print("  ", p0, p1, p2)

def print_info_recovered(id, title):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.GREEN}↪{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}{Fore.GREEN}{title}{Style.RESET_ALL} was recovered"
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print("  ", p0, p1, p2)

def print_info_available(id, title):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.GREEN}✓{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}{Fore.GREEN}{title}{Style.RESET_ALL} is now playable in your region"
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

def print_info_unavailable(id, title):
    p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.RED} ⃠{Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}{Fore.RED}{title}{Style.RESET_ALL} is now unplayable in your region{Style.RESET_ALL}"
    p2 = f"{Style.RESET_ALL}{Style.DIM}[{id}]{Style.RESET_ALL}"
    print("  ", p0, p1, p2)

def print_info_nochanges():
    print("  (no new changes)")

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

def print_verbose_and_log(msg, condition=True, error=None):
    if condition and error:
        log.error(msg)
        log.exception(error)
    elif condition:
        log.info(msg)

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

        print_verbose_and_log(f"Read {len(items)} row(s) from '{playlist_id}.ipl'")

        if VERBOSE_FLAG:
            missing = 0
            for item in items:
                if item[0] == MISSING_FLAG:
                    missing += 1
            print_verbose_and_log(f"{missing} item(s) already marked as missing.")

        return items
    except Exception as err:
        print_verbose_and_log(f"Error occured while reading playlist file for {playlist_id}.", error=err)
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
    header = ["#IPL", "1.1", "SPOTIFY", len(rows), playlist_id, name]

    print_verbose_and_log(f"Writing {len(rows)} row(s) to '{playlist_id}.ipl'")
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
            print_verbose_and_log(f"Found unrecognized id {id} - {title}")
            added.append((id, title))
            master.insert(index, ["", id, title])
            index += 1

    print_verbose_and_log("No unrecognized ids found. ", condition=is_empty(added))
    print_verbose_and_log(f"{len(added)} unrecognized id(s) found. ", condition=not is_empty(added))

    return added

def find_recovered_items(master, new_items):
    """Compares the items from the new_items list and master list,
    and finds all ids present in new_items that were previously marked as missing.

    Parameters
    ----------
    master : list
        list of all items, formatted as [flag, video_id, title]
    new_items : dict
        list of new items, formatted as { video_id : [flag, video_id, title] }

    Returns
    -------
    list
        a list of all the recovered songs, formatted as (video_id, title)
    """
    recovered = []
    for i, [flag, id, title] in enumerate(master):
        if id in new_items and flag == MISSING_FLAG:
            print_verbose_and_log(f"Found recovered id {id} - {title}")
            recovered.append((id, title))
            master[i] = ["", id, title]

    print_verbose_and_log("No recovered ids found. ", condition=is_empty(recovered))
    print_verbose_and_log(f"{len(recovered)} recovered id(s) found. ", condition=not is_empty(recovered))

    return recovered

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
            print_verbose_and_log(f"Found missing id at position {i}, {master[i]}")
            master[i][0] = MISSING_FLAG
            missing.append((id, title))

    print_verbose_and_log("No missing ids found. ", condition=is_empty(missing))
    print_verbose_and_log(f"{len(missing)} missing id(s) found. ", condition=not is_empty(missing))

    return missing

def main():
    client = auth()
    user = fetch_username(client)
    print_head_signin(user)
    print()

    # Check for user library

    playlist = 'spotify_library'
    name = 'Library'

    print_head_fetching(playlist, name)

    master = read_playlist_file(playlist)
    new = fetch_library(client)

    fname = f"{playlist}.ipl"
    fpath = os.path.join(path, fname)
    if not os.path.exists(fpath):
        print_warn_filenotfound(fname)

    added = find_added_items(master, new)
    recovered = find_recovered_items(master, new)
    missing = find_missing_items(master, new)


    for item in added:
        id = item[0]
        title = item[1]
        print_info_added(id, title)

    for item in recovered:
        id = item[0]
        title = item[1]
        print_info_recovered(id, title)

    for item in missing:
        id = item[0]
        title = item[1]
        print_info_missing(id, title)


    if not is_empty(added) or not is_empty(missing) or not is_empty(recovered):
        if not os.path.exists(fpath):
            print_warn_createfile(fname)
        print_warn_writingfile(fname)
        write_playlist_file(master, playlist, name)

    else:
        print_info_nochanges()

    print()

    # Check for all other playlists

    for playlist in playlists:
        try:
            name = fetch_playlist_name(client, playlist)
            print_head_fetching(playlist, name)
        except Exception as err:
            print_verbose_and_log(f"Playlist {playlist} not found.", error=err)
            print_err_plnotfound(playlist)
            continue

        master = read_playlist_file(playlist)
        new = fetch_playlist(client, playlist)

        fname = f"{playlist}.ipl"
        fpath = os.path.join(path, fname)
        if not os.path.exists(fpath):
            print_warn_filenotfound(fname)

        added = find_added_items(master, new)
        recovered = find_recovered_items(master, new)
        missing = find_missing_items(master, new)


        for item in added:
            id = item[0]
            title = item[1]
            print_info_added(id, title)

        for item in recovered:
            id = item[0]
            title = item[1]
            print_info_recovered(id, title)

        for item in missing:
            id = item[0]
            title = item[1]
            print_info_missing(id, title)


        if not is_empty(added) or not is_empty(missing) or not is_empty(recovered):
            if not os.path.exists(fpath):
                print_warn_createfile(fname)
            print_warn_writingfile(fname)
            write_playlist_file(master, playlist, name)

        else:
            print_info_nochanges()

        print()

    log.info("Script exited successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print_verbose_and_log("Script exited unexpectedly.", error=err)
        raise err




# Todo: available, unavailable, check linked songs add ipl unavailable state, possible bug with song ids - check 4D98wFVp9mJKizx5lhaHzb  Vampire Weekend - Ottoman

# def id_linked_playable(id):
#     print(id)
#     resp = sp.tracks(tracks=[id], market=market)

#     playable = resp['tracks'][0]['is_playable']
#     print(f"Linked to: {resp['tracks'][0]['id']}")

#     print(f"Playable: {playable}")
#     return playable

# results = sp.current_user_saved_tracks(limit=50)

# for item in results['items']:
#     id = item['track']['id']
#     playable = market in item['track']['available_markets'] or id_linked_playable(id)
#     if not playable:
#         print(f"Found missing! {item['track']['artists'][0]['name']} - {item['track']['name']} [{item['track']['id']}]")

