from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')
if "QAMOOSI_V340_LEARNING_UX" in s:
    print('v3.4 learning UX already applied')
    raise SystemExit(0)

s = s.replace("const appVersion = '3.3.0';", "const appVersion = '3.4.0';\nconst QAMOOSI_V340_LEARNING_UX = true;")

s = s.replace("  Set<String> difficult = {};\n  Map<String, int> wrongCounts = {};", "  Set<String> difficult = {};\n  Set<String> studied = {};\n  Map<String, int> wrongCounts = {};")
s = s.replace("    difficult = (prefs.getStringList('$pkey.difficult') ?? []).toSet();\n    wrongCounts", "    difficult = (prefs.getStringList('$pkey.difficult') ?? []).toSet();\n    studied = (prefs.getStringList('$pkey.studied') ?? []).toSet();\n    wrongCounts")
s = s.replace("      prefs.setStringList('$pkey.difficult', difficult.toList()),\n      prefs.setString('$pkey.wrongCounts'", "      prefs.setStringList('$pkey.difficult', difficult.toList()),\n      prefs.setStringList('$pkey.studied', studied.toList()),\n      prefs.setString('$pkey.wrongCounts'")

tts_start = s.find("  Future<bool> _configureTts() async {")
tts_end = s.find("  Future<bool> testPronunciation() async {", tts_start)
if tts_start < 0 or tts_end < 0:
    raise SystemExit('TTS block not found')
new_tts = r'''  bool _ttsWarmed = false;
  Future<bool>? _ttsPreparing;

  Future<bool> _configureTts() async {
    try {
      await tts.awaitSpeakCompletion(false);
      await tts.setSpeechRate(.42);
      await tts.setPitch(1.0);
      await tts.setVolume(1.0);
      const candidates = ['en-US', 'en-GB', 'en-AU', 'en'];
      for (final language in candidates) {
        try {
          final result = await tts.setLanguage(language);
          if (result == 1 || result == true || result == null) {
            ttsLanguage = language;
            ttsReady = true;
            return true;
          }
        } catch (_) {}
      }
      ttsReady = false;
      return false;
    } catch (_) {
      ttsReady = false;
      return false;
    }
  }

  Future<bool> _prepareTts() async {
    if (_ttsWarmed && ttsReady) return true;
    final running = _ttsPreparing;
    if (running != null) return running;
    final future = () async {
      if (!ttsReady && !await _configureTts()) return false;
      try {
        await tts.setVolume(0.0);
        await tts.speak('ready');
        await Future.delayed(const Duration(milliseconds: 520));
        await tts.stop();
        await tts.setVolume(1.0);
        await Future.delayed(const Duration(milliseconds: 80));
        _ttsWarmed = true;
        return true;
      } catch (_) {
        try { await tts.setVolume(1.0); } catch (_) {}
        _ttsWarmed = true;
        return ttsReady;
      }
    }();
    _ttsPreparing = future;
    final ok = await future;
    _ttsPreparing = null;
    return ok;
  }

  Future<bool> speak(String text) async {
    final value = text.trim();
    if (!sound || value.isEmpty) return false;
    try {
      if (!await _prepareTts()) return false;
      await tts.stop();
      await tts.setLanguage(ttsLanguage);
      await tts.setSpeechRate(.42);
      await tts.setPitch(1.0);
      await tts.setVolume(1.0);
      final result = await tts.speak(value);
      return result == 1 || result == true || result == null;
    } catch (_) {
      ttsReady = false;
      _ttsWarmed = false;
      if (!await _prepareTts()) return false;
      try {
        await tts.stop();
        await Future.delayed(const Duration(milliseconds: 120));
        final result = await tts.speak(value);
        return result == 1 || result == true || result == null;
      } catch (_) {
        return false;
      }
    }
  }

'''
s = s[:tts_start] + new_tts + s[tts_end:]
s = s.replace("    await _configureTts();\n  }", "    await _configureTts();\n    await _prepareTts();\n  }", 1)

answer_anchor = s.find("  Future<void> answer(WordItem word, bool correct) async {")
if answer_anchor < 0:
    raise SystemExit('answer anchor not found')
helpers = r'''  Future<void> markStudied(WordItem word) async {
    final key = '${word.id}';
    if (studied.add(key)) {
      await prefs.setStringList('$pkey.studied', studied.toList());
      notifyListeners();
    }
  }

  int difficultyScore(WordItem word) {
    final key = '${word.id}';
    var score = (wrongCounts[key] ?? 0) * 10;
    if (difficult.contains(key)) score += 20;
    if (mastered.contains(key)) score -= 12;
    return score;
  }

  Future<void> setReviewState(WordItem word, {required bool masteredNow}) async {
    final key = '${word.id}';
    studied.add(key);
    if (masteredNow) {
      mastered.add(key);
      difficult.remove(key);
    } else {
      difficult.add(key);
      mastered.remove(key);
    }
    await saveProgress();
  }

'''
s = s[:answer_anchor] + helpers + s[answer_anchor:]
s = s.replace("  Future<void> answer(WordItem word, bool correct) async {\n    if (correct) {\n      points += .5;\n      mastered.add('${word.id}');", "  Future<void> answer(WordItem word, bool correct) async {\n    studied.add('${word.id}');\n    if (correct) {\n      points += .5;\n      mastered.add('${word.id}');\n      difficult.remove('${word.id}');")

s = s.replace("        navigationBarTheme: const NavigationBarThemeData(\n          height: 72,\n          labelTextStyle: WidgetStatePropertyAll(TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700)),\n        ),", "        navigationBarTheme: NavigationBarThemeData(\n          height: 72,\n          backgroundColor: Colors.white,\n          indicatorColor: const Color(0xffdbeafe),\n          elevation: 2,\n          labelTextStyle: const WidgetStatePropertyAll(TextStyle(fontSize: 12.5, fontWeight: FontWeight.w800)),\n        ),")

quick_start = s.find('class QuickCard extends StatelessWidget {')
quick_end = s.find('class DictionaryPage extends StatefulWidget {', quick_start)
if quick_start < 0 or quick_end < 0:
    raise SystemExit('QuickCard block not found')
quick = r'''class QuickCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  const QuickCard({super.key, required this.icon, required this.title, required this.subtitle, required this.onTap});

  Color _accent() {
    const colors = [
      Color(0xff2563eb), Color(0xff7c3aed), Color(0xffdb2777),
      Color(0xffea580c), Color(0xff059669), Color(0xff0891b2),
    ];
    return colors[icon.codePoint.abs() % colors.length];
  }

  @override
  Widget build(BuildContext context) {
    final accent = _accent();
    return Card(
      color: Color.alphaBlend(accent.withOpacity(.075), Colors.white),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(24),
        side: BorderSide(color: accent.withOpacity(.20)),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(24),
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(color: accent.withOpacity(.14), borderRadius: BorderRadius.circular(15)),
              child: Icon(icon, color: accent),
            ),
            const SizedBox(height: 14),
            Text(title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),
            const SizedBox(height: 4),
            Text(subtitle, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Color(0xff64748b), height: 1.25)),
          ]),
        ),
      ),
    );
  }
}

'''
s = s[:quick_start] + quick + s[quick_end:]

flash_start = s.find('class FlashCardsPage extends StatefulWidget {')
flash_end = s.find('class QuizSetupPage', flash_start)
if flash_start < 0 or flash_end < 0:
    raise SystemExit('FlashCards block not found')
flash = r'''class FlashCardsPage extends StatefulWidget {
  final Store store;
  const FlashCardsPage({super.key, required this.store});

  @override
  State<FlashCardsPage> createState() => _FlashCardsPageState();
}

class _FlashCardsPageState extends State<FlashCardsPage> {
  String grade = '1';
  int index = 0;
  bool showMeaning = false;
  bool showExample = false;

  @override
  void initState() {
    super.initState();
    index = widget.store.lastIndex(grade);
    WidgetsBinding.instance.addPostFrameCallback((_) => _markCurrent());
  }

  void _markCurrent() {
    final list = widget.store.byGrade(grade);
    if (list.isNotEmpty && index < list.length) widget.store.markStudied(list[index]);
  }

  void move(int delta, int length) {
    if (length == 0) return;
    setState(() {
      index = (index + delta) % length;
      if (index < 0) index += length;
      showMeaning = false;
      showExample = false;
    });
    widget.store.saveLastIndex(grade, index);
    _markCurrent();
  }

  Future<void> pronounce(BuildContext context, String value) async {
    final list = widget.store.byGrade(grade);
    if (list.isNotEmpty && index < list.length) await widget.store.markStudied(list[index]);
    final ok = await widget.store.speak(value);
    if (!ok && context.mounted) snack(context, 'تعذر تشغيل النطق. فعّل محرك تحويل النص إلى كلام الإنجليزي من إعدادات الهاتف');
  }

  Widget _actionButton({required Widget child}) => SizedBox(height: 46, child: child);

  @override
  Widget build(BuildContext context) {
    final list = widget.store.byGrade(grade);
    if (list.isNotEmpty && index >= list.length) index = 0;
    final word = list.isEmpty ? null : list[index];
    final hasExample = word != null && (word.exampleEn.isNotEmpty || word.exampleAr.isNotEmpty);
    return Scaffold(
      appBar: AppBar(title: const Text('البطاقات التعليمية'), toolbarHeight: 52),
      body: Padding(
        padding: const EdgeInsets.fromLTRB(10, 4, 10, 8),
        child: Column(children: [
          SizedBox(
            height: 52,
            child: DropdownButtonFormField<String>(
              initialValue: grade,
              isExpanded: true,
              items: grades.map((g) => DropdownMenuItem(value: g, child: Text(gradeName(g)))).toList(),
              onChanged: (value) {
                setState(() {
                  grade = value ?? '1';
                  index = widget.store.lastIndex(grade);
                  showMeaning = false;
                  showExample = false;
                });
                _markCurrent();
              },
              decoration: const InputDecoration(contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 8)),
            ),
          ),
          const SizedBox(height: 4),
          if (word != null) Text('${index + 1} / ${list.length}', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 13)),
          const SizedBox(height: 4),
          Expanded(
            child: word == null
                ? const Center(child: Text('لا توجد كلمات في هذا الصف'))
                : GestureDetector(
                    onHorizontalDragEnd: (details) {
                      final v = details.primaryVelocity ?? 0;
                      if (v < -100) move(1, list.length);
                      if (v > 100) move(-1, list.length);
                    },
                    child: LayoutBuilder(builder: (context, constraints) {
                      final compact = constraints.maxHeight < 430;
                      final wordSize = compact ? 34.0 : 40.0;
                      final innerWidth = max(240.0, constraints.maxWidth - 24);
                      return Card(
                        margin: EdgeInsets.zero,
                        child: Padding(
                          padding: EdgeInsets.all(compact ? 10 : 14),
                          child: Center(
                            child: FittedBox(
                              fit: BoxFit.scaleDown,
                              alignment: Alignment.center,
                              child: SizedBox(
                                width: innerWidth,
                                child: Column(mainAxisSize: MainAxisSize.min, children: [
                                  Text(word.en, textDirection: TextDirection.ltr, textAlign: TextAlign.center, style: TextStyle(fontSize: wordSize, fontWeight: FontWeight.w900)),
                                  const SizedBox(height: 3),
                                  Text(gradeName(word.grade), style: const TextStyle(fontSize: 12, color: Color(0xff64748b), fontWeight: FontWeight.w700)),
                                  SizedBox(height: compact ? 7 : 10),
                                  SizedBox(width: double.infinity, height: 44, child: FilledButton.tonalIcon(
                                    onPressed: () => pronounce(context, word.en),
                                    icon: const Icon(Icons.volume_up_rounded),
                                    label: const Text('لفظ الكلمة'),
                                  )),
                                  if (hasExample) ...[
                                    const SizedBox(height: 7),
                                    SizedBox(width: double.infinity, height: 44, child: OutlinedButton.icon(
                                      onPressed: () => setState(() => showExample = !showExample),
                                      icon: const Icon(Icons.format_quote_rounded),
                                      label: Text(showExample ? 'إخفاء مثال الجملة' : 'إظهار مثال الجملة'),
                                    )),
                                    if (showExample) Container(
                                      width: double.infinity,
                                      margin: const EdgeInsets.only(top: 7),
                                      padding: const EdgeInsets.all(10),
                                      decoration: BoxDecoration(color: const Color(0xfff3e8ff), borderRadius: BorderRadius.circular(16)),
                                      child: Column(mainAxisSize: MainAxisSize.min, children: [
                                        if (word.exampleEn.isNotEmpty) ...[
                                          Text(word.exampleEn, textDirection: TextDirection.ltr, textAlign: TextAlign.center, maxLines: 3, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: compact ? 14 : 16, fontWeight: FontWeight.w800)),
                                          const SizedBox(height: 5),
                                          SizedBox(height: 38, child: FilledButton.tonalIcon(onPressed: () => pronounce(context, word.exampleEn), icon: const Icon(Icons.volume_up_rounded, size: 18), label: const Text('لفظ الجملة'))),
                                        ],
                                        if (word.exampleAr.isNotEmpty) ...[
                                          const SizedBox(height: 5),
                                          Text(word.exampleAr, textAlign: TextAlign.center, maxLines: 3, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: compact ? 13 : 15, height: 1.25)),
                                        ],
                                      ]),
                                    ),
                                  ],
                                  const SizedBox(height: 7),
                                  SizedBox(width: double.infinity, height: 44, child: FilledButton.icon(
                                    onPressed: () => setState(() => showMeaning = !showMeaning),
                                    icon: const Icon(Icons.translate_rounded),
                                    label: Text(showMeaning ? 'إخفاء المعنى' : 'إظهار المعنى'),
                                  )),
                                  if (showMeaning) Container(
                                    width: double.infinity,
                                    margin: const EdgeInsets.only(top: 7),
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                                    decoration: BoxDecoration(color: const Color(0xffdbeafe), borderRadius: BorderRadius.circular(16)),
                                    child: Text(word.ar, textAlign: TextAlign.center, maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: compact ? 22 : 27, fontWeight: FontWeight.w900)),
                                  ),
                                ]),
                              ),
                            ),
                          ),
                        ),
                      );
                    }),
                  ),
          ),
          const SizedBox(height: 6),
          Row(children: [
            Expanded(child: _actionButton(child: OutlinedButton.icon(onPressed: word == null ? null : () => move(-1, list.length), icon: const Icon(Icons.arrow_forward_rounded, size: 19), label: const Text('السابق')))),
            const SizedBox(width: 7),
            Expanded(child: _actionButton(child: FilledButton.icon(onPressed: word == null ? null : () => move(1, list.length), icon: const Icon(Icons.arrow_back_rounded, size: 19), label: const Text('التالي')))),
          ]),
          const SizedBox(height: 5),
          Row(children: [
            Expanded(child: _actionButton(child: OutlinedButton.icon(
              style: OutlinedButton.styleFrom(foregroundColor: const Color(0xffb45309), side: const BorderSide(color: Color(0xfff59e0b))),
              onPressed: word == null ? null : () async { await widget.store.setReviewState(word, masteredNow: false); move(1, list.length); },
              icon: const Icon(Icons.refresh_rounded, size: 19), label: const Text('تحتاج مراجعة')))),
            const SizedBox(width: 7),
            Expanded(child: _actionButton(child: FilledButton.icon(
              style: FilledButton.styleFrom(backgroundColor: const Color(0xff059669), foregroundColor: Colors.white),
              onPressed: word == null ? null : () async { await widget.store.setReviewState(word, masteredNow: true); move(1, list.length); },
              icon: const Icon(Icons.check_rounded, size: 19), label: const Text('أتقنتها')))),
          ]),
        ]),
      ),
    );
  }
}

'''
s = s[:flash_start] + flash + s[flash_end:]

quiz_start = s.find('class QuizSetupPage')
quiz_end = s.find('class DifficultPage', quiz_start)
if quiz_start < 0 or quiz_end < 0:
    raise SystemExit('Quiz block not found')
quiz = r'''class QuizSetupPage extends StatefulWidget {
  final Store store;
  const QuizSetupPage({super.key, required this.store});
  @override
  State<QuizSetupPage> createState() => _QuizSetupPageState();
}

class _QuizSetupPageState extends State<QuizSetupPage> {
  String grade = '1';
  String mode = 'random';
  String unit = '';
  int count = 20;

  List<String> get units => widget.store.byGrade(grade).map((w) => w.unit.trim()).where((v) => v.isNotEmpty).toSet().toList()..sort();

  int _pageNumber(WordItem w) => int.tryParse(RegExp(r'\d+').firstMatch(w.sourcePage)?.group(0) ?? '') ?? 999999;

  List<WordItem> _questions() {
    List<WordItem> list;
    switch (mode) {
      case 'comprehensive':
        list = List<WordItem>.from(widget.store.words)..sort((a, b) {
          final g = (int.tryParse(a.grade) ?? 99).compareTo(int.tryParse(b.grade) ?? 99);
          return g != 0 ? g : a.id.compareTo(b.id);
        });
        break;
      case 'pdf':
        list = widget.store.byGrade(grade).where((w) => w.sourcePage.trim().isNotEmpty).toList();
        list.sort((a, b) {
          final p = _pageNumber(a).compareTo(_pageNumber(b));
          return p != 0 ? p : a.id.compareTo(b.id);
        });
        break;
      case 'unit':
        list = widget.store.byGrade(grade).where((w) => w.unit == unit).toList();
        break;
      case 'easy':
        list = List<WordItem>.from(widget.store.byGrade(grade));
        list.sort((a, b) => widget.store.difficultyScore(a).compareTo(widget.store.difficultyScore(b)));
        break;
      case 'studied':
        list = widget.store.byGrade(grade).where((w) => widget.store.studied.contains('${w.id}')).toList();
        break;
      default:
        list = List<WordItem>.from(widget.store.byGrade(grade))..shuffle();
    }
    if (count > 0 && list.length > count) return list.take(count).toList(growable: false);
    return list;
  }

  String get modeTitle => const {
    'random': 'عشوائي',
    'pdf': 'حسب ترتيب PDF',
    'unit': 'حسب الوحدة',
    'easy': 'من الأسهل إلى الأصعب',
    'studied': 'الكلمات التي درستها',
    'comprehensive': 'شامل كل الصفوف',
  }[mode] ?? 'اختبار';

  void _start() {
    if (mode == 'unit' && unit.isEmpty) {
      snack(context, 'اختر الوحدة أولاً');
      return;
    }
    final q = _questions();
    if (q.isEmpty) {
      final msg = mode == 'pdf' ? 'لا توجد كلمات مرتبطة بصفحات PDF في هذا الصف بعد' : mode == 'studied' ? 'افتح بعض الكلمات وادرسها أولاً' : 'لا توجد كلمات مناسبة لهذا الاختبار';
      snack(context, msg);
      return;
    }
    push(context, QuizPage(store: widget.store, questions: q, title: modeTitle));
  }

  @override
  Widget build(BuildContext context) {
    final unitList = units;
    if (unit.isNotEmpty && !unitList.contains(unit)) unit = '';
    return Scaffold(
      appBar: AppBar(title: const Text('إعداد الاختبار')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            gradient: const LinearGradient(colors: [Color(0xff2563eb), Color(0xff7c3aed)]),
            borderRadius: BorderRadius.circular(24),
          ),
          child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Icon(Icons.quiz_rounded, color: Colors.white, size: 36),
            SizedBox(height: 8),
            Text('اختبار على طريقتك', style: TextStyle(color: Colors.white, fontSize: 23, fontWeight: FontWeight.w900)),
            SizedBox(height: 5),
            Text('اختر ترتيب الأسئلة والمحتوى قبل أن تبدأ.', style: TextStyle(color: Colors.white, height: 1.4)),
          ]),
        ),
        const SizedBox(height: 14),
        if (mode != 'comprehensive') DropdownButtonFormField<String>(
          value: grade,
          items: grades.map((g) => DropdownMenuItem(value: g, child: Text(gradeName(g)))).toList(),
          onChanged: (v) => setState(() { grade = v ?? grade; unit = ''; }),
          decoration: const InputDecoration(labelText: 'الصف'),
        ),
        if (mode != 'comprehensive') const SizedBox(height: 10),
        DropdownButtonFormField<String>(
          value: mode,
          items: const [
            DropdownMenuItem(value: 'random', child: Text('عشوائي')),
            DropdownMenuItem(value: 'pdf', child: Text('حسب ترتيب ظهور الكلمات في PDF')),
            DropdownMenuItem(value: 'unit', child: Text('حسب الوحدة')),
            DropdownMenuItem(value: 'easy', child: Text('حسب السهولة')),
            DropdownMenuItem(value: 'studied', child: Text('حسب الكلمات المدروسة على الجهاز')),
            DropdownMenuItem(value: 'comprehensive', child: Text('شامل - جميع الصفوف')),
          ],
          onChanged: (v) => setState(() { mode = v ?? mode; unit = ''; }),
          decoration: const InputDecoration(labelText: 'نوع الاختبار'),
        ),
        if (mode == 'unit') ...[
          const SizedBox(height: 10),
          DropdownButtonFormField<String>(
            value: unit.isEmpty ? null : unit,
            items: unitList.map((u) => DropdownMenuItem(value: u, child: Text(u))).toList(),
            onChanged: (v) => setState(() => unit = v ?? ''),
            decoration: const InputDecoration(labelText: 'الوحدة'),
          ),
        ],
        const SizedBox(height: 10),
        DropdownButtonFormField<int>(
          value: count,
          items: const [
            DropdownMenuItem(value: 10, child: Text('10 أسئلة')),
            DropdownMenuItem(value: 20, child: Text('20 سؤالاً')),
            DropdownMenuItem(value: 40, child: Text('40 سؤالاً')),
            DropdownMenuItem(value: 0, child: Text('كل الكلمات المتاحة')),
          ],
          onChanged: (v) => setState(() => count = v ?? 20),
          decoration: const InputDecoration(labelText: 'عدد الأسئلة'),
        ),
        const SizedBox(height: 18),
        FilledButton.icon(onPressed: _start, icon: const Icon(Icons.play_arrow_rounded), label: Text('ابدأ • $modeTitle')),
        if (mode == 'pdf') const Padding(padding: EdgeInsets.only(top: 10), child: Text('يحافظ على ترتيب الصفحات وترتيب الحفظ من ملفات PDF التي استخرجتها داخل التطبيق.', textAlign: TextAlign.center, style: TextStyle(color: Color(0xff64748b)))),
      ]),
    );
  }
}

class QuizPage extends StatefulWidget {
  final Store store;
  final List<WordItem> questions;
  final String title;
  const QuizPage({super.key, required this.store, required this.questions, required this.title});
  @override
  State<QuizPage> createState() => _QuizPageState();
}

class _QuizPageState extends State<QuizPage> {
  int i = 0, score = 0;
  final Set<int> wrongIds = {};

  List<String> _options(WordItem w) {
    final choices = <String>{w.ar};
    final sameGrade = widget.store.byGrade(w.grade).where((x) => x.ar != w.ar).toList();
    final pool = sameGrade.isNotEmpty ? sameGrade : widget.store.words.where((x) => x.ar != w.ar).toList();
    pool.shuffle();
    for (final item in pool) {
      choices.add(item.ar);
      if (choices.length >= 4) break;
    }
    return choices.toList()..shuffle();
  }

  Widget _result() {
    final wrong = widget.questions.where((w) => wrongIds.contains(w.id)).toList(growable: false);
    final pct = widget.questions.isEmpty ? 0 : ((score / widget.questions.length) * 100).round();
    return ListView(padding: const EdgeInsets.all(16), children: [
      Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xff059669), Color(0xff2563eb)]), borderRadius: BorderRadius.circular(28)),
        child: Column(children: [
          const Icon(Icons.emoji_events_rounded, size: 64, color: Colors.white),
          const SizedBox(height: 8),
          Text('$score / ${widget.questions.length}', style: const TextStyle(color: Colors.white, fontSize: 36, fontWeight: FontWeight.w900)),
          Text('$pct%', style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w800)),
        ]),
      ),
      const SizedBox(height: 16),
      if (wrong.isEmpty)
        const Card(child: Padding(padding: EdgeInsets.all(22), child: Text('ممتاز! لم تخطئ في أي كلمة.', textAlign: TextAlign.center, style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900))))
      else ...[
        Text('تدرّب على الكلمات التي أخطأت فيها (${wrong.length})', style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w900)),
        const SizedBox(height: 8),
        ...wrong.map((w) => Card(
          color: const Color(0xfffffbeb),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(children: [
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w900)),
                subtitle: Text('${w.ar} • أخطاء سابقة: ${widget.store.wrongCounts['${w.id}'] ?? 0}'),
                trailing: IconButton(icon: const Icon(Icons.school_rounded), tooltip: 'تدريب على الكلمة', onPressed: () => showWord(context, widget.store, w, source: wrong, initialIndex: wrong.indexOf(w))),
              ),
              Row(children: [
                Expanded(child: OutlinedButton.icon(
                  onPressed: () async { await widget.store.setReviewState(w, masteredNow: false); if (mounted) setState(() {}); },
                  icon: const Icon(Icons.refresh_rounded), label: const Text('تحتاج مراجعة'))),
                const SizedBox(width: 8),
                Expanded(child: FilledButton.icon(
                  style: FilledButton.styleFrom(backgroundColor: const Color(0xff059669), foregroundColor: Colors.white),
                  onPressed: () async { await widget.store.setReviewState(w, masteredNow: true); if (mounted) setState(() {}); },
                  icon: const Icon(Icons.check_rounded), label: const Text('أتقنتها'))),
              ]),
            ]),
          ),
        )),
      ],
      const SizedBox(height: 16),
      FilledButton.icon(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.done_all_rounded), label: const Text('إنهاء الاختبار')),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    if (widget.questions.isEmpty) return Scaffold(appBar: AppBar(), body: const Center(child: Text('لا توجد كلمات')));
    if (i >= widget.questions.length) return Scaffold(appBar: AppBar(title: const Text('نتيجة الاختبار')), body: _result());
    final w = widget.questions[i];
    final options = _options(w);
    return Scaffold(
      appBar: AppBar(title: Text('${widget.title} • ${i + 1}/${widget.questions.length}')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        LinearProgressIndicator(value: (i + 1) / widget.questions.length, minHeight: 8, borderRadius: BorderRadius.circular(10)),
        const SizedBox(height: 14),
        Card(
          color: const Color(0xffeff6ff),
          child: Padding(padding: const EdgeInsets.all(24), child: Column(children: [
            Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 35, fontWeight: FontWeight.w900)),
            const SizedBox(height: 12),
            FilledButton.tonalIcon(onPressed: () => widget.store.speak(w.en), icon: const Icon(Icons.volume_up_rounded), label: const Text('اسمع الكلمة')),
          ])),
        ),
        const SizedBox(height: 6),
        ...options.asMap().entries.map((entry) {
          final palette = [const Color(0xffeff6ff), const Color(0xfff5f3ff), const Color(0xfffdf2f8), const Color(0xffecfdf5)];
          final o = entry.value;
          return Card(
            color: palette[entry.key % palette.length],
            child: ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
              title: Text(o, style: const TextStyle(fontWeight: FontWeight.w800)),
              trailing: const Icon(Icons.chevron_left_rounded),
              onTap: () async {
                final ok = o == w.ar;
                await widget.store.answer(w, ok);
                if (ok) score++; else wrongIds.add(w.id);
                if (mounted) setState(() => i++);
              },
            ),
          );
        }),
      ]),
    );
  }
}

'''
s = s[:quiz_start] + quiz + s[quiz_end:]

old_sort = """      list.sort((a, b) {\n        final f = b.frequency.compareTo(a.frequency);\n        if (f != 0) return f;\n        return a.word.compareTo(b.word);\n      });\n"""
if old_sort in s:
    s = s.replace(old_sort, "      // Keep the extraction map's insertion order: this is the first appearance order in the PDF.\n", 1)

s = s.replace("void showWord(BuildContext context, Store store, WordItem word, {List<WordItem>? source, int? initialIndex}) {\n  final list", "void showWord(BuildContext context, Store store, WordItem word, {List<WordItem>? source, int? initialIndex}) {\n  store.markStudied(word);\n  final list")

settings_start = s.find('class SettingsTile extends StatelessWidget {')
settings_end = s.find('void showWord(', settings_start)
if settings_start > 0 and settings_end > settings_start:
    settings = r'''class SettingsTile extends StatelessWidget {
  final IconData icon;
  final String title, subtitle;
  final VoidCallback? onTap;
  const SettingsTile({super.key, required this.icon, required this.title, required this.subtitle, this.onTap});
  @override
  Widget build(BuildContext context) {
    const colors = [Color(0xff2563eb), Color(0xff7c3aed), Color(0xffdb2777), Color(0xffea580c), Color(0xff059669), Color(0xff0891b2)];
    final accent = colors[icon.codePoint.abs() % colors.length];
    return Card(
      color: Color.alphaBlend(accent.withOpacity(.055), Colors.white),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22), side: BorderSide(color: accent.withOpacity(.17))),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(width: 44, height: 44, decoration: BoxDecoration(color: accent.withOpacity(.14), borderRadius: BorderRadius.circular(14)), child: Icon(icon, color: accent)),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
        subtitle: Text(subtitle),
        trailing: onTap == null ? null : Icon(Icons.chevron_left, color: accent),
        onTap: onTap,
      ),
    );
  }
}

'''
    s = s[:settings_start] + settings + s[settings_end:]

p.write_text(s, encoding='utf-8')
print('Applied Qamoosi AI v3.4 learning UX patch')
