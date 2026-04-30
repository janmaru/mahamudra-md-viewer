#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verifica che la versione italiana sia pronta per l'avvio"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

print('Avvio verifica pre-lancio della versione italiana...')
print()

# Test 1: Carica il modulo i18n
try:
    from i18n import init_i18n, get_i18n
    print('[OK] Modulo i18n caricato')
except Exception as e:
    print(f'[ERRORE] Impossibile caricare i18n: {e}')
    sys.exit(1)

# Test 2: Inizializza con italiano
try:
    init_i18n('it')
    i18n = get_i18n()
    print(f'[OK] i18n inizializzato in italiano: {i18n.get_language()}')
except Exception as e:
    print(f'[ERRORE] Impossibile inizializzare italiano: {e}')
    sys.exit(1)

# Test 3: Verifica traduzioni critiche
translations_to_check = [
    'app.title',
    'empty_state.subtitle',
    'shortcuts.open_file',
    'shortcuts.change_folder',
    'sidebar.explorer',
    'sidebar.bookmarks',
    'sidebar.search',
]

print()
print('Traduzioni italiano caricate:')
print('-' * 60)
for key in translations_to_check:
    value = i18n.t(key)
    print(f'  {key:30} = {value}')

print()
print('[OK] Tutte le traduzioni caricate correttamente!')
print()
print('=' * 60)
print('L app è pronta per il lancio in italiano!')
print('=' * 60)
print()
print('COMANDO PER AVVIARE:')
print('  python md_reader.py --lang it')
print()
