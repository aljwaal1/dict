from pathlib import Path
import re

s=Path('lib/main.dart').read_text(encoding='utf-8')

required_words=['school','classroom','great','happy','beautiful','learn','teacher','difficult','morning']
stop_match=re.search(r"static const _stopWords = <String>\{(.*?)\n  \};",s,re.S)
proper_match=re.search(r"static const _knownProperNames = <String>\{(.*?)\n  \};",s,re.S)
if not stop_match or not proper_match:
    raise SystemExit('word filter sets not found')
stop=set(re.findall(r"'([^']+)'",stop_match.group(1)))
proper=set(re.findall(r"'([^']+)'",proper_match.group(1)))
for w in required_words:
    if w in stop or w in proper:
        raise SystemExit(f'educational word incorrectly excluded: {w}')
for w in ['and','with','from','unit','lesson','page']:
    if w not in stop:
        raise SystemExit(f'expected stop word missing: {w}')
for w in ['jordan','amman','ahmed']:
    if w not in proper:
        raise SystemExit(f'expected proper name/place missing: {w}')

required_source=[
    "for (var pi = 0; pi < document.pages.length; pi++)",
    "final pageText = await document.pages[pi].loadText();",
    "final text = pageText?.fullText ?? '';",
    "map.values.toList",
    "const Text('بطاقات سريعة')",
    "Text('${index + 1} من ${widget.words.length}'",
    "bool showMeaning = true;",
    "bool showExample = true;",
]
for needle in required_source:
    if needle not in s:
        raise SystemExit('missing functional invariant: '+needle)
if 'final pages = <String>[];' in s:
    raise SystemExit('old full-book PDF buffering returned')
if "const appVersion = '3.4.8';" not in s:
    raise SystemExit('unexpected Android version')

print('Android v3.4.8 functional regression checks passed')
