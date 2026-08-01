from pathlib import Path
import re

path = Path('lib/main.dart')
text = path.read_text(encoding='utf-8')

# Excel package import.
excel_import = "import 'package:excel/excel.dart' as excel_lib;\n"
if excel_import not in text:
    anchor = "import 'package:file_picker/file_picker.dart';\n"
    text = text.replace(anchor, anchor + excel_import)

# Add robust JSON/Excel/CSV import methods to Store.
if 'Future<int> importJsonWords()' not in text:
    marker = '  Future<void> exportCsv() async {'
    methods = r'''  Future<int> _mergeImportedWords(List<WordItem> imported) async {
    final valid = imported
        .where((w) => w.en.trim().isNotEmpty && w.ar.trim().isNotEmpty && grades.contains(w.grade))
        .toList();
    final index = <String, WordItem>{
      for (final w in words) '${w.grade}|${w.en.trim().toLowerCase()}': w,
    };
    var added = 0;
    for (final word in valid) {
      final key = '${word.grade}|${word.en.trim().toLowerCase()}';
      if (!index.containsKey(key)) added++;
      index[key] = word;
    }
    words = index.values.toList(growable: true);
    await persistWords();
    notifyListeners();
    return added;
  }

  Future<int> importJsonWords() async {
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['json'],
      withData: true,
    );
    if (picked == null || picked.files.isEmpty) return -1;
    final bytes = picked.files.first.bytes;
    if (bytes == null) throw Exception('تعذر قراءة ملف JSON');
    final decoded = jsonDecode(utf8.decode(bytes));

    dynamic rawWords;
    if (decoded is List) {
      rawWords = decoded;
    } else if (decoded is Map) {
      rawWords = decoded['words'];
      if (rawWords == null && decoded['data'] is Map) {
        rawWords = decoded['data']['words'];
      }
    }
    if (rawWords is! List) {
      throw Exception('لم يتم العثور على قائمة words داخل الملف');
    }

    final imported = <WordItem>[];
    for (final item in rawWords) {
      if (item is Map) {
        imported.add(WordItem.fromJson(Map<String, dynamic>.from(item)));
      }
    }
    if (imported.isEmpty) throw Exception('لا توجد كلمات صالحة في الملف');
    return _mergeImportedWords(imported);
  }

  String _cellText(dynamic value) {
    if (value == null) return '';
    return value.toString().trim();
  }

  String _normalizeHeader(String value) => value
      .trim()
      .toLowerCase()
      .replaceAll(' ', '_')
      .replaceAll('-', '_');

  String _valueByHeaders(Map<String, String> row, List<String> names) {
    for (final name in names) {
      final value = row[_normalizeHeader(name)];
      if (value != null && value.trim().isNotEmpty) return value.trim();
    }
    return '';
  }

  WordItem? _wordFromImportRow(Map<String, String> row, int fallbackId) {
    final en = _valueByHeaders(row, ['word_en', 'english', 'word', 'الكلمة_الإنجليزية', 'الكلمة']);
    final ar = _valueByHeaders(row, ['meaning_ar', 'arabic', 'meaning', 'المعنى_العربي', 'المعنى']);
    if (en.isEmpty || ar.isEmpty) return null;
    final rawGrade = _valueByHeaders(row, ['grade', 'class', 'الصف']);
    final grade = normalizeGrade(rawGrade.isEmpty ? '1' : rawGrade);
    if (!grades.contains(grade)) return null;
    final rawId = _valueByHeaders(row, ['id', 'الرقم']);
    return WordItem(
      id: int.tryParse(rawId) ?? fallbackId,
      grade: grade,
      en: en,
      ar: ar,
      exampleEn: _valueByHeaders(row, ['example_en', 'sentence_en', 'example', 'الجملة_الإنجليزية', 'مثال_إنجليزي']),
      exampleAr: _valueByHeaders(row, ['example_ar', 'sentence_ar', 'translation', 'ترجمة_الجملة', 'مثال_عربي']),
    );
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

    if (extension == 'csv') {
      final lines = const LineSplitter().convert(utf8.decode(bytes).replaceFirst('\ufeff', ''));
      if (lines.isEmpty) throw Exception('ملف CSV فارغ');
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
      final headers = parseCsvLine(lines.first).map(_normalizeHeader).toList();
      for (final line in lines.skip(1)) {
        if (line.trim().isEmpty) continue;
        final values = parseCsvLine(line);
        final row = <String, String>{};
        for (var i = 0; i < headers.length; i++) {
          row[headers[i]] = i < values.length ? values[i].trim() : '';
        }
        final word = _wordFromImportRow(row, nextId);
        if (word != null) {
          imported.add(word);
          nextId++;
        }
      }
    } else {
      final workbook = excel_lib.Excel.decodeBytes(bytes);
      if (workbook.tables.isEmpty) throw Exception('ملف Excel لا يحتوي على أوراق');
      final sheet = workbook.tables.values.first;
      if (sheet.rows.isEmpty) throw Exception('ورقة Excel فارغة');
      final headers = sheet.rows.first.map((cell) => _normalizeHeader(_cellText(cell?.value))).toList();
      for (final cells in sheet.rows.skip(1)) {
        final row = <String, String>{};
        for (var i = 0; i < headers.length; i++) {
          row[headers[i]] = i < cells.length ? _cellText(cells[i]?.value) : '';
        }
        final word = _wordFromImportRow(row, nextId);
        if (word != null) {
          imported.add(word);
          nextId++;
        }
      }
    }

    if (imported.isEmpty) {
      throw Exception('لم يتم العثور على صفوف صالحة. تأكد من أسماء الأعمدة');
    }
    return _mergeImportedWords(imported);
  }

'''
    text = text.replace(marker, methods + marker)

# Add import controls in settings before backup/export controls.
if "title: 'رفع ملف JSON'" not in text:
    anchor = "          const SectionTitle('النسخ الاحتياطي ونقل البيانات'),"
    controls = anchor + r'''
          SettingsTile(
            icon: Icons.data_object_rounded,
            title: 'رفع ملف JSON',
            subtitle: 'استيراد الكلمات ودمجها دون تكرار',
            onTap: () async {
              try {
                final count = await store.importJsonWords();
                if (!context.mounted || count < 0) return;
                snack(context, count == 0 ? 'تم تحديث الكلمات الموجودة دون إضافة مكررات' : 'تم استيراد $count كلمة جديدة');
              } catch (e) {
                if (context.mounted) snack(context, 'تعذر استيراد JSON: $e');
              }
            },
          ),
          SettingsTile(
            icon: Icons.upload_file_rounded,
            title: 'رفع ملف Excel أو CSV',
            subtitle: 'يدعم XLSX وCSV مع دمج الكلمات تلقائياً',
            onTap: () async {
              try {
                final count = await store.importExcelWords();
                if (!context.mounted || count < 0) return;
                snack(context, count == 0 ? 'تم تحديث الكلمات الموجودة دون إضافة مكررات' : 'تم استيراد $count كلمة جديدة');
              } catch (e) {
                if (context.mounted) snack(context, 'تعذر استيراد الملف: $e');
              }
            },
          ),'''
    text = text.replace(anchor, controls)

path.write_text(text, encoding='utf-8')
print('Added JSON and Excel/CSV import features')
