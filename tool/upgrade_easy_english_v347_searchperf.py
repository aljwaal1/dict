from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

if "import 'dart:async';" not in s:
    s = s.replace("import 'dart:convert';\n", "import 'dart:async';\nimport 'dart:convert';\n", 1)

s = s.replace("const appVersion = '3.4.6';", "const appVersion = '3.4.7';")

old = '''class _SmartSearchPageState extends State<SmartSearchPage> {\n  final controller = TextEditingController();\n  String query = '';\n\n  @override\n  void dispose() {\n    controller.dispose();\n    super.dispose();\n  }'''
new = '''class _SmartSearchPageState extends State<SmartSearchPage> {\n  final controller = TextEditingController();\n  Timer? _searchDebounce;\n  String query = '';\n\n  void _queueSearch(String value) {\n    _searchDebounce?.cancel();\n    _searchDebounce = Timer(const Duration(milliseconds: 110), () {\n      if (!mounted || value == query) return;\n      setState(() => query = value);\n    });\n  }\n\n  @override\n  void dispose() {\n    _searchDebounce?.cancel();\n    controller.dispose();\n    super.dispose();\n  }'''
if old not in s:
    raise SystemExit('SmartSearch state anchor not found')
s = s.replace(old, new, 1)

old_change = "            onChanged: (v) => setState(() => query = v),"
new_change = "            onChanged: _queueSearch,"
if old_change not in s:
    raise SystemExit('Search onChanged anchor not found')
s = s.replace(old_change, new_change, 1)

old_clear = "                onPressed: () { controller.clear(); setState(() => query = ''); },"
new_clear = "                onPressed: () { _searchDebounce?.cancel(); controller.clear(); if (query.isNotEmpty) setState(() => query = ''); },"
if old_clear not in s:
    raise SystemExit('Search clear anchor not found')
s = s.replace(old_clear, new_clear, 1)

p.write_text(s, encoding='utf-8')

pub = Path('pubspec.yaml')
ps = pub.read_text(encoding='utf-8')
ps = re.sub(r'^version:\s*3\.4\.6\+35$', 'version: 3.4.7+36', ps, flags=re.M)
pub.write_text(ps, encoding='utf-8')
print('Easy English AI v3.4.7 search performance patch applied')
