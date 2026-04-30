#!/usr/bin/env python3
"""Test markdown parsing for edge cases and problematic patterns."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import markdown

test_patterns = [
    ('Bold', '**bold text**'),
    ('Italic', '*italic text*'),
    ('Headers', '# H1\n## H2\n### H3'),
    ('Lists', '- item 1\n- item 2\n  - nested'),
    ('Code inline', 'Use `code` like this'),
    ('Code block', '```python\ncode\n```'),
    ('Links', '[text](url)'),
    ('Images', '![alt](url)'),
    ('Blockquote', '> quoted text'),
    ('HR', '---'),
    ('Table', '| A | B |\n|---|---|\n| 1 | 2 |'),
    ('Strikethrough', '~~strike~~'),
    ('XML tag opening', '<tag>content</tag>'),
    ('HTML comments', '<!-- comment -->'),
    ('Inline HTML', '<span>inline</span>'),
    ('Escaped chars', r'\\escaped \* chars'),
    ('Blockquote note', '> Note: this is a note'),
    ('Inline code with <', '`<tag>here</tag>`'),
]

print('MARKDOWN PARSING TEST (using markdown library)')
print('=' * 70)
print()

for name, md_text in test_patterns:
    try:
        result = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
        status = '✓'
        print(f'{status} {name:<30} - OK')
    except Exception as e:
        status = '✗'
        print(f'{status} {name:<30} - ERROR: {str(e)[:40]}')

print()
print('=' * 70)
print('SCANNING MARKDOWN FILES:')
print()

md_files = sorted(list(Path('.').rglob('*.md')))

errors = []
for md_file in md_files[:15]:
    try:
        content = md_file.read_text('utf-8')
        result = markdown.markdown(content, extensions=["tables", "fenced_code"])
        line_count = len(content.split('\n'))
        print(f'✓ {str(md_file):<45} - {line_count:>3} lines')
    except Exception as e:
        print(f'✗ {str(md_file):<45}')
        print(f'  ERROR: {str(e)[:70]}')
        errors.append((str(md_file), str(e)))

if errors:
    print()
    print('=' * 70)
    print('DETAILED ERROR REPORT:')
    print()
    for filepath, error in errors:
        print(f'FILE: {filepath}')
        print(f'ERROR: {error}')
        print()

print('=' * 70)
print(f'[DONE] Tested {len(md_files)} markdown files. Errors: {len(errors)}')
