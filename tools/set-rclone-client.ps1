# Puts the owner's own Google OAuth client into the rclone remote "gdrive",
# then re-runs the browser login. Secrets are typed by the owner here and
# never pass through chat or files.
$rclone = 'C:\Users\Вадим\AppData\Local\Microsoft\WinGet\Packages\Rclone.Rclone_Microsoft.Winget.Source_8wekyb3d8bbwe\rclone-v1.76.0-windows-amd64\rclone.exe'

$id = Read-Host 'Вставь Client ID и нажми Enter'
$secretSecure = Read-Host 'Вставь Client secret и нажми Enter' -AsSecureString
$secret = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretSecure))

& $rclone config update gdrive client_id $id client_secret $secret --non-interactive | Out-Null
$secret = $null

Write-Host 'Сейчас откроется браузер: войди в тот же Google и нажми «Разрешить».'
& $rclone config reconnect gdrive: --auto-confirm

Write-Host 'Проверка: список папки content-studio на Диске'
& $rclone lsd gdrive:content-studio
if ($LASTEXITCODE -eq 0) { Write-Host 'ГОТОВО. Диск подключён через твой ключ.' } else { Write-Host 'Не получилось. Напиши Claude «rclone не подключился».' }
