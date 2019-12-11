
[CmdletBinding(PositionalBinding=$False)]
param(
    [string] $ChannelId
)

function Read-GoogleApiKey {
    $KeyFile = Get-Item "$ENV:UserProfile\Documents\WindowsPowerShell\Scripts\vars\google-api-key.txt"
    $Line = Get-Content $KeyFile
    return $Line
}
$GoogleApiKey = Read-GoogleApiKey

function Read-ChannelId {
    $File = Get-Item "$ENV:UserProfile\Documents\WindowsPowerShell\Scripts\vars\channel-id.txt"
    $Line = Get-Content $File
    return $Line
}
if (-not $ChannelId) {
    $ChannelId = Read-ChannelId
}

function Get-Playlists {
    param ([string]$ChannelId, [string]$GoogleApiKey)

    $Playlists = @()

    do {
        $Method = "GET"
        $Url = "https://www.googleapis.com/youtube/v3/playlists"
        $Body = @{
            pageToken = $PageToken
            key = $GoogleApiKey
            part = "snippet,contentDetails"
            id = $PlaylistId
        }

        $Response = Invoke-RestMethod -Uri $Url -Method $Method -Body $Body
        $PageToken = $Response.nextPageToken
        $Playlists += [System.Object[]] $Response.items
    } while ($PageToken -ne $null)

    return $Playlists
}


# Get Playlist info
$Playlists = Get-Playlists -ChannelId $ChannelId -GoogleApiKey $GoogleApiKey

Write-Host "$($Playlists.Length) playlists in channel `'$ChannelId`'"

foreach ($Item in $Playlists) {

    $Id = $Item.contentDetails.id
    $Name = $Item.snippet.title

    Write-Host "$Id`t$Name"
}
