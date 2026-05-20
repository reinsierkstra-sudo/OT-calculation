$root = "C:\Users\$env:USERNAME\LaptopHours"
Set-Location $root
& "$root\.venv\Scripts\Activate.ps1"
Start-Process -WindowStyle Hidden python -ArgumentList "-m","app.server"
Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:5000"
