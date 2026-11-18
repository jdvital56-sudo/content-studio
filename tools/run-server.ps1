# Keeps the Content Studio wall alive: starts the server and restarts it
# 3 s after any exit. Started hidden at Windows logon by the scheduled task
# "ContentStudio" (see docs). Only one copy: exits if the port is taken.
$log = 'C:\src\content-studio\data-server.log'
while ($true) {
    $busy = Get-NetTCPConnection -LocalPort 8791 -State Listen -ErrorAction SilentlyContinue
    if (-not $busy) {
        & 'C:\Program Files\nodejs\node.exe' 'C:\src\content-studio\server\server.mjs' *>> $log
    }
    Start-Sleep -Seconds 3
}
