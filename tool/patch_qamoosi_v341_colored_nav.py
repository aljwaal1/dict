from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

if 'QAMOOSI_V341_COLORED_NAV' in s:
    print('v3.4.1 colored navigation already applied')
    raise SystemExit(0)

old = """      bottomNavigationBar: NavigationBar(\n        selectedIndex: index,\n        onDestinationSelected: (v) => setState(() => index = v),\n        destinations: const [\n          NavigationDestination(icon: Icon(Icons.home_rounded), label: 'الرئيسية'),\n          NavigationDestination(icon: Icon(Icons.search_rounded), label: 'البحث'),\n          NavigationDestination(icon: Icon(Icons.auto_stories_rounded), label: 'المنهاج'),\n          NavigationDestination(icon: Icon(Icons.extension_rounded), label: 'التعلم'),\n          NavigationDestination(icon: Icon(Icons.grid_view_rounded), label: 'المزيد'),\n        ],\n      ),"""

new = """      bottomNavigationBar: NavigationBar(\n        selectedIndex: index,\n        onDestinationSelected: (v) => setState(() => index = v),\n        destinations: const [\n          NavigationDestination(\n            icon: Icon(Icons.home_rounded, color: Color(0xff2563eb)),\n            selectedIcon: _QamoosiSelectedNavIcon(icon: Icons.home_rounded, color: Color(0xff2563eb), soft: Color(0xffdbeafe)),\n            label: 'الرئيسية',\n          ),\n          NavigationDestination(\n            icon: Icon(Icons.search_rounded, color: Color(0xff7c3aed)),\n            selectedIcon: _QamoosiSelectedNavIcon(icon: Icons.search_rounded, color: Color(0xff7c3aed), soft: Color(0xffede9fe)),\n            label: 'البحث',\n          ),\n          NavigationDestination(\n            icon: Icon(Icons.auto_stories_rounded, color: Color(0xff0891b2)),\n            selectedIcon: _QamoosiSelectedNavIcon(icon: Icons.auto_stories_rounded, color: Color(0xff0891b2), soft: Color(0xffcffafe)),\n            label: 'المنهاج',\n          ),\n          NavigationDestination(\n            icon: Icon(Icons.extension_rounded, color: Color(0xffea580c)),\n            selectedIcon: _QamoosiSelectedNavIcon(icon: Icons.extension_rounded, color: Color(0xffea580c), soft: Color(0xffffedd5)),\n            label: 'التعلم',\n          ),\n          NavigationDestination(\n            icon: Icon(Icons.grid_view_rounded, color: Color(0xffdb2777)),\n            selectedIcon: _QamoosiSelectedNavIcon(icon: Icons.grid_view_rounded, color: Color(0xffdb2777), soft: Color(0xffffe4e6)),\n            label: 'المزيد',\n          ),\n        ],\n      ),"""

if old not in s:
    raise SystemExit('Bottom NavigationBar block not found')
s = s.replace(old, new, 1)

anchor = 'class MainShell extends StatefulWidget {'
idx = s.find(anchor)
if idx < 0:
    raise SystemExit('MainShell anchor not found')
helper = """const QAMOOSI_V341_COLORED_NAV = true;\n\nclass _QamoosiSelectedNavIcon extends StatelessWidget {\n  final IconData icon;\n  final Color color;\n  final Color soft;\n  const _QamoosiSelectedNavIcon({required this.icon, required this.color, required this.soft});\n\n  @override\n  Widget build(BuildContext context) => Container(\n        width: 48,\n        height: 38,\n        decoration: BoxDecoration(\n          color: soft,\n          borderRadius: BorderRadius.circular(14),\n          border: Border.all(color: color.withOpacity(.24)),\n          boxShadow: [BoxShadow(color: color.withOpacity(.16), blurRadius: 10, offset: const Offset(0, 4))],\n        ),\n        alignment: Alignment.center,\n        child: Icon(icon, color: color, size: 27),\n      );\n}\n\n"""
s = s[:idx] + helper + s[idx:]

s = s.replace("          indicatorColor: const Color(0xffdbeafe),", "          indicatorColor: Colors.transparent,", 1)
s = s.replace("          elevation: 2,", "          elevation: 5,\n          shadowColor: const Color(0x220f172a),\n          surfaceTintColor: Colors.white,", 1)
s = s.replace("const appVersion = '3.4.0';", "const appVersion = '3.4.1';", 1)

p.write_text(s, encoding='utf-8')
print('Applied Qamoosi AI v3.4.1 vivid colored Android navigation')
