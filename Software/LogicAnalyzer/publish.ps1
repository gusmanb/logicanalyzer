param (
    [Parameter(Mandatory=$true)]
    [string]$packageName
)

# Ruta al archivo .csproj del proyecto que deseas publicar
$projectPath = ".\LogicAnalyzer\LogicAnalyzer.csproj"

# Leer la versión del framework desde el archivo .csproj
[xml]$csproj = Get-Content $projectPath
$targetFramework = $csproj.Project.PropertyGroup.TargetFramework

# Ruta a la carpeta de publicación
$publishDir = ".\LogicAnalyzer\bin\Release\$targetFramework\publish"

# Limpiar la carpeta de publicación
if (Test-Path $publishDir) {
    Remove-Item -Recurse -Force $publishDir
}

# Compilar el proyecto
dotnet build $projectPath -c Release

# Obtener todos los perfiles de publicación
$profiles = Get-ChildItem -Path . -Recurse -Filter "*.pubxml" | Select-Object -ExpandProperty FullName

# Publicar usando cada perfil
foreach ($profile in $profiles) {
    $profileName = [System.IO.Path]::GetFileNameWithoutExtension($profile)
    Write-Host "Publicando perfil: $profileName"
    dotnet publish $projectPath -c Release -p:PublishProfile=$profileName
}

# Crear la carpeta de paquetes si no existe
$packagesDir = "..\Packages"
if (-not (Test-Path $packagesDir)) {
    New-Item -ItemType Directory -Path $packagesDir
}

# Empaquetar los resultados
$publishSubDirs = Get-ChildItem -Path $publishDir -Directory
foreach ($subDir in $publishSubDirs) {
    $architecture = $subDir.Name
    $zipPath = "$packagesDir\$packageName-$architecture.zip"
    Write-Host "Empaquetando $subDir.FullName en $zipPath"

    # Eliminar el archivo ZIP si ya existe
    if (Test-Path $zipPath) {
        Remove-Item -Force $zipPath
    }

    # Excluir los paquetes de Windows
    if ($architecture -notmatch "win") {
        # Convertir las rutas a formato WSL
        $wslPath = wsl -e bash -c "wslpath -a '$($subDir.FullName)'"
        $wslZipPath = wsl -e bash -c "wslpath -a '$zipPath'"

        # Usar WSL para empaquetar y establecer el atributo de ejecutable
        wsl -e bash -c "cd $wslPath && chmod +x LogicAnalyzer && zip -r $wslZipPath ."
    } else {
        Compress-Archive -Path "$($subDir.FullName)\*" -DestinationPath $zipPath
    }
}