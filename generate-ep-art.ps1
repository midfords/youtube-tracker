
param (
    [string] $TemplateFile = "$ENV:UserProfile\Pictures\EP_Template.png"
    [Parameter(Mandatory=$true)]
    [string] $AlbumArtFile,
    [Parameter(Mandatory=$true)]
    [string] $OutputFile
)

function Resize-Image {
    param([System.Drawing.Image] $Image, [int] $Height)

    Add-Type -AssemblyName System.Drawing     # Add System.Drawing assembly

    $Width = $Image.Width * $Height / $Image.Height
    Write-Host $Image.Height
    Write-Host $Image.Width
    Write-Host $Height
    Write-Host $Width

    # Create empty canvas for the new image
    $Canvas = New-Object System.Drawing.Bitmap($Width, $Height)

    # Draw new image on the empty canvas
    $Graph = [System.Drawing.Graphics]::FromImage($Canvas)
    $Graph.DrawImage($Image, 0, 0, $Width, $Height)

    return $Canvas
}

function Is-PointInCircle {
    param([int] $OriginX, [int] $OriginY, [int] $Radius, [int] $PointX, [int] $PointY)

    $a = $OriginX - $PointX
    $b = $OriginY - $PointY
    $c = [math]::sqrt($a * $a + $b * $b)

    return $c -lt $Radius
}

function Crop-ImageCircle {
    param([System.Drawing.Image] $Image, [int] $Radius)

    # Create empty canvas for the new image
    $Canvas = New-Object System.Drawing.Bitmap($Width, $Height)

    # Draw new image on the empty canvas
    $Graph = [System.Drawing.Graphics]::FromImage($Canvas)

    $OriginX = $Image.Width / 2
    $OriginY = $Image.Height / 2

    for ($i = 0; $i -lt $Image.Width; $i++) {
        for ($j = 0; $j -lt $Image.Height; $j++) {
            if (Is-PointInCircle -OriginX $OriginX -OriginY $OriginY -Radius $Radius -PointX $i -PointY $j) {
                $Graph.DrawPixel($Image, 0, 0, $Width, $Height)
    } } }

    return $Canvas
}

function Graph-Image {
    param([System.Drawing.Image] $BackgroundImage, [System.Drawing.Image]$ForegroundImage)

    # Create empty canvas for the new image
    $Canvas = New-Object System.Drawing.Bitmap($BackgroundImage.Width, $BackgroundImage.Height)

    # Draw new image on the empty canvas
    $GraphBackground = [System.Drawing.Graphics]::FromImage($Canvas)
    $GraphBackground.DrawImage($BackgroundImage, 0, 0, $BackgroundImage.Width, $BackgroundImage.Height)

    $GraphForeground = [System.Drawing.Graphics]::FromImage($Canvas)
    $GraphForeground.DrawImage($ForegroundImage, 0, 0, $ForegroundImage.Width, $ForegroundImage.Height)

    return $Canvas
}

$AlbumImage = [System.Drawing.Image]::FromFile((Get-Item $AlbumArtFile))
$TemplateImage = [System.Drawing.Image]::FromFile((Get-Item $TemplateFile))

$AlbumImage = Resize-Image -Image $AlbumImage -Height 935
$Radius = [math]::max($AlbumImage.Height, $AlbumImage.Width)
$AlbumImageCircle = Crop-ImageCircle -Image $AlbumImage -Radius $Radius

$Image = Graph-Image -BackgroundImage $TemplateImage -ForegroundImage $AlbumImageCircle
$Image.Save($OutputFile);

