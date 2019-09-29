
[CmdletBinding(PositionalBinding=$False)]
param(
    [string] $Directory = "$ENV:UserProfile\Downloads\",                # Directory to sort
    [string] $PlaylistName = "Playlist.m3u",                            # Name for generated playlist file
    [string] $MainLibraryName = "$ENV:UserProfile\Music\Library.m3u"    # Path to main library playlist (leave blank if none)
)

Set-Variable UNKNOWN_ARTIST -option Constant -value "Unknown Artist" # Unkown artist default
Set-Variable UNKNOWN_ALBUM -option Constant -value "Unknown Album"   # Unkown album default
Set-Variable UNKNOWN_TRACK -option Constant -value "00"              # Unknown tracks are labeled with this string
Set-Variable TRACK_SPACE -option Constant -value "0"                 # Track numbers 1-9 are spaced with this character
Set-Variable TRACK_DELIMITOR -option Constant -value " - "           # Separator for track and artist
Set-Variable EXTENSION -option Constant -value ".mp3"                # File extension to look for

$Shell = New-Object -ComObject "Shell.Application"
$ObjDir = $Shell.NameSpace($Directory)
$Files = Get-ChildItem $Directory | ?{$_.Extension -in $EXTENSION}

# Get / Create playlist files
if ($MainLibraryName -ne "") {
    $MainLibrary = Get-Item $MainLibraryName
}
if (-not (Test-Path -Path $PlaylistName)) {
    $Playlist = New-Item $PlaylistName -Type File
    "#EXTM3U" | Add-Content $Playlist
} else {
    $Playlist = Get-Item $PlaylistName
}

foreach($File in $Files) {
    $ObjFile = $ObjDir.parsename($File.Name)

    # Get and parse metadata
    $Filename = $ObjDir.GetDetailsOf($ObjFile, 0)                     #  0 - File name
    $Artist = $ObjDir.GetDetailsOf($ObjFile, 13)                      # 13 - Artist
    $Album = $ObjDir.GetDetailsOf($ObjFile, 14)                       # 14 - Album
    $Title = $ObjDir.GetDetailsOf($ObjFile, 21)                       # 21 - Title
    $Track = $ObjDir.GetDetailsOf($ObjFile, 26)                       # 26 - Track
    $Length = $ObjDir.GetDetailsOf($ObjFile, 27).Trim().Split(":")    # 27 - Length

    $ArtistPath = $Artist.Trim()
    $AlbumPath = $Album.Trim()
    $TitlePath = $Title.Trim()

    $Hours = [int] $Length[0]
    $Minutes = [int] $Length[1]
    $Seconds = [int] $Length[2]

    # Process metadata
    $Length = $Hours * 3600 + $Minutes * 60 + $Seconds

    if ($ArtistPath -eq "") {
        $ArtistPath = $UNKNOWN_ARTIST
    }
    if ($AlbumPath -eq "") {
        $AlbumPath = $UNKNOWN_ALBUM
    }
    if ($Track -le 9 -and $Track -ge 1) {
        $Track = $TRACK_SPACE + $Track
    }
    if ($Track -eq 0) {
        $Track = $UNKNOWN_TRACK
    }

    $Forbidden = '<','>',':','"','/','\','|','?','*'
    foreach ($Char in $Forbidden) {
        $TitlePath = $TitlePath.Replace($Char, "_")
        $ArtistPath = $ArtistPath.Replace($Char, "_")
        $AlbumPath = $AlbumPath.Replace($Char, "_")
    }

    # Create new directory
    $NewFilename = "$Track" + $TRACK_DELIMITOR + "$TitlePath" + $EXTENSION
    $NewFilepath = "$ArtistPath\$AlbumPath"

    if (-not (Test-Path -Path $NewFilepath)) {
        New-Item $NewFilepath -Type Directory
    }

    # Rename and move file to new directory
    Rename-Item -Path $File.FullName -NewName $NewFilename
    Move-Item -Path $NewFilename -Destination $NewFilepath

    # Cleanup string for playlist file and write lines to playlist(s)

    #
    # #EXTM3U
    # #EXTINF:123,Artist Name - Song Title
    # URI/Escaped/Relative/File/Path
    #

    $NewFilepath = [uri]::EscapeUriString("$ArtistPath/$AlbumPath/$NewFilename")

    "#EXTINF:$Length,$Artist - $Title" | Add-Content $Playlist
    $NewFilepath | Add-Content $Playlist

    if ($MainLibraryName -ne "") {
        "#EXTINF:$Length,$Artist - $Title" | Add-Content $MainLibrary
        $NewFilepath | Add-Content $MainLibrary
    }
}
