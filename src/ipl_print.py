import os
import csv
import argparse
import configparser
from colorama import Fore
from colorama import Style

parser = argparse.ArgumentParser(description='Arguments to specify playlist ids to print.')
parser.add_argument('-p', '--playlists', nargs='+', help='list of playlist ids to print.')
parser.add_argument('-m', '--missing_only', action='store_true', help='list only missing items.')
parser.add_argument('-l', '--list', action='store_true', help='list of available playlists.')
args = parser.parse_args()
playlists = args.playlists

LIST_AVAILABLE_FLAG = args.list
MISSING_ONLY_FLAG = args.missing_only
MISSING_FLAG = "!"

config = configparser.ConfigParser()
src_dir = os.path.dirname(__file__)
module_dir = os.path.join(src_dir, '..')
config_path = os.path.join(module_dir, 'config/config.ini')
config.read(config_path)

path = config.get('params', 'path')

def print_column_headers():
    p0 = " Missing   "
    l0 = "---------  "
    p1 = " Video Id    "
    l1 = "-----------  "
    p2 = " Title "
    l2 = "---------------------------"
    print(p0, p1, p2)
    print(l0, l1, l2)

def print_header_available(ids):
    print()
    print("Available playlists:")
    for [_, _, _, count, id, name] in ids:
        print(f"  {id} - {name} [{count}]")
    print()

def print_header(row):
    print()
    print(f" Version = {row[1]}")
    print(f" Id = {row[4]}")
    print(f" Title = {row[5]}")
    print(f" Count = {row[3]}")
    print()

def print_read_error(id):
    print(f"Could not read file '{id}.ipl' at '{path}'")

def print_item(id, title, missing=False):
    p0 = "           "
    if missing:
        p0 = f"{Style.RESET_ALL}{Style.BRIGHT}{Fore.RED}    !      {Style.RESET_ALL}"
    p1 = f"{Style.RESET_ALL}{id}  "
    p2 = f"{Style.RESET_ALL}{title}"
    print(p0, p1, p2)

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
    fpath = os.path.join(path, f"{playlist_id}.ipl")

    with open(fpath, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)
        items = [row for row in reader]

    return (header, items)

def main():
    if LIST_AVAILABLE_FLAG:
        file_names = [f.split('.')[0] for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith('.ipl')]
        file_headers = [read_playlist_file(id)[0] for id in file_names]
        print_header_available(file_headers)

    if playlists == None:
        return

    for playlist in playlists:
        try:
            (header, rows) = read_playlist_file(playlist)
        except:
            print_read_error(playlist)
            continue

        print_header(header)
        print_column_headers()

        for [flag, id, title] in rows:
            is_missing = flag == MISSING_FLAG
            if not MISSING_ONLY_FLAG or MISSING_ONLY_FLAG and is_missing:
                print_item(id, title, missing=is_missing)

        print()

if __name__ == "__main__":
    main()
