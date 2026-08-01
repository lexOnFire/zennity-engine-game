$gitDir = "C:\Users\User\.local\git"
if (-not (Test-Path $gitDir)) {
    New-Item -ItemType Directory -Force -Path $gitDir
}
$zipPath = Join-Path $gitDir "git.zip"
Write-Host "Baixando MinGit..."
Invoke-WebRequest -Uri "https://github.com/git-for-windows/git/releases/download/v2.45.2.windows.1/MinGit-2.45.2-64-bit.zip" -OutFile $zipPath
Write-Host "Extraindo arquivos do Git..."
Expand-Archive -Path $zipPath -DestinationPath $gitDir -Force
Remove-Item $zipPath -Force

$gitCmd = Join-Path $gitDir "cmd"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$gitCmd*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$gitCmd", "User")
}
$env:Path = "$gitCmd;" + $env:Path

Write-Host "Git instalado com sucesso!"
& "$gitCmd\git.exe" --version
