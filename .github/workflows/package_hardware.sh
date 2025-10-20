#!/bin/bash
set -e

# Create a directory to store the packages
mkdir -p release_assets

# Define the source directory for the electronics
ELECTRONICS_SOURCE_DIR="Electronics/LogicAnalyzer/LogicAnalyzerV2/designs/jitx-design/kicad/output"

# Package the hardware files from the electronics directory
zip -j release_assets/BOM_JLCPCB.zip "$ELECTRONICS_SOURCE_DIR/BOM_JLCPCB.csv"
zip -j release_assets/BOM_PCBWay.zip "$ELECTRONICS_SOURCE_DIR/BOM_PCBWay.xlsx"
zip -j release_assets/CPL.zip "$ELECTRONICS_SOURCE_DIR/CPL.csv"
cp "$ELECTRONICS_SOURCE_DIR/Gerber_Files.zip" release_assets/Gerber_Files.zip

# Package the enclosure files
zip -j release_assets/Enclosure.zip Enclosure/*
