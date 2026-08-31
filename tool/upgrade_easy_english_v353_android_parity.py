from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')


def repl(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'missing anchor: {label}')
    s = s.replace(old, new, 1)

repl("const appVersion = '3.4.8';", "const appVersion = '3.5.3';", 'app version')

repl(
"  Map<String, int> wrongCounts = {};\n  Map<String, int> lastIndexByGrade = {};",
"  Map<String, int> wrongCounts = {};\n  List<String> recentMistakes = [];\n  Map<String, int> lastIndexByGrade = {};",
'recent mistakes field')

repl(
"    wrongCounts = _readMap('$pkey.wrongCounts');\n    lastIndexByGrade = _readMap('$pkey.lastIndex');",
"    wrongCounts = _readMap('$pkey.wrongCounts');\n    recentMistakes = prefs.getStringList('$pkey.recentMistakes') ?? <String>[];\n    lastIndexByGrade = _readMap('$pkey.lastIndex');",
'load recent mistakes')

repl(
"      prefs.setString('$pkey.wrongCounts', jsonEncode(wrongCounts)),\n      prefs.setString('$pkey.lastIndex', jsonEncode(lastIndexByGrade)),",
"      prefs.setString('$pkey.wrongCounts', jsonEncode(wrongCounts)),\n      prefs.setStringList('$pkey.recentMistakes', recentMistakes),\n      prefs.setString('$pkey.lastIndex', jsonEncode(lastIndexByGrade)),",
'save recent mistakes')

repl(
"    } else {\n      difficult.add('${word.id}');\n      wrongCounts['${word.id}'] = (wrongCounts['${word.id}'] ?? 0) + 1;\n    }\n    await saveProgress();",
"    } else {\n      final id = '${word.id}';\n      difficult.add(id);\n      wrongCounts[id] = (wrongCounts[id] ?? 0) + 1;\n      recentMistakes.remove(id);\n      recentMistakes.insert(0, id);\n      if (recentMistakes.length > 40) recentMistakes = recentMistakes.take(40).toList(growable: true);\n    }\n    await saveProgress();",
'answer recent mistakes')

repl(
"  String unit = '';\n  int count = 20;\n\n  List<String> get units => widget.store.byGrade(grade).map((w) => w.unit.trim()).where((v) => v.isNotEmpty).toSet().toList()..sort();",
"  String unit = '';\n  String lesson = '';\n  int count = 20;\n\n  List<String> get units => widget.store.byGrade(grade).map((w) => w.unit.trim()).where((v) => v.isNotEmpty).toSet().toList()..sort();\n  List<String> get lessons => widget.store.byGrade(grade).where((w) => unit.isEmpty || w.unit == unit).map((w) => w.lesson.trim()).where((v) => v.isNotEmpty).toSet().toList()..sort();",
'lesson state')

repl(
"      case 'unit':\n        list = widget.store.byGrade(grade).where((w) => w.unit == unit).toList();\n        break;\n      case 'easy':",
"      case 'unit':\n        list = widget.store.byGrade(grade).where((w) => w.unit == unit).toList();\n        break;\n      case 'lesson':\n        list = widget.store.byGrade(grade).where((w) => (unit.isEmpty || w.unit == unit) && w.lesson == lesson).toList();\n        break;\n      case 'difficult':\n        list = widget.store.byGrade(grade).where((w) => widget.store.difficult.contains('${w.id}')).toList();\n        list.sort((a, b) => widget.store.difficultyScore(b).compareTo(widget.store.difficultyScore(a)));\n        break;\n      case 'mistakes':\n        final ids = widget.store.recentMistakes;\n        final byId = {for (final w in widget.store.byGrade(grade)) '${w.id}': w};\n        list = ids.map((id) => byId[id]).whereType<WordItem>().toList();\n        break;\n      case 'notmastered':\n        list = widget.store.byGrade(grade).where((w) => !widget.store.mastered.contains('${w.id}')).toList();\n        break;\n      case 'smartmix':\n        final pool = widget.store.byGrade(grade);\n        final errors = pool.where((w) => (widget.store.wrongCounts['${w.id}'] ?? 0) > 0).toList()..sort((a,b) => widget.store.difficultyScore(b).compareTo(widget.store.difficultyScore(a)));\n        final fresh = pool.where((w) => !widget.store.studied.contains('${w.id}')).toList()..shuffle();\n        final hard = pool.where((w) => widget.store.difficult.contains('${w.id}') && !errors.contains(w)).toList()..sort((a,b) => widget.store.difficultyScore(b).compareTo(widget.store.difficultyScore(a)));\n        final masteredPool = pool.where((w) => widget.store.mastered.contains('${w.id}')).toList()..shuffle();\n        final target = count > 0 ? count : pool.length;\n        final picked = <WordItem>[];\n        void addUnique(Iterable<WordItem> src, int n) { for (final w in src) { if (!picked.contains(w)) picked.add(w); if (picked.length >= n) break; } }\n        addUnique(errors, (target * .40).ceil());\n        addUnique(fresh, (target * .70).ceil());\n        addUnique(hard, (target * .90).ceil());\n        addUnique(masteredPool, target);\n        if (picked.length < target) addUnique(pool..shuffle(), target);\n        list = picked;\n        break;\n      case 'easy':",
'advanced quiz modes')

repl(
"    'unit': 'حسب الوحدة',\n    'easy': 'من الأسهل إلى الأصعب',",
"    'unit': 'حسب الوحدة',\n    'lesson': 'حسب الدرس',\n    'difficult': 'الكلمات الصعبة فقط',\n    'mistakes': 'أخطائي الأخيرة',\n    'notmastered': 'غير المتقنة فقط',\n    'smartmix': 'مختلط ذكي',\n    'easy': 'من الأسهل إلى الأصعب',",
'mode titles')

repl(
"    if (mode == 'unit' && unit.isEmpty) {\n      snack(context, 'اختر الوحدة أولاً');\n      return;\n    }",
"    if (mode == 'unit' && unit.isEmpty) {\n      snack(context, 'اختر الوحدة أولاً');\n      return;\n    }\n    if (mode == 'lesson' && lesson.isEmpty) {\n      snack(context, 'اختر الدرس أولاً');\n      return;\n    }",
'lesson validation')

repl(
"    final unitList = units;\n    if (unit.isNotEmpty && !unitList.contains(unit)) unit = '';",
"    final unitList = units;\n    final lessonList = lessons;\n    if (unit.isNotEmpty && !unitList.contains(unit)) unit = '';\n    if (lesson.isNotEmpty && !lessonList.contains(lesson)) lesson = '';",
'lesson list build')

repl(
"          onChanged: (v) => setState(() { grade = v ?? grade; unit = ''; }),",
"          onChanged: (v) => setState(() { grade = v ?? grade; unit = ''; lesson = ''; }),",
'grade reset')

repl(
"            DropdownMenuItem(value: 'unit', child: Text('حسب الوحدة')),\n            DropdownMenuItem(value: 'easy', child: Text('حسب السهولة')),",
"            DropdownMenuItem(value: 'unit', child: Text('حسب الوحدة')),\n            DropdownMenuItem(value: 'lesson', child: Text('حسب الدرس')),\n            DropdownMenuItem(value: 'difficult', child: Text('الكلمات الصعبة فقط')),\n            DropdownMenuItem(value: 'mistakes', child: Text('أخطائي الأخيرة')),\n            DropdownMenuItem(value: 'notmastered', child: Text('غير المتقنة فقط')),\n            DropdownMenuItem(value: 'smartmix', child: Text('مختلط ذكي')),\n            DropdownMenuItem(value: 'easy', child: Text('حسب السهولة')),",
'quiz dropdown modes')

repl(
"          onChanged: (v) => setState(() { mode = v ?? mode; unit = ''; }),",
"          onChanged: (v) => setState(() { mode = v ?? mode; unit = ''; lesson = ''; }),",
'mode reset')

repl(
"        if (mode == 'unit') ...[\n          const SizedBox(height: 10),",
"        if (mode == 'unit' || mode == 'lesson') ...[\n          const SizedBox(height: 10),",
'unit selector visibility')

repl(
"            onChanged: (v) => setState(() => unit = v ?? ''),\n            decoration: const InputDecoration(labelText: 'الوحدة'),\n          ),\n        ],\n        const SizedBox(height: 10),",
"            onChanged: (v) => setState(() { unit = v ?? ''; lesson = ''; }),\n            decoration: const InputDecoration(labelText: 'الوحدة'),\n          ),\n        ],\n        if (mode == 'lesson') ...[\n          const SizedBox(height: 10),\n          DropdownButtonFormField<String>(\n            value: lesson.isEmpty ? null : lesson,\n            items: lessonList.map((l) => DropdownMenuItem(value: l, child: Text(l))).toList(),\n            onChanged: (v) => setState(() => lesson = v ?? ''),\n            decoration: const InputDecoration(labelText: 'الدرس'),\n          ),\n        ],\n        const SizedBox(height: 10),",
'lesson selector')

repl(
"      const SizedBox(height: 16),\n      FilledButton.icon(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.done_all_rounded), label: const Text('إنهاء الاختبار')),",
"      const SizedBox(height: 16),\n      if (wrong.isNotEmpty) ...[\n        OutlinedButton.icon(\n          onPressed: () => push(context, QuizPage(store: widget.store, questions: wrong, title: 'إعادة الأخطاء فقط')),\n          icon: const Icon(Icons.replay_rounded),\n          label: const Text('إعادة الأخطاء فقط'),\n        ),\n        const SizedBox(height: 8),\n      ],\n      FilledButton.icon(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.done_all_rounded), label: const Text('إنهاء الاختبار')),",
'repeat wrong')

p.write_text(s, encoding='utf-8')

pub = Path('pubspec.yaml')
ps = pub.read_text(encoding='utf-8')
if 'version: 3.4.8+37' not in ps:
    raise SystemExit('missing pubspec version anchor')
pub.write_text(ps.replace('version: 3.4.8+37', 'version: 3.5.3+38', 1), encoding='utf-8')

checks = [
    "const appVersion = '3.5.3';",
    "recentMistakes",
    "case 'lesson':",
    "case 'difficult':",
    "case 'mistakes':",
    "case 'notmastered':",
    "case 'smartmix':",
    "أخطائي الأخيرة",
    "مختلط ذكي",
    "إعادة الأخطاء فقط",
]
for token in checks:
    if token not in s:
        raise SystemExit(f'missing post-upgrade token: {token}')
print('Android v3.5.3 parity upgrade applied')
