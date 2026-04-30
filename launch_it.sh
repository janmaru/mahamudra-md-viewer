#!/bin/bash
# Launcher per Friedrich - Document Reader in Italiano (Bash)

echo "Avvio Friedrich - Document Reader in ITALIANO..."
echo ""

./.venv/Scripts/python.exe md_reader.py --lang it

read -p "Premi [Invio] per chiudere..."
