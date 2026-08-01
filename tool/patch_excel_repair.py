from pathlib import Path

path = Path('lib/main.dart')
text = path.read_text(encoding='utf-8')

archive_import = "import 'package:archive/archive.dart' as archive_lib;\n"
if archive_import not in text:
    anchor = "import 'package:excel/excel.dart' as excel_lib;\n"
    text = text.replace(anchor, anchor + archive_import)

helper = r'''
  excel_lib.Excel _decodeExcelLenient(List<int> bytes) {
    try {
      return excel_lib.Excel.decodeBytes(bytes);
    } catch (_) {
      final source = archive_lib.ZipDecoder().decodeBytes(bytes, verify: false);
      final repaired = archive_lib.Archive();
      const minimalStyles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <numFmts count="0"/>
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
  <dxfs count="0"/>
  <tableStyles count="0" defaultTableStyle="TableStyleMedium2" defaultPivotStyle="PivotStyleLight16"/>
</styleSheet>''';

      var stylesFound = false;
      for (final file in source.files) {
        if (!file.isFile) continue;
        if (file.name == 'xl/styles.xml') {
          final data = utf8.encode(minimalStyles);
          repaired.addFile(archive_lib.ArchiveFile(file.name, data.length, data));
          stylesFound = true;
        } else {
          final data = file.content as List<int>;
          repaired.addFile(archive_lib.ArchiveFile(file.name, data.length, data));
        }
      }
      if (!stylesFound) {
        final data = utf8.encode(minimalStyles);
        repaired.addFile(archive_lib.ArchiveFile('xl/styles.xml', data.length, data));
      }
      final encoded = archive_lib.ZipEncoder().encode(repaired);
      if (encoded == null) throw Exception('تعذر إصلاح ملف Excel');
      return excel_lib.Excel.decodeBytes(encoded);
    }
  }

'''

if '_decodeExcelLenient(' not in text:
    marker = '  Future<int> importExcelWords() async {'
    text = text.replace(marker, helper + marker)

text = text.replace(
    'final workbook = excel_lib.Excel.decodeBytes(bytes);',
    'final workbook = _decodeExcelLenient(bytes);',
)

path.write_text(text, encoding='utf-8')
print('Added lenient Excel repair for damaged styles.xml')
