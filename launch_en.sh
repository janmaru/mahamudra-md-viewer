#!/bin/bash
# Launcher for Friedrich - Document Reader in English (Bash)

echo "Launching Friedrich - Document Reader in ENGLISH..."
echo ""

# Windows (Git Bash) keeps the venv interpreter in Scripts/, Linux in bin/.
if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=./.venv/Scripts/python.exe; fi
"$PY" md_reader.py --lang en

read -p "Press [Enter] to close..."
