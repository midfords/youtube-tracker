
[CmdletBinding(PositionalBinding=$False)]
param(
    [string] $PlaylistId,
    [Parameter(Mandatory=$true)]
    [int] $Count
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
    } while ($PlaylistItems.Length -lt $Count -and $PageToken -ne $null)

    return $PlaylistItems[0..($Count-1)]
}

function Generate-Filename {
    param ([string]$Name)

    $Forbidden = '<','>',':','"','/','\','|','?','*'
    foreach ($Char in $Forbidden) {
        $Name = $Name.Replace($Char, "_")
    }
    $Name += ".mp3"

    return $Name
}

function Generate-SafeFilename {
    param ([string]$Name)

    $Forbidden = '<','>',':','"','/','\','|','?','*',' ','(',')','[',']','-'
    foreach ($Char in $Forbidden) {
        $Name = $Name.Replace($Char, "")
    }
    $Name += ".mp3"

    return $Name
}

Write-Host "Gathering $Count items from playlist. (Id: $PlaylistId)"

$Items = Get-PlaylistItems -PlaylistId $PlaylistId -Count $Count -GoogleApiKey $GoogleApiKey

foreach($Item in $Items) {

    $VideoId = $Item.contentDetails.videoId
    $Url = "https://www.convertmp3.io/fetch/?video=https://www.youtube.com/watch?v=$VideoId"
    $Title = Generate-Filename -Name $Item.snippet.title
    $SafeTitle = Generate-SafeFilename -Name $Item.snippet.title

    Write-Host "Downloading `'$Title`'"

    Invoke-WebRequest -Uri $Url -OutFile "$SafeTitle"
}
