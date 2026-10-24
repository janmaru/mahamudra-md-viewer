#!/bin/bash
# Launcher per Friedrich - Document Reader in Italiano (Bash)

echo "Avvio Friedrich - Document Reader in ITALIANO..."
echo ""

# Windows (Git Bash) keeps the venv interpreter in Scripts/, Linux in bin/.
if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=./.venv/Scripts/python.exe; fi
"$PY" md_reader.py --lang it

read -p "Premi [Invio] per chiudere..."
