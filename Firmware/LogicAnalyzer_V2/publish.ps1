param (
    [string]$packageName = "LogicAnalyzer"
)

# Define board types and turbo mode options
$boardTypes = @("BOARD_PICO", "BOARD_PICO_W", "BOARD_PICO_W_WIFI", "BOARD_ZERO", "BOARD_PICO_2")
$turboModes = @("0", "1")

# Path to the build settings file
$buildSettingsFile = "LogicAnalyzer_Build_Settings.cmake"

# Paths from settings.json
$cmakePath = "${env:USERPROFILE}/.pico-sdk/cmake/v3.28.6/bin/cmake"
$ninjaPath = "${env:USERPROFILE}/.pico-sdk/ninja/v1.12.1/ninja"
$picoSdkPath = "${env:USERPROFILE}/.pico-sdk/sdk/2.0.0"
$picoToolchainPath = "${env:USERPROFILE}/.pico-sdk/toolchain/13_2_Rel1"

# Function to update the build settings file
function Update-BuildSettings {
    param (
        [string]$boardType,
        [string]$turboMode
    )
    $content = Get-Content $buildSettingsFile
    $content = $content -replace '(set\(BOARD_TYPE ".*"\))', "set(BOARD_TYPE `"$boardType`")"
    $content = $content -replace '(set\(TURBO_MODE .*\))', "set(TURBO_MODE $turboMode)"
    Set-Content $buildSettingsFile $content
}

# Get the number of processors
$processorCount = [Environment]::ProcessorCount

# Create the publish directory if it doesn't exist
$publishDir = ".\publish"
if (-Not (Test-Path -Path $publishDir)) {
    New-Item -ItemType Directory -Path $publishDir
} else {
    # Clear the publish directory
    Remove-Item -Recurse -Force "$publishDir\*"
}

# Loop through each board type and turbo mode combination
foreach ($boardType in $boardTypes) {
    foreach ($turboMode in $turboModes) {
        # Skip turbo mode for BOARD_PICO_W variants
        if ($turboMode -eq "1" -and ($boardType -eq "BOARD_PICO_W" -or $boardType -eq "BOARD_PICO_W_WIFI")) {
            continue
        }

        # Update the build settings file
        Update-BuildSettings -boardType $boardType -turboMode $turboMode

        # Clean the build directory
        Remove-Item -Recurse -Force "build"
        New-Item -ItemType Directory -Path "build"
        Set-Location -Path "build"

        # Set environment variables
        $env:PICO_SDK_PATH = $picoSdkPath
        $env:PICO_TOOLCHAIN_PATH = $picoToolchainPath
        $env:Path = "${env:USERPROFILE}/.pico-sdk/toolchain/13_2_Rel1/bin;${env:USERPROFILE}/.pico-sdk/picotool/2.0.0/picotool;${env:USERPROFILE}/.pico-sdk/cmake/v3.28.6/bin;${env:USERPROFILE}/.pico-sdk/ninja/v1.12.1;${env:Path}"

        # Run the CMake configuration command
        & $cmakePath -G "Ninja" ..

        # Run the CMake build command
        & $cmakePath --build . --config Release -- -j $processorCount

        # Check if the .uf2 file exists before moving it
        $uf2File = "LogicAnalyzer.uf2"
        if (Test-Path -Path $uf2File) {
            # Determine the final binary name
            if ($turboMode -eq "1") {
                $binaryName = "${packageName}_${boardType}_Turbo.uf2"
            } else {
                $binaryName = "${packageName}_${boardType}.uf2"
            }

            # Move the generated .uf2 file
            Move-Item -Path $uf2File -Destination "..\$publishDir\$binaryName"
        } else {
            Write-Host "Error: $uf2File not found for $boardType with Turbo $turboMode"
        }

        # Return to the root directory
        Set-Location -Path ".."
    }
}

# Compress the .uf2 files and delete the originals
Get-ChildItem -Path $publishDir -Filter *.uf2 | ForEach-Object {
    $zipFileName = "$($_.BaseName).zip"
    Compress-Archive -Path $_.FullName -DestinationPath "$publishDir\$zipFileName"
    Remove-Item -Path $_.FullName
}