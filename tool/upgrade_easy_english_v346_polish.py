from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

s = s.replace("import 'dart:typed_data';\n", "")
s = s.replace("const appVersion = '3.4.5';", "const appVersion = '3.4.6';")
s = s.replace('QAMOOSI_V340_LEARNING_UX', 'qamoosiV340LearningUx')

# Theme polish: quieter surfaces, tighter hierarchy, consistent components.
s = s.replace("const seed = Color(0xff1769e0);", "const seed = Color(0xff2563eb);")
s = s.replace("scaffoldBackgroundColor: const Color(0xfff7f9fc),", "scaffoldBackgroundColor: const Color(0xfff6f8fc),\n        visualDensity: VisualDensity.standard,")
s = s.replace("borderRadius: BorderRadius.circular(20),\n            side: const BorderSide(color: Color(0xffe3ecfb)),", "borderRadius: BorderRadius.circular(18),\n            side: const BorderSide(color: Color(0xffe5eaf2)),")
s = s.replace("margin: const EdgeInsets.symmetric(vertical: 6),", "margin: const EdgeInsets.symmetric(vertical: 5),")
s = s.replace("height: 68,\n          backgroundColor: Colors.white,\n          indicatorColor: const Color(0xffdbeafe),\n          elevation: 1,", "height: 64,\n          backgroundColor: Colors.white,\n          indicatorColor: const Color(0xffdbeafe),\n          elevation: 0,")
anchor = "        navigationBarTheme: NavigationBarThemeData(\n          height: 64,\n          backgroundColor: Colors.white,\n          indicatorColor: const Color(0xffdbeafe),\n          elevation: 0,\n          labelTextStyle: const WidgetStatePropertyAll(TextStyle(fontSize: 12.5, fontWeight: FontWeight.w800)),\n        ),"
if anchor in s:
    s = s.replace(anchor, anchor + "\n        dividerTheme: const DividerThemeData(color: Color(0xffe8edf5), thickness: 1, space: 1),\n        snackBarTheme: SnackBarThemeData(behavior: SnackBarBehavior.floating, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))),\n        dialogTheme: DialogThemeData(backgroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22))),\n        bottomSheetTheme: const BottomSheetThemeData(backgroundColor: Colors.white, showDragHandle: true),\n        listTileTheme: const ListTileThemeData(iconColor: Color(0xff2563eb), textColor: Color(0xff172033)),")
else:
    raise SystemExit('navigationBarTheme anchor not found')

# Remove the artificial silent TTS warm-up delay. First tap now configures and speaks immediately.
old_tts = '''  Future<bool> _prepareTts() async {\n    if (_ttsWarmed && ttsReady) return true;\n    final running = _ttsPreparing;\n    if (running != null) return running;\n    final future = () async {\n      if (!ttsReady && !await _configureTts()) return false;\n      try {\n        await tts.setVolume(0.0);\n        await tts.speak('ready');\n        await Future.delayed(const Duration(milliseconds: 520));\n        await tts.stop();\n        await tts.setVolume(1.0);\n        await Future.delayed(const Duration(milliseconds: 80));\n        _ttsWarmed = true;\n        return true;\n      } catch (_) {\n        try { await tts.setVolume(1.0); } catch (_) {}\n        _ttsWarmed = true;\n        return ttsReady;\n      }\n    }();\n    _ttsPreparing = future;\n    final ok = await future;\n    _ttsPreparing = null;\n    return ok;\n  }'''
new_tts = '''  Future<bool> _prepareTts() async {\n    if (_ttsWarmed && ttsReady) return true;\n    final running = _ttsPreparing;\n    if (running != null) return running;\n    final future = () async {\n      final ok = ttsReady || await _configureTts();\n      if (ok) _ttsWarmed = true;\n      return ok;\n    }();\n    _ttsPreparing = future;\n    final ok = await future;\n    _ttsPreparing = null;\n    return ok;\n  }'''
if old_tts not in s:
    raise SystemExit('TTS warmup block not found')
s = s.replace(old_tts, new_tts)

# Moving between flash cards should not rewrite all progress values or rebuild the app.
s = s.replace("  Future<void> saveLastIndex(String grade, int index) async {\n    lastIndexByGrade[grade] = index;\n    await saveProgress();\n  }", "  Future<void> saveLastIndex(String grade, int index) async {\n    lastIndexByGrade[grade] = index;\n    await prefs.setString('$pkey.lastIndex', jsonEncode(lastIndexByGrade));\n  }")

# Avoid repeated grade filtering for one index lookup.
s = s.replace("  int lastIndex(String g) => byGrade(g).isEmpty ? 0 : (lastIndexByGrade[g] ?? 0).clamp(0, byGrade(g).length - 1);", "  int lastIndex(String g) {\n    final list = byGrade(g);\n    return list.isEmpty ? 0 : (lastIndexByGrade[g] ?? 0).clamp(0, list.length - 1);\n  }")

# Dead helper reported by analyzer.
s = re.sub(r"\n  String _cellText\(dynamic value\) \{\n    if \(value == null\) return '';\n    return value\.toString\(\)\.trim\(\);\n  \}\n", "\n", s)

# Cleaner first-run presentation.
s = s.replace("width: 108,\n                    height: 108,", "width: 88,\n                    height: 88,")
s = s.replace("borderRadius: BorderRadius.circular(32),", "borderRadius: BorderRadius.circular(26),", 1)
s = s.replace("child: Icon(Icons.auto_awesome_rounded, size: 58,", "child: Icon(Icons.auto_awesome_rounded, size: 46,")
s = s.replace("const SizedBox(height: 24),\n                  const Text('Easy English AI'", "const SizedBox(height: 18),\n                  const Text('Easy English AI'")
s = s.replace("style: TextStyle(fontSize: 29, fontWeight: FontWeight.w900)", "style: TextStyle(fontSize: 27, fontWeight: FontWeight.w900, letterSpacing: -.4)")
s = s.replace("LinearProgressIndicator(value: bootProgress.clamp(0, 1), minHeight: 10)", "LinearProgressIndicator(value: bootProgress.clamp(0, 1), minHeight: 7)")
s = s.replace("'يستخرج الكلمات التعليمية، ينظف الضوضاء، ثم يستخدم التعلم الآلي لترجمة الكلمات والجمل على جهازك.'", "'يستخرج كلمات الكتاب، ينظف الضوضاء، ثم يجهز المعاني والجمل والترجمة بطريقة واضحة.'")

# More expressive selected/unselected bottom navigation without changing destinations.
old_nav = '''          NavigationDestination(icon: Icon(Icons.home_rounded), label: 'الرئيسية'),\n          NavigationDestination(icon: Icon(Icons.search_rounded), label: 'AI بحث'),\n          NavigationDestination(icon: Icon(Icons.auto_stories_rounded), label: 'الصفوف'),\n          NavigationDestination(icon: Icon(Icons.extension_rounded), label: 'تدريب'),\n          NavigationDestination(icon: Icon(Icons.grid_view_rounded), label: 'المزيد'),'''
new_nav = '''          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home_rounded), label: 'الرئيسية'),\n          NavigationDestination(icon: Icon(Icons.search_outlined), selectedIcon: Icon(Icons.search_rounded), label: 'AI بحث'),\n          NavigationDestination(icon: Icon(Icons.auto_stories_outlined), selectedIcon: Icon(Icons.auto_stories_rounded), label: 'الصفوف'),\n          NavigationDestination(icon: Icon(Icons.extension_outlined), selectedIcon: Icon(Icons.extension_rounded), label: 'تدريب'),\n          NavigationDestination(icon: Icon(Icons.grid_view_outlined), selectedIcon: Icon(Icons.grid_view_rounded), label: 'المزيد'),'''
if old_nav not in s:
    raise SystemExit('navigation destinations block not found')
s = s.replace(old_nav, new_nav)

p.write_text(s, encoding='utf-8')

pub = Path('pubspec.yaml')
ps = pub.read_text(encoding='utf-8')
ps = re.sub(r'^version:\s*3\.4\.5\+34$', 'version: 3.4.6+35', ps, flags=re.M)
pub.write_text(ps, encoding='utf-8')
print('Easy English AI v3.4.6 final polish applied')
