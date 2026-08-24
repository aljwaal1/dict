from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

# patch_global_ai_v330.py historically expects the original _loadWords block.
# Normalize only that function to the expected baseline immediately before the
# v3.3 patch runs. The v3.3 patch then replaces it with the final merge-aware
# implementation. This is a one-time clean-source migration helper.
pattern = re.compile(
    r"  Future<void> _loadWords\(\) async \{.*?\n  \}\n\n  Future<void> persistWords\(\)",
    re.S,
)
expected = """  Future<void> _loadWords() async {
    final raw = prefs.getString('words_json') ?? await rootBundle.loadString('assets/data/words.json');
    final data = jsonDecode(raw) as Map<String, dynamic>;
    words = (data['words'] as List? ?? [])
        .map((e) => WordItem.fromJson(Map<String, dynamic>.from(e)))
        .where((w) => w.en.isNotEmpty && w.ar.isNotEmpty && grades.contains(w.grade))
        .toList(growable: true);
  }

  Future<void> persistWords()"""

m = pattern.search(s)
if not m:
    raise SystemExit('compat: _loadWords function boundary not found')
s = s[:m.start()] + expected + s[m.end():]
p.write_text(s, encoding='utf-8')
print('Normalized _loadWords for v3.3 clean materialization')
