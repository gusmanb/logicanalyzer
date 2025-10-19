#!/bin/bash
set -e

# Create a directory to store the packages
mkdir -p hardware_packages

# Define the source directory
SOURCE_DIR="Electronics/LogicAnalyzer/LogicAnalyzerV2/designs/jitx-design/kicad/output"

# Package the hardware files
zip -j hardware_packages/BOM_JLCPCB.zip $SOURCE_DIR/BOM_JLCPCB.csv
zip -j hardware_packages/BOM_PCBWay.zip $SOURCE_DIR/BOM_PCBWay.xlsx
zip -j hardware_packages/CPL.zip $SOURCE_DIR/CPL.csv
cp $SOURCE_DIR/Gerber_Files.zip hardware_packages/Gerber_Files.zip
