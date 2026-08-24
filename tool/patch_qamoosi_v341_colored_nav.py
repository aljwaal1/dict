from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

if 'QAMOOSI_V341_COLORED_NAV' in s:
    print('v3.4.1 colored navigation already applied')
    raise SystemExit(0)

# Match the first bottom NavigationBar regardless of whitespace/format changes
pattern = re.compile(
    r"bottomNavigationBar:\s*NavigationBar\((?P<body>.*?)\n\s*\),",
    re.S,
)
m = pattern.search(s)
if not m:
    raise SystemExit('Bottom NavigationBar not found')
block = m.group(0)

# Keep selectedIndex/onDestinationSelected from the current block and replace destinations only.
head_match = re.search(r"bottomNavigationBar:\s*NavigationBar\((.*?)destinations:\s*(?:const\s*)?\[", block, re.S)
if not head_match:
    raise SystemExit('NavigationBar destinations not found')
head = head_match.group(1)
new_block = """bottomNavigationBar: NavigationBar(
%s        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_rounded, color: Color(0xff2563eb)),
            selectedIcon: _QamoosiSelectedNavIcon(icon: Icons.home_rounded, color: Color(0xff2563eb), soft: Color(0xffdbeafe)),
            label: 'الرئيسية',
          ),
          NavigationDestination(
            icon: Icon(Icons.search_rounded, color: Color(0xff7c3aed)),
            selectedIcon: _QamoosiSelectedNavIcon(icon: Icons.search_rounded, color: Color(0xff7c3aed), soft: Color(0xffede9fe)),
            label: 'البحث',
          ),
          NavigationDestination(
            icon: Icon(Icons.auto_stories_rounded, color: Color(0xff0891b2)),
            selectedIcon: _QamoosiSelectedNavIcon(icon: Icons.auto_stories_rounded, color: Color(0xff0891b2), soft: Color(0xffcffafe)),
            label: 'المنهاج',
          ),
          NavigationDestination(
            icon: Icon(Icons.extension_rounded, color: Color(0xffea580c)),
            selectedIcon: _QamoosiSelectedNavIcon(icon: Icons.extension_rounded, color: Color(0xffea580c), soft: Color(0xffffedd5)),
            label: 'التعلم',
          ),
          NavigationDestination(
            icon: Icon(Icons.grid_view_rounded, color: Color(0xffdb2777)),
            selectedIcon: _QamoosiSelectedNavIcon(icon: Icons.grid_view_rounded, color: Color(0xffdb2777), soft: Color(0xffffe4e6)),
            label: 'المزيد',
          ),
        ],
      ),""" % head
s = s[:m.start()] + new_block + s[m.end():]

anchor = 'class MainShell extends StatefulWidget {'
idx = s.find(anchor)
if idx < 0:
    raise SystemExit('MainShell anchor not found')
helper = """const QAMOOSI_V341_COLORED_NAV = true;

class _QamoosiSelectedNavIcon extends StatelessWidget {
  final IconData icon;
  final Color color;
  final Color soft;
  const _QamoosiSelectedNavIcon({required this.icon, required this.color, required this.soft});

  @override
  Widget build(BuildContext context) => Container(
        width: 48,
        height: 38,
        decoration: BoxDecoration(
          color: soft,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withOpacity(.24)),
          boxShadow: [BoxShadow(color: color.withOpacity(.16), blurRadius: 10, offset: const Offset(0, 4))],
        ),
        alignment: Alignment.center,
        child: Icon(icon, color: color, size: 27),
      );
}

"""
s = s[:idx] + helper + s[idx:]
s = s.replace("const appVersion = '3.4.0';", "const appVersion = '3.4.1';", 1)

p.write_text(s, encoding='utf-8')
print('Applied Qamoosi AI v3.4.1 vivid colored Android navigation')
