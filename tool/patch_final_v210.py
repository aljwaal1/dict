from pathlib import Path
import re

p = Path('lib/main.dart')
text = p.read_text(encoding='utf-8')

# Version and XML parser import.
text = re.sub(r"const appVersion = '[^']+';", "const appVersion = '2.1.0';", text, count=1)
if "package:xml/xml.dart" not in text:
    text = text.replace("import 'package:shared_preferences/shared_preferences.dart';", "import 'package:shared_preferences/shared_preferences.dart';\nimport 'package:xml/xml.dart';")

# TTS state and initialization.
text = text.replace("  final tts = FlutterTts();", "  final tts = FlutterTts();\n  bool ttsReady = false;\n  String ttsLanguage = 'en-US';")
text = re.sub(
    r"    await tts\.setLanguage\('en-US'\);\n    await tts\.setSpeechRate\(\.38\);\n    await tts\.setPitch\(1\.0\);\n    await tts\.setVolume\(1\.0\);\n    await tts\.awaitSpeakCompletion\(true\);",
    "    await _configureTts();",
    text,
    count=1,
)

new_tts = r'''  Future<bool> _configureTts() async {
    try {
      await tts.awaitSpeakCompletion(false);
      await tts.setSpeechRate(.42);
      await tts.setPitch(1.0);
      await tts.setVolume(1.0);
      const candidates = ['en-US', 'en-GB', 'en-AU', 'en'];
      for (final language in candidates) {
        try {
          final result = await tts.setLanguage(language);
          if (result == 1 || result == true || result == null) {
            ttsLanguage = language;
            ttsReady = true;
            return true;
          }
        } catch (_) {}
      }
      ttsReady = false;
      return false;
    } catch (_) {
      ttsReady = false;
      return false;
    }
  }

  Future<bool> speak(String text) async {
    final value = text.trim();
    if (!sound || value.isEmpty) return false;
    try {
      if (!ttsReady && !await _configureTts()) return false;
      await tts.stop();
      await tts.setLanguage(ttsLanguage);
      await tts.setSpeechRate(.42);
      await tts.setPitch(1.0);
      await tts.setVolume(1.0);
      final result = await tts.speak(value);
      return result == 1 || result == true || result == null;
    } catch (_) {
      ttsReady = false;
      if (!await _configureTts()) return false;
      try {
        final result = await tts.speak(value);
        return result == 1 || result == true || result == null;
      } catch (_) {
        return false;
      }
    }
  }

  Future<bool> testPronunciation() async {
    if (!sound) return false;
    return speak('Welcome to my school dictionary');
  }'''
text = re.sub(
    r"  Future<void> speak\(String text\) async \{.*?\n  \}\n\n  Future<bool> testPronunciation\(\) async \{.*?\n  \}",
    new_tts,
    text,
    count=1,
    flags=re.S,
)

# XLSX parser that reads values directly from worksheet XML and never parses styles.xml.
excel_block = r'''  List<List<String>> _readXlsxRows(Uint8List bytes) {
    final archive = ZipDecoder().decodeBytes(bytes, verify: true);
    final files = <String, List<int>>{};
    for (final file in archive.files) {
      if (!file.isFile) continue;
      files[file.name] = List<int>.from(file.content as List<int>);
    }

    final shared = <String>[];
    final sharedBytes = files['xl/sharedStrings.xml'];
    if (sharedBytes != null) {
      final doc = XmlDocument.parse(utf8.decode(sharedBytes, allowMalformed: true));
      for (final si in doc.descendants.whereType<XmlElement>().where((e) => e.name.local == 'si')) {
        shared.add(si.descendants.whereType<XmlElement>().where((e) => e.name.local == 't').map((e) => e.innerText).join());
      }
    }

    int columnIndex(String reference) {
      final letters = RegExp(r'^[A-Za-z]+').firstMatch(reference)?.group(0)?.toUpperCase() ?? 'A';
      var value = 0;
      for (final code in letters.codeUnits) value = value * 26 + code - 64;
      return value - 1;
    }

    final sheetNames = files.keys.where((name) => RegExp(r'^xl/worksheets/sheet\d+\.xml$').hasMatch(name)).toList()
      ..sort((a, b) {
        final na = int.tryParse(RegExp(r'\d+').firstMatch(a)?.group(0) ?? '') ?? 0;
        final nb = int.tryParse(RegExp(r'\d+').firstMatch(b)?.group(0) ?? '') ?? 0;
        return na.compareTo(nb);
      });
    if (sheetNames.isEmpty) throw Exception('ملف Excel لا يحتوي على أوراق قابلة للقراءة');

    final allRows = <List<String>>[];
    for (final name in sheetNames) {
      final doc = XmlDocument.parse(utf8.decode(files[name]!, allowMalformed: true));
      for (final rowElement in doc.descendants.whereType<XmlElement>().where((e) => e.name.local == 'row')) {
        final values = <int, String>{};
        var maxColumn = -1;
        for (final cell in rowElement.children.whereType<XmlElement>().where((e) => e.name.local == 'c')) {
          final ref = cell.getAttribute('r') ?? 'A1';
          final col = columnIndex(ref);
          maxColumn = max(maxColumn, col);
          final type = cell.getAttribute('t') ?? '';
          String value = '';
          if (type == 'inlineStr') {
            value = cell.descendants.whereType<XmlElement>().where((e) => e.name.local == 't').map((e) => e.innerText).join();
          } else {
            final raw = cell.descendants.whereType<XmlElement>().where((e) => e.name.local == 'v').map((e) => e.innerText).firstOrNull ?? '';
            if (type == 's') {
              final index = int.tryParse(raw) ?? -1;
              value = index >= 0 && index < shared.length ? shared[index] : '';
            } else if (type == 'b') {
              value = raw == '1' ? 'true' : 'false';
            } else {
              value = raw;
            }
          }
          values[col] = value.trim();
        }
        if (maxColumn >= 0) {
          allRows.add(List<String>.generate(maxColumn + 1, (i) => values[i] ?? ''));
        }
      }
    }
    return allRows;
  }

  Future<int> importExcelWords() async {
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['xlsx', 'csv'],
      withData: true,
    );
    if (picked == null || picked.files.isEmpty) return -1;
    final file = picked.files.first;
    final bytes = file.bytes;
    if (bytes == null) throw Exception('تعذر قراءة الملف');
    final extension = (file.extension ?? '').toLowerCase();
    final imported = <WordItem>[];
    var nextId = words.isEmpty ? 1 : words.map((w) => w.id).reduce(max) + 1;

    List<String> parseCsvLine(String line) {
      final values = <String>[];
      final current = StringBuffer();
      var quoted = false;
      for (var i = 0; i < line.length; i++) {
        final char = line[i];
        if (char == '"') {
          if (quoted && i + 1 < line.length && line[i + 1] == '"') {
            current.write('"');
            i++;
          } else {
            quoted = !quoted;
          }
        } else if (char == ',' && !quoted) {
          values.add(current.toString());
          current.clear();
        } else {
          current.write(char);
        }
      }
      values.add(current.toString());
      return values;
    }

    if (extension == 'csv') {
      final lines = const LineSplitter().convert(utf8.decode(bytes, allowMalformed: true).replaceFirst('\ufeff', ''));
      if (lines.isEmpty) throw Exception('ملف CSV فارغ');
      final headers = parseCsvLine(lines.first).map(_normalizeHeader).toList();
      for (final line in lines.skip(1)) {
        if (line.trim().isEmpty) continue;
        final cells = parseCsvLine(line);
        final row = <String, String>{};
        for (var i = 0; i < headers.length; i++) row[headers[i]] = i < cells.length ? cells[i].trim() : '';
        final word = _wordFromImportRow(row, nextId);
        if (word != null) { imported.add(word); nextId++; }
      }
    } else {
      final rows = _readXlsxRows(Uint8List.fromList(bytes));
      if (rows.isEmpty) throw Exception('ورقة Excel فارغة');
      var headers = <String>[];
      for (final cells in rows) {
        if (cells.every((v) => v.trim().isEmpty)) continue;
        if (headers.isEmpty) {
          headers = cells.map(_normalizeHeader).toList();
          continue;
        }
        final row = <String, String>{};
        for (var i = 0; i < headers.length; i++) row[headers[i]] = i < cells.length ? cells[i].trim() : '';
        final word = _wordFromImportRow(row, nextId);
        if (word != null) { imported.add(word); nextId++; }
      }
    }
    if (imported.isEmpty) throw Exception('لم يتم العثور على كلمات صالحة. يجب أن يحتوي الصف الأول على عناوين الأعمدة');
    return _mergeImportedWords(imported);
  }'''
text = re.sub(
    r"  excel_lib\.Excel _decodeExcelCompat\(Uint8List bytes\) \{.*?\n  Future<int> importExcelWords\(\) async \{.*?\n  \}",
    excel_block,
    text,
    count=1,
    flags=re.S,
)

# Explicit, accessible flashcards with pronunciation, example, meaning, previous and next.
flashcards = r'''class FlashCardsPage extends StatefulWidget {
  final Store store;
  const FlashCardsPage({super.key, required this.store});

  @override
  State<FlashCardsPage> createState() => _FlashCardsPageState();
}

class _FlashCardsPageState extends State<FlashCardsPage> {
  String grade = '1';
  int index = 0;
  bool showMeaning = false;
  bool showExample = false;

  void move(int delta, int length) {
    if (length == 0) return;
    setState(() {
      index = (index + delta) % length;
      if (index < 0) index += length;
      showMeaning = false;
      showExample = false;
    });
    widget.store.saveLastIndex(grade, index);
  }

  Future<void> pronounce(BuildContext context, String value) async {
    final ok = await widget.store.speak(value);
    if (!ok && context.mounted) snack(context, 'تعذر تشغيل النطق. فعّل محرك تحويل النص إلى كلام الإنجليزي من إعدادات الهاتف');
  }

  @override
  Widget build(BuildContext context) {
    final list = widget.store.byGrade(grade);
    if (list.isNotEmpty && index >= list.length) index = 0;
    final word = list.isEmpty ? null : list[index];
    final hasExample = word != null && (word.exampleEn.isNotEmpty || word.exampleAr.isNotEmpty);
    return Scaffold(
      appBar: AppBar(title: const Text('البطاقات التعليمية')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          DropdownButtonFormField<String>(
            initialValue: grade,
            items: grades.map((g) => DropdownMenuItem(value: g, child: Text(gradeName(g)))).toList(),
            onChanged: (value) => setState(() {
              grade = value ?? '1';
              index = widget.store.lastIndex(grade);
              showMeaning = false;
              showExample = false;
            }),
          ),
          const SizedBox(height: 12),
          if (word != null) Text('${index + 1} / ${list.length}', style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          Expanded(
            child: word == null
                ? const Center(child: Text('لا توجد كلمات في هذا الصف'))
                : GestureDetector(
                    onHorizontalDragEnd: (details) {
                      final v = details.primaryVelocity ?? 0;
                      if (v < -100) move(1, list.length);
                      if (v > 100) move(-1, list.length);
                    },
                    child: Card(
                      child: ListView(
                        padding: const EdgeInsets.all(24),
                        children: [
                          const SizedBox(height: 22),
                          Text(word.en, textDirection: TextDirection.ltr, textAlign: TextAlign.center, style: const TextStyle(fontSize: 42, fontWeight: FontWeight.w900)),
                          const SizedBox(height: 24),
                          FilledButton.tonalIcon(
                            onPressed: () => pronounce(context, word.en),
                            icon: const Icon(Icons.volume_up_rounded),
                            label: const Text('لفظ الكلمة'),
                          ),
                          const SizedBox(height: 12),
                          if (hasExample) OutlinedButton.icon(
                            onPressed: () => setState(() => showExample = !showExample),
                            icon: const Icon(Icons.format_quote_rounded),
                            label: Text(showExample ? 'إخفاء مثال الجملة' : 'إظهار مثال الجملة'),
                          ),
                          if (hasExample) const SizedBox(height: 12),
                          FilledButton.icon(
                            onPressed: () => setState(() => showMeaning = !showMeaning),
                            icon: const Icon(Icons.translate_rounded),
                            label: Text(showMeaning ? 'إخفاء المعنى' : 'إظهار المعنى'),
                          ),
                          if (showMeaning) Padding(
                            padding: const EdgeInsets.only(top: 24),
                            child: Text(word.ar, textAlign: TextAlign.center, style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w900)),
                          ),
                          if (showExample) Container(
                            margin: const EdgeInsets.only(top: 20),
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(color: Theme.of(context).colorScheme.secondaryContainer, borderRadius: BorderRadius.circular(18)),
                            child: Column(children: [
                              if (word.exampleEn.isNotEmpty) Row(children: [
                                Expanded(child: Text(word.exampleEn, textDirection: TextDirection.ltr, textAlign: TextAlign.center, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700))),
                                IconButton(onPressed: () => pronounce(context, word.exampleEn), icon: const Icon(Icons.volume_up_rounded)),
                              ]),
                              if (word.exampleAr.isNotEmpty) Text(word.exampleAr, textAlign: TextAlign.center),
                            ]),
                          ),
                        ],
                      ),
                    ),
                  ),
          ),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(child: OutlinedButton.icon(onPressed: word == null ? null : () => move(-1, list.length), icon: const Icon(Icons.arrow_forward_rounded), label: const Text('السابق'))),
            const SizedBox(width: 10),
            Expanded(child: FilledButton.icon(onPressed: word == null ? null : () => move(1, list.length), icon: const Icon(Icons.arrow_back_rounded), label: const Text('التالي'))),
          ]),
          const SizedBox(height: 8),
          Row(children: [
            Expanded(child: OutlinedButton.icon(onPressed: word == null ? null : () async { await widget.store.answer(word, false); move(1, list.length); }, icon: const Icon(Icons.refresh), label: const Text('تحتاج مراجعة'))),
            const SizedBox(width: 10),
            Expanded(child: FilledButton.icon(onPressed: word == null ? null : () async { await widget.store.answer(word, true); move(1, list.length); }, icon: const Icon(Icons.check), label: const Text('أتقنتها'))),
          ]),
        ]),
      ),
    );
  }
}

'''
text = re.sub(r"class FlashCardsPage extends StatefulWidget \{.*?\nclass QuizSetupPage", flashcards + "class QuizSetupPage", text, count=1, flags=re.S)

# Navigable word card. Existing 3-argument calls continue to work.
word_card = r'''void showWord(BuildContext context, Store store, WordItem word, {List<WordItem>? source, int? initialIndex}) {
  final list = (source == null || source.isEmpty) ? store.byGrade(word.grade) : source;
  var index = initialIndex ?? list.indexWhere((item) => item.id == word.id);
  if (index < 0) index = 0;
  push(context, WordCardPage(store: store, words: list.isEmpty ? [word] : list, initialIndex: index));
}

class WordCardPage extends StatefulWidget {
  final Store store;
  final List<WordItem> words;
  final int initialIndex;
  const WordCardPage({super.key, required this.store, required this.words, required this.initialIndex});

  @override
  State<WordCardPage> createState() => _WordCardPageState();
}

class _WordCardPageState extends State<WordCardPage> {
  late int index;
  bool showMeaning = false;
  bool showExample = false;

  @override
  void initState() {
    super.initState();
    index = widget.initialIndex.clamp(0, widget.words.length - 1);
  }

  void move(int delta) {
    setState(() {
      index = (index + delta) % widget.words.length;
      if (index < 0) index += widget.words.length;
      showMeaning = false;
      showExample = false;
    });
  }

  Future<void> pronounce(String value) async {
    final ok = await widget.store.speak(value);
    if (!ok && mounted) snack(context, 'تعذر تشغيل النطق. ثبّت أو فعّل صوت اللغة الإنجليزية في إعدادات الهاتف');
  }

  @override
  Widget build(BuildContext context) {
    final word = widget.words[index];
    final hasExample = word.exampleEn.isNotEmpty || word.exampleAr.isNotEmpty;
    return Scaffold(
      appBar: AppBar(title: Text('بطاقة الكلمة ${index + 1} / ${widget.words.length}')),
      body: SafeArea(
        child: GestureDetector(
          onHorizontalDragEnd: (details) {
            final v = details.primaryVelocity ?? 0;
            if (v < -100) move(1);
            if (v > 100) move(-1);
          },
          child: ListView(
            padding: const EdgeInsets.all(18),
            children: [
              Card(child: Padding(
                padding: const EdgeInsets.fromLTRB(22, 34, 22, 28),
                child: Column(children: [
                  Text(word.en, textDirection: TextDirection.ltr, textAlign: TextAlign.center, style: const TextStyle(fontSize: 43, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 8),
                  Text(gradeName(word.grade), style: const TextStyle(color: Color(0xff6f7d94))),
                  const SizedBox(height: 24),
                  SizedBox(width: double.infinity, child: FilledButton.tonalIcon(onPressed: () => pronounce(word.en), icon: const Icon(Icons.volume_up_rounded), label: const Text('لفظ الكلمة'))),
                  const SizedBox(height: 12),
                  if (hasExample) SizedBox(width: double.infinity, child: OutlinedButton.icon(onPressed: () => setState(() => showExample = !showExample), icon: const Icon(Icons.format_quote_rounded), label: Text(showExample ? 'إخفاء مثال الجملة' : 'إظهار مثال الجملة'))),
                  if (hasExample) const SizedBox(height: 12),
                  SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: () => setState(() => showMeaning = !showMeaning), icon: const Icon(Icons.translate_rounded), label: Text(showMeaning ? 'إخفاء المعنى' : 'إظهار المعنى'))),
                  if (showMeaning) Container(width: double.infinity, margin: const EdgeInsets.only(top: 20), padding: const EdgeInsets.all(20), decoration: BoxDecoration(color: Theme.of(context).colorScheme.primaryContainer, borderRadius: BorderRadius.circular(20)), child: Text(word.ar, textAlign: TextAlign.center, style: const TextStyle(fontSize: 31, fontWeight: FontWeight.w900))),
                  if (showExample) Container(width: double.infinity, margin: const EdgeInsets.only(top: 20), padding: const EdgeInsets.all(18), decoration: BoxDecoration(color: Theme.of(context).colorScheme.secondaryContainer, borderRadius: BorderRadius.circular(20)), child: Column(children: [
                    if (word.exampleEn.isNotEmpty) Row(children: [Expanded(child: Text(word.exampleEn, textDirection: TextDirection.ltr, textAlign: TextAlign.center, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w700))), IconButton.filledTonal(onPressed: () => pronounce(word.exampleEn), icon: const Icon(Icons.volume_up_rounded))]),
                    if (word.exampleAr.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 8), child: Text(word.exampleAr, textAlign: TextAlign.center)),
                  ])),
                ]),
              )),
              const SizedBox(height: 12),
              Row(children: [
                Expanded(child: OutlinedButton.icon(onPressed: () => move(-1), icon: const Icon(Icons.arrow_forward_rounded), label: const Text('السابق'))),
                const SizedBox(width: 12),
                Expanded(child: FilledButton.icon(onPressed: () => move(1), icon: const Icon(Icons.arrow_back_rounded), label: const Text('التالي'))),
              ]),
            ],
          ),
        ),
      ),
    );
  }
}

'''
text = re.sub(r"void showWord\(BuildContext context, Store store, WordItem w\) \{.*?\nvoid push\(BuildContext context", word_card + "void push(BuildContext context", text, count=1, flags=re.S)

# Pass the active list/index to word cards where available.
text = text.replace("onTap: () => showWord(context, widget.store, w),", "onTap: () => showWord(context, widget.store, w, source: list, initialIndex: i),")
text = text.replace("if (context.mounted) showWord(context, store, w);", "if (context.mounted) showWord(context, store, w, source: list, initialIndex: i);")

p.write_text(text, encoding='utf-8')
print('Applied final v2.1.0 root fixes')
