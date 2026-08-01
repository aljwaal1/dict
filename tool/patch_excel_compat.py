from pathlib import Path

path = Path('lib/main.dart')
text = path.read_text(encoding='utf-8')

if "import 'dart:typed_data';" not in text:
    text = text.replace("import 'dart:math';\n", "import 'dart:math';\nimport 'dart:typed_data';\n")

if "import 'package:archive/archive.dart';" not in text:
    text = text.replace(
        "import 'package:excel/excel.dart' as excel_lib;\n",
        "import 'package:excel/excel.dart' as excel_lib;\nimport 'package:archive/archive.dart';\n",
    )

helper = r'''  excel_lib.Excel _decodeExcelCompat(Uint8List bytes) {
    try {
      return excel_lib.Excel.decodeBytes(bytes);
    } catch (firstError) {
      final archive = ZipDecoder().decodeBytes(bytes, verify: true);
      final repaired = Archive();

      for (final file in archive.files) {
        if (!file.isFile) continue;
        var data = List<int>.from(file.content as List<int>);

        if (file.name == 'xl/styles.xml') {
          var xml = utf8.decode(data, allowMalformed: true);
          // Some valid XLSX files use a namespace prefix such as x:styleSheet.
          // The Dart excel parser may incorrectly report these as damaged.
          xml = xml
              .replaceAll('xmlns:x=', 'xmlns=')
              .replaceAll('<x:', '<')
              .replaceAll('</x:', '</');
          data = utf8.encode(xml);
        }

        repaired.addFile(ArchiveFile(file.name, data.length, data));
      }

      final encoded = ZipEncoder().encode(repaired);
      if (encoded == null) throw firstError;
      return excel_lib.Excel.decodeBytes(Uint8List.fromList(encoded));
    }
  }

'''

marker = '  Future<int> importExcelWords() async {'
if '_decodeExcelCompat(Uint8List bytes)' not in text:
    text = text.replace(marker, helper + marker)
else:
    start = text.find('  excel_lib.Excel _decodeExcelCompat(Uint8List bytes) {')
    end = text.find(marker, start)
    if start != -1 and end != -1:
        text = text[:start] + helper + text[end:]

text = text.replace(
    'final workbook = excel_lib.Excel.decodeBytes(bytes);',
    'final workbook = _decodeExcelCompat(Uint8List.fromList(bytes));',
)

path.write_text(text, encoding='utf-8')
print('Fixed Excel style namespace compatibility')
