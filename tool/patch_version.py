from pathlib import Path
import re

path = Path('lib/main.dart')
text = path.read_text(encoding='utf-8')
text = re.sub(r"const appVersion = '[^']+';", "const appVersion = '2.0.2';", text, count=1)
path.write_text(text, encoding='utf-8')
print('Updated visible app version to 2.0.2')
