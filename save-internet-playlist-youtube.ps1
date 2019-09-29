
[CmdletBinding(PositionalBinding=$False)]
param(
    [string] $PlaylistId
)

function Read-GoogleApiKey {
    $KeyFile = Get-Item "$ENV:UserProfile\Documents\WindowsPowerShell\Scripts\vars\google-api-key.txt"
    $Line = Get-Content $KeyFile
    return $Line
}
$GoogleApiKey = Read-GoogleApiKey

function Read-PlaylistId {
    $File = Get-Item "$ENV:UserProfile\Documents\WindowsPowerShell\Scripts\vars\playlist-id.txt"
    $Line = Get-Content $File
    return $Line
}
if (-not $PlaylistId) {
    $PlaylistId = Read-PlaylistId
}

function Get-PlaylistInfo {
    param ([string]$PlaylistId, [string]$GoogleApiKey)

    $Method = "GET"
    $Url = "https://www.googleapis.com/youtube/v3/playlists"
    $Body = @{
        key = $GoogleApiKey
        part = "snippet"
        id = $PlaylistId
    }

    $Response = Invoke-RestMethod -Uri $Url -Method $Method -Body $Body
    return $Response.items[0]
}

function Generate-Filename {
    param ([string]$Name)

    $Forbidden = '<','>',':','"','/','\','|','?','*'
    foreach ($Char in $Forbidden) {
        $Name = $Name.Replace($Char, "_")
    }
    $Name += ".ipl"

    return $Name
}

function Safety-CsvString {
    param ([string]$String)

    $String = $String.Replace(",", "")

    return $String
}

function Get-PlaylistItems {
    param ([string]$PlaylistId, [int]$Count, [string]$GoogleApiKey)

    $PlaylistItems = @()

    do {
        $Method = "GET"
        $Url = "https://www.googleapis.com/youtube/v3/playlistItems"
        $Body = @{
            pageToken = $PageToken
            key = $GoogleApiKey
            part = "snippet,contentDetails"
            playlistId = $PlaylistId
            maxResults = 50
        }

        $Response = Invoke-RestMethod -Uri $Url -Method $Method -Body $Body
        $PageToken = $Response.nextPageToken
        $PlaylistItems += [System.Object[]] $Response.items
    } while (($PlaylistItems.Length -lt $Count -or $Count -eq -1) -and $PageToken -ne $null)

    if ($Count -eq -1) {
        return $PlaylistItems
    }

    return $PlaylistItems[0..($Count-1)]
}

$NumMissing = 0
$NumMissingDiff = 0
$NumLines = 0
$NewItems = 0

# Get Playlist info
Write-Host "Retrieving playlist info for $PlaylistId"
$Playlist = Get-PlaylistInfo -PlaylistId $PlaylistId -GoogleApiKey $GoogleApiKey
$PlaylistName = $Playlist.snippet.title
Write-Host "Retrieving $PlaylistName"
$PlaylistName = Generate-Filename -Name $PlaylistName
$PlaylistItems = Get-PlaylistItems -PlaylistId $PlaylistId -Count -1 -GoogleApiKey $GoogleApiKey
$PlaylistItems = [System.Collections.ArrayList]$PlaylistItems

$Length = $PlaylistItems.Count

# Get / Create playlist file
$PlaylistPath = "$ENV:UserProfile\Documents\WindowsPowerShell\Scripts\ipls\$PlaylistName"
if (-not (Test-Path -Path $PlaylistPath)) {
    $PlaylistFile = New-Item $PlaylistPath -Type File
} else {
    $PlaylistFile = Get-Item $PlaylistPath
}

Write-Host "Opening file: $PlaylistPath"
Write-Host "Reading from file."

$Lines = Get-Content $PlaylistFile
if ($Lines.Length -gt 0) {
    $Lines = $Lines[1..($Lines.Length - 1)]
    $NumLines = $Lines.Length -1
}

Write-Host "Processing lines."

# Generate Map of Video Ids
$Map = @{}
for ($i = 0; $i -lt $Lines.Length; $i ++) {

    $Line = $Lines[$i]
    $Tokens = $Line.Split(",")

    $Map.Add($Tokens[1], $i)
    if ($Tokens[0] -eq "!") {
        $NumMissing += 1
} }

for ($i = $PlaylistItems.Count - 1; $i -ge 0; $i --) {

    $Item = $PlaylistItems[$i]
    $Id = $Item.contentDetails.videoId

    if ($Map.ContainsKey($Id)) {
        $Map.Remove($Id)
        $PlaylistItems.RemoveAt($i)
} }

$Output = New-Object System.Collections.ArrayList($null)

foreach ($Item in $PlaylistItems) {

    $Id = $Item.contentDetails.videoId
    $Name = $Item.snippet.title

    [void]$Output.Add(",$Id,$Name")
    $NewItems += 1
}

Write-Host "Writing to file."

for ($i = 0; $i -lt $Lines.Length; $i ++) {

    $Line = $Lines[$i]
    $Tokens = $Line.Split(",")

    if ($Map.ContainsKey($Tokens[1])) {
        # Item was removed from playlist
        $Tokens[0] = "!"
        $NumMissingDiff += 1
    }

    [void]$Output.Add([string]::Join(",", $Tokens))
}

Clear-Content $PlaylistFile
"#IPL,1.0,YOUTUBE,$Length,$PlaylistId" | Add-Content $PlaylistFile
$Output | Add-Content $PlaylistFile

Write-Host "Finished. `n`nResults:"
Write-Host "------------------"
Write-Host "Missing: $NumMissing > $NumMissingDiff  ($($NumMissingDiff - $NumMissing) new)"
Write-Host "New Items: $NewItems"
