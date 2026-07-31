from pathlib import Path
import re

path = Path('lib/main.dart')
text = path.read_text(encoding='utf-8')

# Stronger, clearer English TTS setup.
text = text.replace(
"""    await tts.setLanguage('en-US');
    await tts.setSpeechRate(.42);""",
"""    await tts.setLanguage('en-US');
    await tts.setSpeechRate(.38);
    await tts.setPitch(1.0);
    await tts.setVolume(1.0);
    await tts.awaitSpeakCompletion(true);""",
)

text = re.sub(
    r"  Future<void> speak\(String text\) async \{.*?\n  \}",
    """  Future<void> speak(String text) async {
    final value = text.trim();
    if (!sound || value.isEmpty) return;
    try {
      SystemSound.play(SystemSoundType.click);
      await tts.stop();
      await tts.setLanguage('en-US');
      await tts.setSpeechRate(.38);
      await tts.setPitch(1.0);
      await tts.setVolume(1.0);
      await tts.speak(value);
    } catch (_) {
      // Keep the app usable even when the device has no English TTS engine.
    }
  }

  Future<bool> testPronunciation() async {
    if (!sound) return false;
    try {
      final available = await tts.isLanguageAvailable('en-US');
      if (available != true && available != 1) return false;
      await speak('Welcome to my school dictionary');
      return true;
    } catch (_) {
      return false;
    }
  }""",
    text,
    count=1,
    flags=re.S,
)

# Pronunciation button in grade word lists while retaining mastery state.
old_grade = """            trailing: Icon(store.mastered.contains('${w.id}') ? Icons.check_circle : Icons.chevron_left, color: store.mastered.contains('${w.id}') ? Colors.green : null),
            onTap: () async { await store.saveLastIndex(grade, i); if (context.mounted) showWord(context, store, w); },"""
new_grade = """            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  tooltip: 'نطق الكلمة',
                  icon: const Icon(Icons.volume_up_rounded),
                  onPressed: () => store.speak(w.en),
                ),
                Icon(
                  store.mastered.contains('${w.id}') ? Icons.check_circle : Icons.chevron_left,
                  color: store.mastered.contains('${w.id}') ? Colors.green : null,
                ),
              ],
            ),
            onTap: () async {
              await store.saveLastIndex(grade, i);
              if (context.mounted) showWord(context, store, w);
            },"""
text = text.replace(old_grade, new_grade)

# Pronunciation button in difficult words.
text = text.replace(
"""itemBuilder: (_, i) => Card(child: ListTile(title: Text(list[i].en, textDirection: TextDirection.ltr), subtitle: Text(list[i].ar), onTap: () => showWord(context, store, list[i]))))""",
"""itemBuilder: (_, i) => Card(child: ListTile(
      title: Text(list[i].en, textDirection: TextDirection.ltr),
      subtitle: Text(list[i].ar),
      trailing: IconButton(
        tooltip: 'نطق الكلمة',
        icon: const Icon(Icons.volume_up_rounded),
        onPressed: () => store.speak(list[i].en),
      ),
      onTap: () => showWord(context, store, list[i]),
    )))""",
)

# Pronunciation test inside settings.
settings_anchor = """          Card(child: SwitchListTile(secondary: const Icon(Icons.volume_up_outlined), title: const Text('الأصوات والنطق'), subtitle: const Text('صوت الضغط ونطق الكلمات الإنجليزية'), value: store.sound, onChanged: store.setSound)),"""
settings_replacement = settings_anchor + """
          SettingsTile(
            icon: Icons.record_voice_over_rounded,
            title: 'تجربة النطق الإنجليزي',
            subtitle: 'تشغيل جملة تجريبية والتأكد من محرك الصوت',
            onTap: () async {
              final ok = await store.testPronunciation();
              if (!context.mounted) return;
              snack(
                context,
                ok
                    ? 'تم تشغيل تجربة النطق بنجاح'
                    : store.sound
                        ? 'محرك النطق الإنجليزي غير متاح على الجهاز'
                        : 'فعّل الأصوات والنطق أولاً',
              );
            },
          ),"""
if "تجربة النطق الإنجليزي" not in text:
    text = text.replace(settings_anchor, settings_replacement)

# Replace the small bottom sheet with a full-page, readable word card.
start = text.find('void showWord(BuildContext context, Store store, WordItem w) {')
end = text.find('\nvoid push(BuildContext context, Widget page)', start)
if start != -1 and end != -1:
    replacement = r'''void showWord(BuildContext context, Store store, WordItem w) {
  push(context, WordCardPage(store: store, word: w));
}

class WordCardPage extends StatefulWidget {
  final Store store;
  final WordItem word;
  const WordCardPage({super.key, required this.store, required this.word});

  @override
  State<WordCardPage> createState() => _WordCardPageState();
}

class _WordCardPageState extends State<WordCardPage> {
  bool reveal = false;

  @override
  Widget build(BuildContext context) {
    final word = widget.word;
    return Scaffold(
      appBar: AppBar(title: const Text('بطاقة الكلمة')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(18),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(24, 34, 24, 30),
                child: Column(
                  children: [
                    Text(
                      word.en,
                      textDirection: TextDirection.ltr,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 42, fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 14),
                    FilledButton.tonalIcon(
                      onPressed: () => widget.store.speak(word.en),
                      icon: const Icon(Icons.volume_up_rounded),
                      label: const Text('استمع إلى النطق'),
                    ),
                    const SizedBox(height: 24),
                    FilledButton.icon(
                      onPressed: () => setState(() => reveal = !reveal),
                      icon: Icon(reveal ? Icons.visibility_off : Icons.translate_rounded),
                      label: Text(reveal ? 'إخفاء المعنى' : 'إظهار المعنى'),
                    ),
                    AnimatedSize(
                      duration: const Duration(milliseconds: 220),
                      child: !reveal
                          ? const SizedBox.shrink()
                          : Padding(
                              padding: const EdgeInsets.only(top: 28),
                              child: Column(
                                children: [
                                  Text(
                                    word.ar,
                                    textAlign: TextAlign.center,
                                    style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w900),
                                  ),
                                  if (word.exampleEn.isNotEmpty) ...[
                                    const SizedBox(height: 26),
                                    Row(
                                      children: [
                                        Expanded(
                                          child: Text(
                                            word.exampleEn,
                                            textDirection: TextDirection.ltr,
                                            textAlign: TextAlign.center,
                                            style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w700),
                                          ),
                                        ),
                                        IconButton(
                                          tooltip: 'نطق الجملة',
                                          icon: const Icon(Icons.volume_up_rounded),
                                          onPressed: () => widget.store.speak(word.exampleEn),
                                        ),
                                      ],
                                    ),
                                  ],
                                  if (word.exampleAr.isNotEmpty)
                                    Padding(
                                      padding: const EdgeInsets.only(top: 10),
                                      child: Text(
                                        word.exampleAr,
                                        textAlign: TextAlign.center,
                                        style: const TextStyle(fontSize: 17, color: Color(0xff6f7d94)),
                                      ),
                                    ),
                                ],
                              ),
                            ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
'''
    text = text[:start] + replacement + text[end:]

path.write_text(text, encoding='utf-8')
print('Applied pronunciation and full word-card improvements')
