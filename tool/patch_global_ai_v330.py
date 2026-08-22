from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')
if "const appVersion = '3.3.0';" in s:
    print('v3.3.0 already applied')
    raise SystemExit(0)

s = s.replace("const appVersion = '3.2.3';", "const appVersion = '3.3.0';")
s = s.replace("title: 'القاموس المدرسي الأردني',", "title: 'قاموسي AI',")
s = s.replace('القاموس المدرسي الأردني', 'قاموسي AI')
s = s.replace('المنهاج الأردني', 'المفردات حسب الصف')
s = s.replace('مختبر الكتاب', 'استوديو AI للكتاب')
s = s.replace("AppBar(title: const Text('بحث ذكي'))", "AppBar(title: const Text('بحث AI الذكي'))")
s = s.replace("AppBar(title: const Text('التعلم والتمرين'))", "AppBar(title: const Text('التدريب الذكي'))")
s = s.replace("label: 'البحث'", "label: 'AI بحث'")
s = s.replace("label: 'المنهاج'", "label: 'الصفوف'")
s = s.replace("label: 'التعلم'", "label: 'تدريب'")
s = s.replace("title: 'اختبار ذكي', subtitle: 'اختبر فهمك'", "title: 'اختبار AI متكيف', subtitle: 'يتكيف مع مستواك وأخطائك'")
s = s.replace("title: 'الصعبة', subtitle: '${store.difficult.length} تحتاج مراجعة'", "title: 'مراجعة AI', subtitle: '${store.smartStudyWords.length} كلمة مقترحة لك'")
s = s.replace("title: 'استوديو AI للكتاب', subtitle: 'رفع كتاب أو وحدة وتحويلها إلى قاموس منظم'", "title: 'استوديو AI للكتاب', subtitle: 'استخرج المفردات والمعاني والجمل من أي كتاب PDF'")
s = s.replace("const Text('حوّل الكتاب إلى قاموس'", "const Text('حوّل أي كتاب إلى قاموس بالذكاء الاصطناعي'")
s = s.replace("const Text('يقرأ PDF، يكتشف الوحدة والدرس، يستخرج الكلمات التعليمية ويستبعد الأسماء والأماكن والأرقام والحروف والرموز، ثم يعرض النتائج للمراجعة قبل الحفظ.'", "const Text('يحلل PDF، يكتشف بنية الكتاب، ينظف المفردات، ويستخدم التعلم الآلي للترجمة واقتراح أمثلة قبل أن تراجعها وتحفظها.'")
s = s.replace("subject: 'كلمات قاموسي AI'", "subject: 'كلمات قاموسي AI'")
s = s.replace("return speak('Welcome to my school dictionary');", "return speak('Welcome to Qamoosi AI, the smart dictionary for Arab students');")

old_load = """  Future<void> _loadWords() async {
    final raw = prefs.getString('words_json') ?? await rootBundle.loadString('assets/data/words.json');
    final data = jsonDecode(raw) as Map<String, dynamic>;
    words = (data['words'] as List? ?? [])
        .map((e) => WordItem.fromJson(Map<String, dynamic>.from(e)))
        .where((w) => w.en.isNotEmpty && w.ar.isNotEmpty && grades.contains(w.grade))
        .toList(growable: true);
  }
"""
new_load = """  Future<void> _loadWords() async {
    // Always load the latest global built-in vocabulary, then merge the user's
    // saved words on top. This preserves user data while allowing app updates
    // to add new grade vocabulary and enrich older entries with examples.
    final seedRaw = await rootBundle.loadString('assets/data/words.json');
    final seedData = jsonDecode(seedRaw) as Map<String, dynamic>;
    final seedWords = (seedData['words'] as List? ?? [])
        .map((e) => WordItem.fromJson(Map<String, dynamic>.from(e)))
        .where((w) => w.en.isNotEmpty && w.ar.isNotEmpty && grades.contains(w.grade))
        .toList(growable: true);

    final index = <String, WordItem>{};
    String key(WordItem w) => '${w.grade}|${w.semester}|${w.unit}|${w.lesson}|${w.en.trim().toLowerCase()}';
    for (final w in seedWords) index[key(w)] = w;

    final savedRaw = prefs.getString('words_json');
    if (savedRaw != null) {
      try {
        final savedData = jsonDecode(savedRaw) as Map<String, dynamic>;
        final savedWords = (savedData['words'] as List? ?? [])
            .map((e) => WordItem.fromJson(Map<String, dynamic>.from(e)))
            .where((w) => w.en.isNotEmpty && w.ar.isNotEmpty && grades.contains(w.grade));
        for (final w in savedWords) {
          final k = key(w);
          final seed = index[k];
          index[k] = WordItem(
            id: w.id,
            grade: w.grade,
            en: w.en,
            ar: w.ar,
            exampleEn: w.exampleEn.isNotEmpty ? w.exampleEn : (seed?.exampleEn ?? ''),
            exampleAr: w.exampleAr.isNotEmpty ? w.exampleAr : (seed?.exampleAr ?? ''),
            semester: w.semester,
            unit: w.unit,
            lesson: w.lesson,
            sourcePage: w.sourcePage,
          );
        }
      } catch (_) {}
    }
    words = index.values.toList(growable: true);
  }
"""
if old_load not in s:
    raise SystemExit('loadWords block not found')
s = s.replace(old_load, new_load)

needle = """  List<WordItem> smartSearch(String value) {
    final q = value.trim().toLowerCase();
    if (q.isEmpty) return const [];
    int rank(WordItem w) {
      final en = w.en.toLowerCase();
      final ar = w.ar.toLowerCase();
      final exEn = w.exampleEn.toLowerCase();
      final exAr = w.exampleAr.toLowerCase();
      if (en == q || ar == q) return 0;
      if (en.startsWith(q) || ar.startsWith(q)) return 1;
      if (en.contains(q) || ar.contains(q)) return 2;
      if (exEn.contains(q) || exAr.contains(q)) return 3;
      return 99;
    }
"""
replacement = """  int _editDistance(String a, String b) {
    if (a == b) return 0;
    if (a.isEmpty) return b.length;
    if (b.isEmpty) return a.length;
    var prev = List<int>.generate(b.length + 1, (i) => i);
    for (var i = 1; i <= a.length; i++) {
      final cur = List<int>.filled(b.length + 1, 0);
      cur[0] = i;
      for (var j = 1; j <= b.length; j++) {
        final cost = a[i - 1] == b[j - 1] ? 0 : 1;
        cur[j] = min(min(cur[j - 1] + 1, prev[j] + 1), prev[j - 1] + cost);
      }
      prev = cur;
    }
    return prev[b.length];
  }

  List<WordItem> get smartStudyWords {
    final ranked = List<WordItem>.from(words);
    int score(WordItem w) {
      final id = '${w.id}';
      var value = (wrongCounts[id] ?? 0) * 10;
      if (difficult.contains(id)) value += 20;
      if (!mastered.contains(id)) value += 5;
      if (w.exampleEn.isNotEmpty && w.exampleAr.isNotEmpty) value += 2;
      return value;
    }
    ranked.sort((a, b) => score(b).compareTo(score(a)));
    return ranked.where((w) => score(w) > 0).take(30).toList(growable: false);
  }

  List<WordItem> smartSearch(String value) {
    final q = value.trim().toLowerCase();
    if (q.isEmpty) return const [];
    int rank(WordItem w) {
      final en = w.en.toLowerCase();
      final ar = w.ar.toLowerCase();
      final exEn = w.exampleEn.toLowerCase();
      final exAr = w.exampleAr.toLowerCase();
      if (en == q || ar == q) return 0;
      if (en.startsWith(q) || ar.startsWith(q)) return 1;
      if (en.contains(q) || ar.contains(q)) return 2;
      if (q.length >= 3 && _editDistance(en, q) <= (q.length >= 6 ? 2 : 1)) return 3;
      if (exEn.contains(q) || exAr.contains(q)) return 4;
      return 99;
    }
"""
if needle not in s:
    raise SystemExit('smartSearch block not found')
s = s.replace(needle, replacement)

# Onboarding: stop opening recovery dialog before the intro.
s = s.replace("""  bool ready = false;
""", """  bool ready = false;
  bool introDone = false;
""", 1)
s = s.replace("""      setState(() => ready = true);
      if (store.freshInstall) {
        WidgetsBinding.instance.addPostFrameCallback((_) => _offerRecovery());
      }
""", """      setState(() => ready = true);
""", 1)
s = s.replace("""    if (!ready) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    return AnimatedBuilder(animation: store, builder: (_, __) => HomeShell(store: store));
""", """    if (!ready) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    if (store.freshInstall && !introDone) {
      return QamoosiAiOnboarding(onDone: () {
        setState(() => introDone = true);
        WidgetsBinding.instance.addPostFrameCallback((_) => _offerRecovery());
      });
    }
    return AnimatedBuilder(animation: store, builder: (_, __) => HomeShell(store: store));
""", 1)

onboarding = r'''
class QamoosiAiOnboarding extends StatefulWidget {
  final VoidCallback onDone;
  const QamoosiAiOnboarding({super.key, required this.onDone});
  @override
  State<QamoosiAiOnboarding> createState() => _QamoosiAiOnboardingState();
}

class _QamoosiAiOnboardingState extends State<QamoosiAiOnboarding> {
  final controller = PageController();
  int page = 0;
  final items = const [
    (Icons.auto_awesome_rounded, 'قاموسي AI', 'القاموس الذكي للطلاب العرب', 'تعلّم الإنجليزية من كلمات مناسبة لصفك مع المعنى والجملة والترجمة والنطق.'),
    (Icons.manage_search_rounded, 'بحث يفهم أخطاء الكتابة', 'اكتب بالعربي أو الإنجليزي', 'البحث الذكي يرتب النتائج ويقترح الكلمات القريبة حتى عند وجود خطأ بسيط في الكتابة.'),
    (Icons.picture_as_pdf_rounded, 'استوديو AI للكتاب', 'حوّل أي PDF إلى مفردات', 'يستخرج الكلمات التعليمية، ينظف الضوضاء، ثم يستخدم التعلم الآلي لترجمة الكلمات والجمل على جهازك.'),
    (Icons.psychology_alt_rounded, 'مدرب يتعلم من تقدمك', 'مراجعة شخصية لكل طالب', 'يراقب الكلمات الصعبة والأخطاء ويقترح قائمة مراجعة ذكية بدل دراسة كل الكلمات بنفس الطريقة.'),
  ];

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Column(children: [
        Align(alignment: Alignment.centerLeft, child: TextButton(onPressed: widget.onDone, child: const Text('تخطي'))),
        Expanded(child: PageView.builder(
          controller: controller,
          itemCount: items.length,
          onPageChanged: (v) => setState(() => page = v),
          itemBuilder: (_, i) {
            final item = items[i];
            return Padding(
              padding: const EdgeInsets.all(28),
              child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                Container(width: 128, height: 128, decoration: BoxDecoration(color: Theme.of(context).colorScheme.primaryContainer, borderRadius: BorderRadius.circular(36)), child: Icon(item.$1, size: 68, color: Theme.of(context).colorScheme.primary)),
                const SizedBox(height: 28),
                Text(item.$2, textAlign: TextAlign.center, style: const TextStyle(fontSize: 31, fontWeight: FontWeight.w900)),
                const SizedBox(height: 10),
                Text(item.$3, textAlign: TextAlign.center, style: TextStyle(fontSize: 19, fontWeight: FontWeight.w800, color: Theme.of(context).colorScheme.primary)),
                const SizedBox(height: 14),
                Text(item.$4, textAlign: TextAlign.center, style: const TextStyle(fontSize: 16, height: 1.7, color: Color(0xff64748b))),
              ]),
            );
          },
        )),
        Row(mainAxisAlignment: MainAxisAlignment.center, children: List.generate(items.length, (i) => AnimatedContainer(duration: const Duration(milliseconds: 220), margin: const EdgeInsets.all(4), width: i == page ? 24 : 8, height: 8, decoration: BoxDecoration(color: i == page ? Theme.of(context).colorScheme.primary : const Color(0xffcbd5e1), borderRadius: BorderRadius.circular(10))))),
        Padding(
          padding: const EdgeInsets.all(20),
          child: SizedBox(width: double.infinity, child: FilledButton.icon(
            onPressed: () {
              if (page == items.length - 1) widget.onDone();
              else controller.nextPage(duration: const Duration(milliseconds: 280), curve: Curves.easeOut);
            },
            icon: Icon(page == items.length - 1 ? Icons.rocket_launch_rounded : Icons.arrow_back_rounded),
            label: Text(page == items.length - 1 ? 'ابدأ مع قاموسي AI' : 'التالي'),
          )),
        ),
      ]),
    ),
  );
}

'''
insert_at = s.find('class HomeShell extends StatefulWidget')
if insert_at < 0:
    raise SystemExit('HomeShell insertion point not found')
s = s[:insert_at] + onboarding + s[insert_at:]

# Add adaptive review entry above BookCandidate and expose it in LearnHub.
adaptive = r'''
class AdaptiveReviewPage extends StatelessWidget {
  final Store store;
  const AdaptiveReviewPage({super.key, required this.store});
  @override
  Widget build(BuildContext context) {
    final words = store.smartStudyWords;
    return Scaffold(
      appBar: AppBar(title: const Text('خطة AI اليومية')),
      body: words.isEmpty
          ? const Center(child: Padding(padding: EdgeInsets.all(28), child: Text('ممتاز! لا توجد كلمات صعبة بعد. ابدأ اختبارًا أو بطاقات تعليمية ليبني المدرب الذكي خطة مناسبة لك.', textAlign: TextAlign.center)))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: words.length,
              itemBuilder: (_, i) {
                final w = words[i];
                final wrong = store.wrongCounts['${w.id}'] ?? 0;
                return Card(child: ListTile(
                  leading: CircleAvatar(child: Text('${i + 1}')),
                  title: Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 20)),
                  subtitle: Text('${w.ar}${wrong > 0 ? ' • أخطاء سابقة: $wrong' : ' • مقترحة للمراجعة'}'),
                  trailing: const Icon(Icons.auto_awesome_rounded),
                  onTap: () => showWord(context, store, w, source: words, initialIndex: i),
                ));
              },
            ),
    );
  }
}

'''
insert_at = s.find('class BookCandidate {')
if insert_at < 0:
    raise SystemExit('BookCandidate insertion point not found')
s = s[:insert_at] + adaptive + s[insert_at:]

learn_needle = """    body: ListView(padding: const EdgeInsets.all(16), children: [
      Row(children: [
"""
learn_repl = """    body: ListView(padding: const EdgeInsets.all(16), children: [
      Card(child: ListTile(
        contentPadding: const EdgeInsets.all(18),
        leading: CircleAvatar(radius: 26, child: const Icon(Icons.auto_awesome_rounded)),
        title: const Text('خطة AI اليومية', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 19)),
        subtitle: Text(store.smartStudyWords.isEmpty ? 'ابدأ التعلم ليبني الذكاء خطتك الشخصية' : '${store.smartStudyWords.length} كلمة مرتبة حسب حاجتك للمراجعة'),
        trailing: const Icon(Icons.chevron_left_rounded),
        onTap: () => push(context, AdaptiveReviewPage(store: store)),
      )),
      const SizedBox(height: 8),
      Row(children: [
"""
if learn_needle not in s:
    raise SystemExit('LearnHub insertion point not found')
s = s.replace(learn_needle, learn_repl, 1)

# Global positioning / clearer labels.
s = s.replace("const Text('ابدأ بكتابة أول حرف'", "const Text('اسأل قاموسي AI عن أي كلمة'")
s = s.replace("const Text('تظهر الكلمات المطابقة فورًا مع كل حرف تكتبه. اضغط على أي كلمة لفتح المعنى والمثال والترجمة والنطق.'", "const Text('اكتب بالعربية أو الإنجليزية. البحث الذكي يرتب التطابقات ويستطيع التقاط بعض أخطاء الكتابة، ثم يعرض المعنى والجملة والترجمة والنطق.'")
s = s.replace("subtitle: Text(count == 0 ? 'جاهز لإضافة وحدات ودروس المنهاج' : '$count كلمة محفوظة')", "subtitle: Text(count == 0 ? 'جاهز لإضافة مفردات هذا الصف' : '$count كلمة لهذا الصف')")
s = s.replace("const Text('عند استيراد ملفات المنهاج أو استخدام استوديو AI للكتاب ستظهر هنا الفصول ثم الوحدات والدروس تلقائيًا.'", "const Text('يمكنك استخدام المفردات العالمية الجاهزة أو استيراد كتابك الخاص عبر استوديو AI، وستظهر الوحدات والدروس تلقائيًا عندما تكون متوفرة.'")

p.write_text(s, encoding='utf-8')
print('Applied Qamoosi AI global v3.3.0 patch')
