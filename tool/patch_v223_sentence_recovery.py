from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

# Always end on v2.2.3, regardless of which previous patch set the version.
s = re.sub(r"const appVersion = '[^']+';", "const appVersion = '2.2.3';", s, count=1)

# Repair the exact build failure seen when the persistent-backup patch was
# applied to already-patched source.
while "  bool freshInstall = false;\n  bool freshInstall = false;\n" in s:
    s = s.replace(
        "  bool freshInstall = false;\n  bool freshInstall = false;\n",
        "  bool freshInstall = false;\n",
        1,
    )

old_json = "exampleEn: '${j['example_en'] ?? j['sentence_en'] ?? j['example'] ?? j['sentence'] ?? ''}'.trim(),\n        exampleAr: '${j['example_ar'] ?? j['sentence_ar'] ?? j['translation'] ?? j['sentence_translation'] ?? ''}'.trim(),"
new_json = "exampleEn: '${j['example_en'] ?? j['sentence_en'] ?? j['exampleEnglish'] ?? j['example_english'] ?? j['sentenceEnglish'] ?? j['sentence_english'] ?? j['exampleSentence'] ?? j['example_sentence'] ?? j['book_example'] ?? j['example'] ?? j['sentence'] ?? j['جملة مثال'] ?? j['مثال من الكتاب'] ?? j['الجملة الإنجليزية'] ?? ''}'.trim(),\n        exampleAr: '${j['example_ar'] ?? j['sentence_ar'] ?? j['exampleArabic'] ?? j['example_arabic'] ?? j['sentenceArabic'] ?? j['sentence_arabic'] ?? j['sentenceTranslation'] ?? j['sentence_translation'] ?? j['translation'] ?? j['ترجمة الجملة'] ?? j['ترجمة المثال'] ?? j['ترجمة المثال إلى العربية'] ?? ''}'.trim(),"
if old_json in s:
    s = s.replace(old_json, new_json, 1)

old_norm = "String _normalizeHeader(String value) => value\n      .trim()\n      .toLowerCase()\n      .replaceAll(' ', '_')\n      .replaceAll('-', '_');"
new_norm = "String _normalizeHeader(String value) => value\n      .trim()\n      .toLowerCase()\n      .replaceAll(RegExp(r'[ـ:：]'), '')\n      .replaceAll(RegExp(r'[أإآ]'), 'ا')\n      .replaceAll('ة', 'ه')\n      .replaceAll('ى', 'ي')\n      .replaceAll(RegExp(r'\\s+'), '_')\n      .replaceAll('-', '_');"
if old_norm in s:
    s = s.replace(old_norm, new_norm, 1)

old_aliases = "exampleEn: _valueByHeaders(row, ['example_en', 'sentence_en', 'example', 'sentence', 'الجملة_الإنجليزية', 'الجملة_الانجليزية', 'جملة_مثال', 'مثال_من_الكتاب', 'مثال_إنجليزي']),\n      exampleAr: _valueByHeaders(row, ['example_ar', 'sentence_ar', 'translation', 'sentence_translation', 'ترجمة_الجملة', 'ترجمة_المثال', 'ترجمة_المثال_إلى_العربية', 'مثال_عربي']),"
new_aliases = "exampleEn: _valueByHeaders(row, ['example_en', 'sentence_en', 'exampleenglish', 'example_english', 'sentenceenglish', 'sentence_english', 'examplesentence', 'example_sentence', 'book_example', 'example', 'sentence', 'الجمله_الانجليزيه', 'جمله_مثال', 'مثال_جمله', 'مثال_من_الكتاب', 'مثال_انجليزي']),\n      exampleAr: _valueByHeaders(row, ['example_ar', 'sentence_ar', 'examplearabic', 'example_arabic', 'sentencearabic', 'sentence_arabic', 'translation', 'sentencetranslation', 'sentence_translation', 'ترجمه_الجمله', 'ترجمه_المثال', 'ترجمه_المثال_الي_العربيه', 'مثال_عربي']),"
if old_aliases in s:
    s = s.replace(old_aliases, new_aliases, 1)

# Make missing English source data explicit, but add this notice only once.
missing_notice = 'الجملة الإنجليزية غير محفوظة لهذه الكلمة'
if missing_notice not in s:
    old_panel = "if (word.exampleAr.isNotEmpty) ...[\n                                const SizedBox(height: 14),"
    new_panel = "if (word.exampleEn.isEmpty && word.exampleAr.isNotEmpty) ...[\n                                const Text('الجملة الإنجليزية غير محفوظة لهذه الكلمة', textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.w800)),\n                                const SizedBox(height: 8),\n                                const Text('أعد استيراد ملف Excel نفسه مرة واحدة لتحديث الجملة الإنجليزية دون تكرار الكلمة.', textAlign: TextAlign.center),\n                              ],\n                              if (word.exampleAr.isNotEmpty) ...[\n                                const SizedBox(height: 14),"
    if old_panel in s:
        s = s.replace(old_panel, new_panel, 1)

p.write_text(s, encoding='utf-8')
print('Applied v2.2.3 sentence recovery/import compatibility patch safely')