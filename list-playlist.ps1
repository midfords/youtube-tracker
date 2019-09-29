
[CmdletBinding(PositionalBinding=$False)]
param(
    [string] $PlaylistId,
    [int] $Count = -1
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
    } while (($PlaylistItems.Length -lt $Count -or $Count -eq -1) -and $PageToken -ne $null)

    if ($Count -eq -1) {
        return $PlaylistItems
    }

    return $PlaylistItems[0..($Count-1)]
}

$Items = Get-PlaylistItems -PlaylistId $PlaylistId -Count $Count -GoogleApiKey $GoogleApiKey

Write-Host "Index`tVideo Id`tTitle"
Write-Host "-----`t--------`t-----"
for ($i = 1; $i -le $Items.Length; $i++) {
    $Item = $Items[$i-1]
    $Title = $Item.contentDetails.videoId
    $Id = $Item.snippet.title
    Write-Host "$i`: `t$Title `t$Id"
}
