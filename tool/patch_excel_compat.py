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
    } catch (_) {
      final archive = ZipDecoder().decodeBytes(bytes, verify: true);
      final repaired = Archive();

      for (final file in archive.files) {
        if (!file.isFile || file.name == 'xl/styles.xml') continue;

        var data = List<int>.from(file.content as List<int>);
        if (file.name == '[Content_Types].xml' ||
            file.name == 'xl/_rels/workbook.xml.rels') {
          var xml = utf8.decode(data, allowMalformed: true);
          xml = xml.replaceAll(
            RegExp(r'<Override[^>]*PartName="/xl/styles.xml"[^>]*/>'),
            '',
          );
          xml = xml.replaceAll(
            RegExp(r'<Relationship[^>]*Type="[^"]*/styles"[^>]*/>'),
            '',
          );
          data = utf8.encode(xml);
        }

        repaired.addFile(ArchiveFile(file.name, data.length, data));
      }

      final encoded = ZipEncoder().encode(repaired);
      if (encoded == null) rethrow;
      return excel_lib.Excel.decodeBytes(Uint8List.fromList(encoded));
    }
  }

'''

marker = '  Future<int> importExcelWords() async {'
if '_decodeExcelCompat(Uint8List bytes)' not in text:
    text = text.replace(marker, helper + marker)

text = text.replace(
    'final workbook = excel_lib.Excel.decodeBytes(bytes);',
    'final workbook = _decodeExcelCompat(Uint8List.fromList(bytes));',
)

path.write_text(text, encoding='utf-8')
print('Restored compatible Excel import with style-free fallback')
