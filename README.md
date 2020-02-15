# YouTube Tracker
This script is used to track YouTube playlists. The script will determine and output playlist items that have been added, removed or renamed. It can track public or private playlists, and be configured to track multiple playlists at once. I've also included an additional script that will read in a playlist file and print its contents to the terminal.

There are several tests included for this project, you can run them with the following command:

`python3 ~/youtube-midfords/test/youtube.test.py`

## Usage

```
usage: youtube.py [-h] [-r] [-s] [-v] [-t]
Flags to change the running behavior of the youtube diff script.
optional arguments:
  -h, --help     show this help message and exit
  -r, --reauth   force the script to reauthenticate.
  -s, --showall  include items that are known to be renamed.
  -v, --verbose  output all verbose messages.
  -t, --test     read params from config_test.ini.
```


```
usage: ipl_print.py [-h] [-p PLAYLISTS [PLAYLISTS ...]] [-m] [-l]
Arguments to specify playlist ids to print.
optional arguments:
  -h, --help            show this help message and exit
  -p PLAYLISTS [PLAYLISTS ...], --playlists PLAYLISTS [PLAYLISTS ...]
                        list of playlist ids to print.
  -m, --missing_only    list only missing items.
  -l, --list            list of available playlists.
```

## Installation and Setup

This script requires access to the YouTube Data API v3, as well as registered Oauth2
credentials. This is to allow the script access to both the public and private playlist information on YouTube.

This script has dependencies on python3.7 and the following additional modules:
- requests
- progressbar2
- colorama
- oauth2client

You can clone this repository using git:

`git clone https://github.com/midfords/youtube-tracker.git youtube-midfords && cd youtube-midfords`

### Get an API key

These steps explain how to obtain your own Google API key.

1. Go to the Google developer's site.
2. Setup an account and create a new API key.
3. Key configuration
  * Application restrictions: None
  * API restrictions: Restrict key
  * Selected APIs: Youtube Data API v3

### Set up an Oauth2 project

These steps explain how to allow the script access to private YouTube playlists.

1. Go to the Google developer's site.
2. Setup a new Oauth2 project.
3. Download the credentials file and store it in the same directory that the secret_path config.ini property points to.

*Note: You do not need to verify the project to use Google Oauth2. Just ignore the unverified project warning.

![Alt](/images/screenshot-auth.png "Screenshot")

### Configuration

Create a config.ini file in the same directory as the script. Fill in the necessary values using your own authentication credentials. See the /config/config_template.ini for a template configuration file.

Template config.ini file:

```
[keys]
api = # YouTube Data API v3 key

[params]
playlists = [
  "",
  ""
] # List of playlist ids, separated by commas
path = # Path to folder where .ipl files will be stored
secret_path = # Path to folder where credentials.storage will be stored
```

Sample config.ini file:

```
[keys]
api = abcdef12345

[params]
playlists = [
  "PLUtTDeNt3L-43VWr1KYEEj7HcPi_ipBkZ",
  "PLUtTDeNt3L-6_C-Lf0YMjTCwqaNQZ6ueQ"
]
path = ~/youtube-midfords/diff/
secret_path = ~/youtube-midfords/auth/
```

Add or remove playlists in this file to change tracked items.

### Aliases

In your rc file (.bashrc, .zshrc, etc.) add this alias to run the YouTube tracker:

`alias run_youtube='python3 ~/youtube-midfords/src/youtube.py'`

Add this alias to run the ipl print util:

`alias print_youtube='python3 ~/youtube-midfords/src/ipl_print.py'`

Now you can run the scripts with `run_youtube` and `print_youtube` commands.

### Screenshots

![Alt](/images/screenshot-diff.png "Screenshot")
![Alt](/images/screenshot-print.png "Screenshot")

