from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

# Collapse duplicated bootstrap flag created by historical repeated patching.
s = re.sub(r"(?:  bool introDone = false;\n){2,}", "  bool introDone = false;\n", s)

# Collapse three identical consecutive smart-learning blocks to one.
smart_marker = "  int _editDistance(String a, String b) {"
smart_positions = [m.start() for m in re.finditer(re.escape(smart_marker), s)]
search_pos = s.find("  List<WordItem> smartSearch(String value) {")
smart_positions = [x for x in smart_positions if 0 <= x < search_pos]
if len(smart_positions) >= 3:
    a, b, c = smart_positions[:3]
    block_len = b - a
    if c - b != block_len:
        raise SystemExit('smart-learning duplicate blocks are not identical in size')
    first_block = s[a:b]
    second_block = s[b:c]
    third_end = c + block_len
    if first_block != second_block or s[c:third_end] != first_block:
        raise SystemExit('smart-learning duplicate blocks differ unexpectedly')
    s = s[:b] + s[third_end:]

# Collapse three identical consecutive onboarding class blocks to one.
onboard_marker = "class QamoosiAiOnboarding extends StatefulWidget {"
positions = [m.start() for m in re.finditer(re.escape(onboard_marker), s)]
if len(positions) >= 3:
    a, b, c = positions[:3]
    block_len = b - a
    if c - b != block_len:
        raise SystemExit('onboarding duplicate blocks are not identical in size')
    first_block = s[a:b]
    second_block = s[b:c]
    third_end = c + block_len
    if first_block != second_block or s[c:third_end] != first_block:
        raise SystemExit('onboarding duplicate blocks differ unexpectedly')
    s = s[:b] + s[third_end:]

# Hard verification: only one definition of each must remain.
checks = {
    '_editDistance': s.count("  int _editDistance(String a, String b) {"),
    'smartStudyWords': s.count("  List<WordItem> get smartStudyWords {"),
    'introDone': s.count("  bool introDone = false;"),
    'QamoosiAiOnboarding': s.count("class QamoosiAiOnboarding extends StatefulWidget {"),
}
for name, count in checks.items():
    print(name, count)
    if count != 1:
        raise SystemExit(f'{name}: expected exactly 1 definition, found {count}')

p.write_text(s, encoding='utf-8')
print('Clean-source duplicate removal complete')
