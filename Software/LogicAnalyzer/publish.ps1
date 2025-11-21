param (
    [Parameter(Mandatory=$true)]
    [string]$packageVersion
)

# Nombres de archivos a publicar
$projectNames = @("LogicAnalyzer", "TerminalCapture")
$mergedName = "all-in-one_$packageVersion"

# Empaquetar directorios en ZIP
function Zip-Directory {
    param(
        [Parameter(Mandatory=$true)]
        [string]$sourceDir,

        [Parameter(Mandatory=$true)]
        [string]$zipPath,

        [Parameter(Mandatory=$true)]
        [string]$architecture,

        [Parameter(Mandatory=$false)]
        $executables
    )

    # Eliminar el archivo ZIP si ya existe
    if (Test-Path $zipPath) {
        Remove-Item -Force $zipPath
    }

    # Excluir los paquetes de Windows
    if ($architecture -notmatch "win") {
        $chmodCmd = if ($executables) { "chmod +x $executables" } else { "true" }

        if ($IsWindows) {
            # Convertir las rutas a formato WSL
            $wslPath = wsl -e bash -c "wslpath -a '$sourceDir'"
            $wslZipPath = wsl -e bash -c "wslpath -a '$zipPath'"

            # Usar WSL para empaquetar y establecer el atributo de ejecutable
            wsl -e bash -c "cd $wslPath && $chmodCmd && zip -rq $wslZipPath ."
        } else {
            # Para Linux y macOS
            $zipPathFull = [System.IO.Path]::GetFullPath($zipPath)
            bash -c "cd '$sourceDir' && $chmodCmd && zip -rq '$zipPathFull' ."
        }
    } else {
        Compress-Archive -Path "$sourceDir/*" -DestinationPath $zipPath
    }
}

# Crear la carpeta de paquetes si no existe
$packagesDir = "../Packages"
if (-not (Test-Path $packagesDir)) {
    New-Item -ItemType Directory -Path $packagesDir
}

# Limpia las subcarpetas carpeta de paquetes
Get-ChildItem -Path $packagesDir -Directory | Remove-Item -Recurse -Force

# Crea la carpeta de mezcla si no existe
$mergedDir = "../Merged"
if (-not (Test-Path $mergedDir)) {
    New-Item -ItemType Directory -Path $mergedDir
}

# Limpia la carpeta de mezcla
Get-ChildItem -Path $mergedDir -Directory | Remove-Item -Recurse -Force

foreach($projectName in $projectNames)
{
    # Publicar cada proyecto
    Write-Host "Publicando proyecto: $projectName"

    # Nombre del paquete
    $packageName = $projectName.ToLower() + "_" + $packageVersion

    # Ruta al archivo .csproj del proyecto que deseas publicar
    $projectPath = "./$projectName/$projectName.csproj"

    # Leer la versión del framework desde el archivo .csproj
    [xml]$csproj = Get-Content $projectPath
    $targetFramework = $csproj.Project.PropertyGroup.TargetFramework

    # Ruta a la carpeta de publicación
    $publishDir = "./$projectName/bin/Release/$targetFramework/publish"

    # Limpiar la carpeta de publicación
    if (Test-Path $publishDir) {
        Remove-Item -Recurse -Force $publishDir
    }

    # Compilar el proyecto
    dotnet build $projectPath -c Release

    # Obtener todos los perfiles de publicación
    $profiles = Get-ChildItem -Path "./$projectName/" -Recurse -Filter "*.pubxml" | Select-Object -ExpandProperty FullName

    # Publicar usando cada perfil
    foreach ($profile in $profiles) {
        $profileName = [System.IO.Path]::GetFileNameWithoutExtension($profile)
        Write-Host "Publicando perfil: $profileName"
        dotnet publish $projectPath -c Release -p:PublishProfile=$profileName
    }

    # Empaquetar los resultados
    $publishSubDirs = Get-ChildItem -Path $publishDir -Directory
    foreach ($subDir in $publishSubDirs) {
        $architecture = $subDir.Name
        $zipPath = "$packagesDir/$packageName-$architecture.zip"

        Write-Host "Copia de $subDir a $mergedDir/$architecture"

        # Copiar los archivos a la carpeta de mezcla
        Copy-Item -Recurse -Force $subDir.FullName $mergedDir

        Write-Host "Empaquetando $subDir en $zipPath"

        Zip-Directory -sourceDir $subDir.FullName -zipPath $zipPath -architecture $architecture -executables $projectName
    }

}

# Empaquetar los resultados en un solo archivo por arquitectura
$mergedSubDirs = Get-ChildItem -Path $mergedDir -Directory
foreach ($subDir in $mergedSubDirs) {
    $architecture = $subDir.Name
    $zipPath = "$packagesDir/$mergedName-$architecture.zip"

    Write-Host "Empaquetando $subDir en $zipPath"

    Zip-Directory -sourceDir $subDir.FullName -zipPath $zipPath -architecture $architecture -executables $projectNames

    if ($architecture -like "osx*") {
        # Empaquetar app de macOS
        $parentDir = Join-Path $mergedDir "LogicAnalyzer-$architecture.app"
        $appDir = Join-Path $parentDir "LogicAnalyzer.app"
        $contentsDir = Join-Path $appDir "Contents"
        $macOSDir = Join-Path $contentsDir "MacOS"
        $resourcesDir = Join-Path $contentsDir "Resources"
        $zipPath = "$packagesDir/app-LogicAnalyzer_$packageVersion-$architecture.app.zip"

        New-Item -ItemType Directory -Force -Path $macOSDir | Out-Null
        New-Item -ItemType Directory -Force -Path $resourcesDir | Out-Null

        Get-ChildItem $subDir.FullName | Copy-Item -Recurse -Force -Destination $macOSDir
        Copy-Item "Artwork/Ico40.icns" $resourcesDir

        $plistPath = Join-Path $contentsDir "Info.plist"

        $plist = @"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>LogicAnalyzer</string>

    <key>CFBundleIdentifier</key>
    <string>com.gusmanb.LogicAnalyzer</string>

    <key>CFBundleVersion</key>
    <string>$packageVersion</string>

    <key>CFBundleShortVersionString</key>
    <string>$packageVersion</string>

    <key>CFBundleExecutable</key>
    <string>LogicAnalyzer</string>

    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>

    <key>CFBundlePackageType</key>
    <string>APPL</string>

    <key>CFBundleIconFile</key>
    <string>Ico40.icns</string>
</dict>
</plist>
"@
        Set-Content -Path $plistPath -Value $plist -Encoding UTF8
        Zip-Directory -sourceDir $parentDir -zipPath $zipPath -architecture $architecture
    }
}

# Limpiar carpeta de mezcla
Get-ChildItem -Path $mergedDir -Directory | Remove-Item -Recurse -Force