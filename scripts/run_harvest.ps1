$root = "C:\Users\$env:USERNAME\LaptopHours"
Set-Location $root
& "$root\.venv\Scripts\Activate.ps1"
python -m app.harvester *>> "$root\data\harvest.log"
