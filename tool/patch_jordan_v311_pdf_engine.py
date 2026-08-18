from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

# Replace the older PDF text plugin with pdfrx, which is maintained and supports direct page text extraction.
s = s.replace("import 'package:read_pdf_text/read_pdf_text.dart';\n", "")
if "import 'package:pdfrx/pdfrx.dart';" not in s:
    s = s.replace("import 'package:path_provider/path_provider.dart';", "import 'package:path_provider/path_provider.dart';\nimport 'package:pdfrx/pdfrx.dart';", 1)

s = s.replace("const appVersion = '3.1.0';", "const appVersion = '3.1.1';", 1)

old_main = """void main() {\n  WidgetsFlutterBinding.ensureInitialized();\n"""
new_main = """Future<void> main() async {\n  WidgetsFlutterBinding.ensureInitialized();\n  await pdfrxFlutterInitialize();\n"""
if old_main in s:
    s = s.replace(old_main, new_main, 1)

old = """      final pages = await ReadPdfText.getPDFtextPaginated(file.path!);\n      final map = <String, BookCandidate>{};\n      String currentUnit = '';\n      String currentLesson = '';\n      for (var pi = 0; pi < pages.length; pi++) {\n        final text = pages[pi];\n"""
new = """      final document = await PdfDocument.openFile(file.path!);\n      final pages = <String>[];\n      try {\n        for (final page in document.pages) {\n          final pageText = await page.loadText();\n          pages.add(pageText?.fullText ?? '');\n        }\n      } finally {\n        await document.dispose();\n      }\n      final map = <String, BookCandidate>{};\n      String currentUnit = '';\n      String currentLesson = '';\n      for (var pi = 0; pi < pages.length; pi++) {\n        final text = pages[pi];\n"""
if old not in s:
    raise SystemExit('PDF extraction anchor not found')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('Jordan v3.1.1 PDF engine patch applied')
