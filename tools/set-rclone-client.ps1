# Creates the rclone remote "gdrive" with the owner's own Google OAuth client.
# The id and secret are read from the JSON file that Google lets you download
# (client_secret_*.json in Downloads), so nothing is copy-pasted and nothing
# passes through chat or git. The JSON is deleted after use.
# Config lives in C:\src\rclone (NOT AppData): the desktop app and the real
# terminal see different AppData folders.
$rclone = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter rclone.exe |
    Select-Object -First 1 -ExpandProperty FullName
$dir = 'C:\src\rclone'
$conf = Join-Path $dir 'rclone.conf'
New-Item -ItemType Directory -Force $dir | Out-Null

$json = Get-ChildItem (Join-Path $env:USERPROFILE 'Downloads') -Filter 'client_secret*.json' |
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-2) } |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $json) {
    Write-Host 'Не нашёл файл client_secret...json в папке Загрузки. Скачай его в Google (кнопка Download JSON) и запусти снова.'
    exit 1
}
Write-Host "Нашёл файл: $($json.Name)"
$c = (Get-Content $json.FullName -Raw -Encoding utf8 | ConvertFrom-Json).installed
if (-not $c.client_id -or -not $c.client_secret) {
    Write-Host 'В файле нет client_id или client_secret. Нужен ключ типа Desktop app.'
    exit 1
}

Write-Host 'Сейчас откроется браузер: выбери свою почту и нажми «Разрешить».'
& $rclone config create gdrive drive client_id $c.client_id client_secret $c.client_secret scope drive.file --config $conf --no-output
Remove-Item $json.FullName -Force
Write-Host 'Файл с ключом из Загрузок удалён.'

Write-Host 'Проверка: создаю папку content-studio на Диске'
& $rclone mkdir gdrive:content-studio --config $conf
& $rclone lsd gdrive: --config $conf
if ($LASTEXITCODE -eq 0) { Write-Host 'ГОТОВО. Диск подключён через твой ключ.' } else { Write-Host 'Не получилось. Напиши Claude «rclone не подключился».' }
