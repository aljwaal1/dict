from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')
s = s.replace("const appVersion = '3.2.2';", "const appVersion = '3.2.3';", 1)
s = s.replace("const appVersion = '3.2.1';", "const appVersion = '3.2.3';", 1)
p.write_text(s, encoding='utf-8')
print('Jordan v3.2.3 release patch applied')
