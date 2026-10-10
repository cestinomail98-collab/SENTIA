$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("$env:USERPROFILE\Desktop\SENTIA.lnk")
$sc.TargetPath = "wscript.exe"
$sc.Arguments = "`"$dir\SENTIA.vbs`""
$sc.WorkingDirectory = $dir
$sc.IconLocation = "$dir\sentia.ico"
$sc.Description = "SENTIA - organismo dati: monitor di sistema vivente"
$sc.Save()
Write-Host "Icona SENTIA creata sul Desktop."
