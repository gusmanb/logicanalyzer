#!/bin/bash
set -e

# Create a directory to store the packages
mkdir -p hardware_packages

# Define the source directory for the electronics
ELECTRONICS_SOURCE_DIR="Electronics/LogicAnalyzer/LogicAnalyzerV2/designs/jitx-design/kicad/output"

# Package the hardware files from the electronics directory
zip -j hardware_packages/BOM_JLCPCB.zip "$ELECTRONICS_SOURCE_DIR/BOM_JLCPCB.csv"
zip -j hardware_packages/BOM_PCBWay.zip "$ELECTRONICS_SOURCE_DIR/BOM_PCBWay.xlsx"
zip -j hardware_packages/CPL.zip "$ELECTRONICS_SOURCE_DIR/CPL.csv"
cp "$ELECTRONICS_SOURCE_DIR/Gerber_Files.zip" hardware_packages/Gerber_Files.zip

# Package the enclosure files
zip -j hardware_packages/Enclosure.zip Enclosure/*
