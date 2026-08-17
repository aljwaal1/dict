from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

# Add a reusable pronunciation helper once. Future Jordan curriculum screens
# should use this for every English word, phrase, sentence and extracted result.
anchor = "class SectionTitle extends StatelessWidget {"
helper = r'''class EnglishSpeakButton extends StatelessWidget {
  final Store store;
  final String text;
  final String label;
  final bool compact;

  const EnglishSpeakButton({
    super.key,
    required this.store,
    required this.text,
    this.label = 'نطق',
    this.compact = false,
  });

  Future<void> _speak(BuildContext context) async {
    final ok = await store.speak(text);
    if (!ok && context.mounted) {
      snack(context, store.sound
          ? 'تعذر تشغيل النطق الإنجليزي. تأكد من وجود صوت إنجليزي في إعدادات الهاتف'
          : 'فعّل الأصوات والنطق من الإعدادات أولاً');
    }
  }

  @override
  Widget build(BuildContext context) {
    if (compact) {
      return IconButton(
        tooltip: label,
        icon: const Icon(Icons.volume_up_rounded),
        onPressed: text.trim().isEmpty ? null : () => _speak(context),
      );
    }
    return FilledButton.tonalIcon(
      onPressed: text.trim().isEmpty ? null : () => _speak(context),
      icon: const Icon(Icons.volume_up_rounded),
      label: Text(label),
    );
  }
}

'''
if 'class EnglishSpeakButton extends StatelessWidget' not in s:
    if anchor not in s:
        raise SystemExit('SectionTitle anchor not found')
    s = s.replace(anchor, helper + anchor, 1)

# Normalize existing list pronunciation actions to the shared helper where safe.
s = s.replace(
    "trailing: IconButton(tooltip: 'نطق الكلمة', icon: const Icon(Icons.volume_up_rounded), onPressed: () => widget.store.speak(w.en)),",
    "trailing: EnglishSpeakButton(store: widget.store, text: w.en, label: 'نطق الكلمة', compact: true),",
)
s = s.replace(
    "IconButton(\n                  tooltip: 'نطق الكلمة',\n                  icon: const Icon(Icons.volume_up_rounded),\n                  onPressed: () => store.speak(w.en),\n                ),",
    "EnglishSpeakButton(store: store, text: w.en, label: 'نطق الكلمة', compact: true),",
)
s = s.replace(
    "trailing: IconButton(\n        tooltip: 'نطق الكلمة',\n        icon: const Icon(Icons.volume_up_rounded),\n        onPressed: () => store.speak(list[i].en),\n      ),",
    "trailing: EnglishSpeakButton(store: store, text: list[i].en, label: 'نطق الكلمة', compact: true),",
)
s = s.replace(
    "trailing: IconButton(\n                      tooltip: 'نطق الجملة',\n                      icon: const Icon(Icons.volume_up_rounded),\n                      onPressed: () => store.speak(sentence),\n                    ),",
    "trailing: EnglishSpeakButton(store: store, text: sentence, label: 'نطق الجملة', compact: true),",
)

# Explicit button remains visible in quiz and learning cards.
s = s.replace(
    "FilledButton.tonalIcon(onPressed: () => widget.store.speak(w.en), icon: const Icon(Icons.volume_up_rounded), label: const Text('اسمع الكلمة'))",
    "EnglishSpeakButton(store: widget.store, text: w.en, label: 'اسمع الكلمة')",
)

p.write_text(s, encoding='utf-8')
print('Applied universal pronunciation policy for Jordan school dictionary')
