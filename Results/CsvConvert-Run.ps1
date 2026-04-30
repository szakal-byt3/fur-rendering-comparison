param (
    [Parameter(Mandatory=$true)]
    [string]$Path,

    [Parameter(Mandatory=$true)]
    [int]$Count
)

$exe = "C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\DotNET\CsvTools\CsvConvert.exe"

for ($i = 1; $i -le $Count; $i++) {
    $inputFile  = Join-Path $Path "Raw\Run$i.csv"
    $outputFile = Join-Path $Path "Cleaned\Run$i.csv"

    Write-Host "Converting Run$i..."

    & $exe -outFormat csv -in $inputFile -o $outputFile
}
