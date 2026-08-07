from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

s = s.replace("const appVersion = '2.2.2';", "const appVersion = '2.2.3';")

old = "exampleEn: '${j['example_en'] ?? j['sentence_en'] ?? j['example'] ?? j['sentence'] ?? ''}'.trim(),\n        exampleAr: '${j['example_ar'] ?? j['sentence_ar'] ?? j['translation'] ?? j['sentence_translation'] ?? ''}'.trim(),"
new = "exampleEn: '${j['example_en'] ?? j['sentence_en'] ?? j['exampleEnglish'] ?? j['example_english'] ?? j['sentenceEnglish'] ?? j['sentence_english'] ?? j['exampleSentence'] ?? j['example_sentence'] ?? j['book_example'] ?? j['example'] ?? j['sentence'] ?? j['جملة مثال'] ?? j['مثال من الكتاب'] ?? j['الجملة الإنجليزية'] ?? ''}'.trim(),\n        exampleAr: '${j['example_ar'] ?? j['sentence_ar'] ?? j['exampleArabic'] ?? j['example_arabic'] ?? j['sentenceArabic'] ?? j['sentence_arabic'] ?? j['sentenceTranslation'] ?? j['sentence_translation'] ?? j['translation'] ?? j['ترجمة الجملة'] ?? j['ترجمة المثال'] ?? j['ترجمة المثال إلى العربية'] ?? ''}'.trim(),"
if old not in s:
    raise SystemExit('WordItem.fromJson target not found')
s = s.replace(old, new, 1)

old = "String _normalizeHeader(String value) => value\n      .trim()\n      .toLowerCase()\n      .replaceAll(' ', '_')\n      .replaceAll('-', '_');"
new = "String _normalizeHeader(String value) => value\n      .trim()\n      .toLowerCase()\n      .replaceAll(RegExp(r'[ـ:：]'), '')\n      .replaceAll(RegExp(r'[أإآ]'), 'ا')\n      .replaceAll('ة', 'ه')\n      .replaceAll('ى', 'ي')\n      .replaceAll(RegExp(r'\\s+'), '_')\n      .replaceAll('-', '_');"
if old not in s:
    raise SystemExit('normalize header target not found')
s = s.replace(old, new, 1)

old = "exampleEn: _valueByHeaders(row, ['example_en', 'sentence_en', 'example', 'sentence', 'الجملة_الإنجليزية', 'الجملة_الانجليزية', 'جملة_مثال', 'مثال_من_الكتاب', 'مثال_إنجليزي']),\n      exampleAr: _valueByHeaders(row, ['example_ar', 'sentence_ar', 'translation', 'sentence_translation', 'ترجمة_الجملة', 'ترجمة_المثال', 'ترجمة_المثال_إلى_العربية', 'مثال_عربي']),"
new = "exampleEn: _valueByHeaders(row, ['example_en', 'sentence_en', 'exampleenglish', 'example_english', 'sentenceenglish', 'sentence_english', 'examplesentence', 'example_sentence', 'book_example', 'example', 'sentence', 'الجمله_الانجليزيه', 'جمله_مثال', 'مثال_جمله', 'مثال_من_الكتاب', 'مثال_انجليزي']),\n      exampleAr: _valueByHeaders(row, ['example_ar', 'sentence_ar', 'examplearabic', 'example_arabic', 'sentencearabic', 'sentence_arabic', 'translation', 'sentencetranslation', 'sentence_translation', 'ترجمه_الجمله', 'ترجمه_المثال', 'ترجمه_المثال_الي_العربيه', 'مثال_عربي']),"
if old not in s:
    raise SystemExit('import aliases target not found')
s = s.replace(old, new, 1)

# Make the sentence panel explicitly show when the English sentence is missing,
# so the user can distinguish missing source data from a rendering bug.
old = "if (word.exampleAr.isNotEmpty) ...[\n                                const SizedBox(height: 14),"
new = "if (word.exampleEn.isEmpty && word.exampleAr.isNotEmpty) ...[\n                                const Text('الجملة الإنجليزية غير محفوظة لهذه الكلمة', textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.w800)),\n                                const SizedBox(height: 8),\n                                const Text('أعد استيراد ملف Excel نفسه مرة واحدة لتحديث الجملة الإنجليزية دون تكرار الكلمة.', textAlign: TextAlign.center),\n                              ],\n                              if (word.exampleAr.isNotEmpty) ...[\n                                const SizedBox(height: 14),"
if old not in s:
    raise SystemExit('sentence panel target not found')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('Applied v2.2.3 sentence recovery/import compatibility patch')
