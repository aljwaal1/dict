from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

# One-time compatibility normalizer for historical text-based v3.3 patch.
# It restores only the small source blocks that patch_global_ai_v330.py expects,
# then that patch writes the final modern implementations.

load_pattern = re.compile(
    r"  Future<void> _loadWords\(\) async \{.*?\n  \}\n\n  Future<void> persistWords\(\)",
    re.S,
)
load_expected = """  Future<void> _loadWords() async {
    final raw = prefs.getString('words_json') ?? await rootBundle.loadString('assets/data/words.json');
    final data = jsonDecode(raw) as Map<String, dynamic>;
    words = (data['words'] as List? ?? [])
        .map((e) => WordItem.fromJson(Map<String, dynamic>.from(e)))
        .where((w) => w.en.isNotEmpty && w.ar.isNotEmpty && grades.contains(w.grade))
        .toList(growable: true);
  }

  Future<void> persistWords()"""
m = load_pattern.search(s)
if not m:
    raise SystemExit('compat: _loadWords function boundary not found')
s = s[:m.start()] + load_expected + s[m.end():]

search_pattern = re.compile(
    r"  List<WordItem> smartSearch\(String value\) \{.*?\n  \}\n  int masteredGrade\(String g\)",
    re.S,
)
search_expected = """  List<WordItem> smartSearch(String value) {
    final q = value.trim().toLowerCase();
    if (q.isEmpty) return const [];
    int rank(WordItem w) {
      final en = w.en.toLowerCase();
      final ar = w.ar.toLowerCase();
      final exEn = w.exampleEn.toLowerCase();
      final exAr = w.exampleAr.toLowerCase();
      if (en == q || ar == q) return 0;
      if (en.startsWith(q) || ar.startsWith(q)) return 1;
      if (en.contains(q) || ar.contains(q)) return 2;
      if (exEn.contains(q) || exAr.contains(q)) return 3;
      return 99;
    }
    final result = words.where((w) => rank(w) < 99).toList(growable: false);
    result.sort((a, b) {
      final r = rank(a).compareTo(rank(b));
      if (r != 0) return r;
      return a.en.toLowerCase().compareTo(b.en.toLowerCase());
    });
    return result;
  }
  int masteredGrade(String g)"""
m = search_pattern.search(s)
if not m:
    raise SystemExit('compat: smartSearch function boundary not found')
s = s[:m.start()] + search_expected + s[m.end():]

p.write_text(s, encoding='utf-8')
print('Normalized _loadWords and smartSearch for v3.3 clean materialization')
