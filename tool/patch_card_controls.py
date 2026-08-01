from pathlib import Path

path = Path('lib/main.dart')
text = path.read_text(encoding='utf-8')

start = text.find('class WordCardPage extends StatefulWidget')
end = text.find('\nvoid push(BuildContext context, Widget page)', start)

if start != -1 and end != -1:
    replacement = r'''class WordCardPage extends StatefulWidget {
  final Store store;
  final WordItem word;
  const WordCardPage({super.key, required this.store, required this.word});

  @override
  State<WordCardPage> createState() => _WordCardPageState();
}

class _WordCardPageState extends State<WordCardPage> {
  bool showMeaning = false;
  bool showExample = false;

  @override
  Widget build(BuildContext context) {
    final word = widget.word;
    final hasExample = word.exampleEn.isNotEmpty || word.exampleAr.isNotEmpty;

    return Scaffold(
      appBar: AppBar(title: const Text('بطاقة الكلمة')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(18),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(22, 34, 22, 28),
                child: Column(
                  children: [
                    Text(
                      word.en,
                      textDirection: TextDirection.ltr,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 43, fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      gradeName(word.grade),
                      style: const TextStyle(color: Color(0xff6f7d94)),
                    ),
                    const SizedBox(height: 26),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton.tonalIcon(
                        onPressed: () => widget.store.speak(word.en),
                        icon: const Icon(Icons.volume_up_rounded),
                        label: const Text('لفظ الكلمة'),
                      ),
                    ),
                    const SizedBox(height: 12),
                    if (hasExample)
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed: () => setState(() => showExample = !showExample),
                          icon: Icon(showExample ? Icons.expand_less_rounded : Icons.format_quote_rounded),
                          label: Text(showExample ? 'إخفاء مثال الجملة' : 'مثال جملة'),
                        ),
                      ),
                    if (hasExample) const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton.icon(
                        onPressed: () => setState(() => showMeaning = !showMeaning),
                        icon: Icon(showMeaning ? Icons.visibility_off_rounded : Icons.translate_rounded),
                        label: Text(showMeaning ? 'إخفاء المعنى' : 'إظهار المعنى'),
                      ),
                    ),
                    AnimatedSize(
                      duration: const Duration(milliseconds: 220),
                      child: !showExample
                          ? const SizedBox.shrink()
                          : Container(
                              width: double.infinity,
                              margin: const EdgeInsets.only(top: 20),
                              padding: const EdgeInsets.all(18),
                              decoration: BoxDecoration(
                                color: Theme.of(context).colorScheme.secondaryContainer.withValues(alpha: .45),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Column(
                                children: [
                                  if (word.exampleEn.isNotEmpty)
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
                                        IconButton.filledTonal(
                                          tooltip: 'لفظ الجملة',
                                          icon: const Icon(Icons.volume_up_rounded),
                                          onPressed: () => widget.store.speak(word.exampleEn),
                                        ),
                                      ],
                                    ),
                                  if (word.exampleAr.isNotEmpty)
                                    Padding(
                                      padding: EdgeInsets.only(top: word.exampleEn.isEmpty ? 0 : 10),
                                      child: Text(
                                        word.exampleAr,
                                        textAlign: TextAlign.center,
                                        style: const TextStyle(fontSize: 17),
                                      ),
                                    ),
                                ],
                              ),
                            ),
                    ),
                    AnimatedSize(
                      duration: const Duration(milliseconds: 220),
                      child: !showMeaning
                          ? const SizedBox.shrink()
                          : Container(
                              width: double.infinity,
                              margin: const EdgeInsets.only(top: 20),
                              padding: const EdgeInsets.all(22),
                              decoration: BoxDecoration(
                                color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: .55),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Text(
                                word.ar,
                                textAlign: TextAlign.center,
                                style: const TextStyle(fontSize: 31, fontWeight: FontWeight.w900),
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
print('Separated word pronunciation, example and meaning controls')
