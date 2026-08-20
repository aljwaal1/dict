from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

s = s.replace("const appVersion = '3.2.0';", "const appVersion = '3.2.1';", 1)

# Unit/Lesson labels must be numeric. Text such as "Unit to" or "Lesson Appearance"
# is normal sentence content, not curriculum metadata.
s = s.replace(
    r"RegExp(r'\\bUnit\\s+([0-9]+|[A-Za-z]+)', caseSensitive: false).firstMatch(text)",
    r"RegExp(r'\\bUnit\\s+([0-9]{1,2})\\b', caseSensitive: false).firstMatch(text)",
)
s = s.replace(
    r"RegExp(r'\\bLesson\\s+([0-9]+|[A-Za-z]+)', caseSensitive: false).firstMatch(text)",
    r"RegExp(r'\\bLesson\\s+([0-9]{1,2})\\b', caseSensitive: false).firstMatch(text)",
)

# A vocabulary item should be unique across the whole imported book. Its frequency
# still accumulates from every page; we keep the first/best source metadata.
s = s.replace(
    "final key = '${currentUnit.toLowerCase()}|${currentLesson.toLowerCase()}|${raw.toLowerCase()}';",
    "final key = raw.toLowerCase();",
    1,
)

# Additional textbook/UI/instruction noise that should not become vocabulary cards.
needle = "if (extraNoise.contains(lower)) return false;"
insert = """if (extraNoise.contains(lower)) return false;
    const bookNoise = <String>{
      'unit','lesson','page','pages','student','students','teacher','teachers','book','books','workbook','workbooks',
      'exercise','exercises','activity','activities','task','tasks','question','questions','answer','answers',
      'read','write','listen','look','check','choose','circle','match','complete','tick','underline','work','pair','pairs','group','groups',
      'example','examples','english','arabic','grammar','vocabulary','language','review','revision','practice','project',
      'true','false','correct','incorrect','number','numbers','name','names','word','words','sentence','sentences',
      'first','second','third','fourth','next','previous','following','above','below'
    };
    if (bookNoise.contains(lower)) return false;"""
if needle in s and 'const bookNoise' not in s:
    s = s.replace(needle, insert, 1)

# Keep repeated words, known dictionary words, and substantial one-off vocabulary.
old_filter = "final list = map.values.where((e) => e.frequency >= 2 || e.exampleEn.isNotEmpty).toList();"
new_filter = "final list = map.values.where((e) => e.frequency >= 2 || e.meaning.trim().isNotEmpty || (e.frequency == 1 && e.word.length >= 5 && e.exampleEn.isNotEmpty)).toList();"
if old_filter in s:
    s = s.replace(old_filter, new_filter, 1)

# Do not require Wi-Fi for model download. Mobile data is acceptable when the user
# explicitly starts extraction, and once downloaded ML Kit works on-device.
s = s.replace("await manager.downloadModel(source.bcpCode);", "await manager.downloadModel(source.bcpCode, isWifiRequired: false);", 1)
s = s.replace("await manager.downloadModel(target.bcpCode);", "await manager.downloadModel(target.bcpCode, isWifiRequired: false);", 1)

p.write_text(s, encoding='utf-8')
print('Jordan v3.2.1 clean extraction patch applied')
