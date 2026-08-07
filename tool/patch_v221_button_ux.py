from pathlib import Path
import re

p = Path('lib/main.dart')
text = p.read_text(encoding='utf-8')

# Version
text = re.sub(r"const appVersion = '[^']+';", "const appVersion = '2.2.1';", text, count=1)

# Global button system: larger touch targets, consistent hierarchy and rounded geometry.
needle = """        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: BorderSide.none),
          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color: Color(0xffe3ecfb))),
          focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color: seed, width: 1.6)),
        ),"""
replacement = needle + """
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            minimumSize: const Size(64, 52),
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
            tapTargetSize: MaterialTapTargetSize.padded,
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            minimumSize: const Size(64, 52),
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            side: const BorderSide(color: Color(0xffcbd9ee)),
            textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
            tapTargetSize: MaterialTapTargetSize.padded,
          ),
        ),
        textButtonTheme: TextButtonThemeData(
          style: TextButton.styleFrom(
            minimumSize: const Size(48, 48),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
            tapTargetSize: MaterialTapTargetSize.padded,
          ),
        ),
        iconButtonTheme: IconButtonThemeData(
          style: IconButton.styleFrom(
            minimumSize: const Size(48, 48),
            padding: const EdgeInsets.all(12),
            tapTargetSize: MaterialTapTargetSize.padded,
          ),
        ),
        navigationBarTheme: const NavigationBarThemeData(
          height: 72,
          labelTextStyle: WidgetStatePropertyAll(TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700)),
        ),"""
if needle in text and 'filledButtonTheme:' not in text:
    text = text.replace(needle, replacement, 1)

# Make pronunciation icon in dictionary self-explanatory via tooltip.
text = text.replace(
    "trailing: IconButton(icon: const Icon(Icons.volume_up_rounded), onPressed: () => widget.store.speak(w.en)),",
    "trailing: IconButton(tooltip: 'نطق الكلمة', icon: const Icon(Icons.volume_up_rounded), onPressed: () => widget.store.speak(w.en)),"
)

# Quiz: replace icon-only audio affordance with a labeled, easy-to-hit control.
old_quiz = "Card(child: Padding(padding: const EdgeInsets.all(28), child: Column(children: [Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 35, fontWeight: FontWeight.w900)), IconButton(icon: const Icon(Icons.volume_up), onPressed: () => widget.store.speak(w.en))])))"
new_quiz = "Card(child: Padding(padding: const EdgeInsets.all(28), child: Column(children: [Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 35, fontWeight: FontWeight.w900)), const SizedBox(height: 14), FilledButton.tonalIcon(onPressed: () => widget.store.speak(w.en), icon: const Icon(Icons.volume_up_rounded), label: const Text('اسمع الكلمة'))])))"
text = text.replace(old_quiz, new_quiz)

# Restore dialog: merge is the safe primary action; replacement is explicitly destructive.
old_actions = "actions: [TextButton(onPressed: () => Navigator.pop(context, null), child: const Text('إلغاء')), OutlinedButton(onPressed: () => Navigator.pop(context, false), child: const Text('دمج')), FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('استبدال'))],"
new_actions = "actions: [TextButton(onPressed: () => Navigator.pop(context, null), child: const Text('إلغاء')), FilledButton(onPressed: () => Navigator.pop(context, false), child: const Text('دمج وحفظ الحالي')), FilledButton(style: FilledButton.styleFrom(backgroundColor: Theme.of(context).colorScheme.error, foregroundColor: Theme.of(context).colorScheme.onError), onPressed: () => Navigator.pop(context, true), child: const Text('استبدال وحذف الحالي'))],"
text = text.replace(old_actions, new_actions)

# Add a clearer tooltip to the search clear button.
text = text.replace(
    "IconButton(icon: const Icon(Icons.close), onPressed: () => setState(() => widget.store.query = ''))",
    "IconButton(tooltip: 'مسح البحث', icon: const Icon(Icons.close), onPressed: () => setState(() => widget.store.query = ''))"
)

p.write_text(text, encoding='utf-8')
