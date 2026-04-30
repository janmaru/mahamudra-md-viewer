#!/bin/bash
# Launcher for Friedrich - Document Reader in English (Bash)

echo "Launching Friedrich - Document Reader in ENGLISH..."
echo ""

./.venv/Scripts/python.exe md_reader.py --lang en

read -p "Press [Enter] to close..."
