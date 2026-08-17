from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

# Identity and supported Jordan school grades.
s = re.sub(r"const grades = \[[^\n]+\];", "const grades = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];", s, count=1)
s = re.sub(r"const appVersion = '[^']+';", "const appVersion = '3.0.0';", s, count=1)
s = s.replace("title: 'قاموسي المدرسي',", "title: 'القاموس المدرسي الأردني',", 1)
s = s.replace("const SliverAppBar(title: Text('قاموسي المدرسي'), floating: true)", "const SliverAppBar(title: Text('القاموس المدرسي الأردني'), floating: true)")
s = s.replace("title: 'قاموسي المدرسي', subtitle: 'الإصدار $appVersion • يعمل دون إنترنت'", "title: 'القاموس المدرسي الأردني', subtitle: 'الإصدار $appVersion • يعمل دون إنترنت'")

# Expand WordItem with curriculum metadata while keeping all old data compatible.
old = """  final String exampleEn;
  final String exampleAr;

  const WordItem({required this.id, required this.grade, required this.en, required this.ar, this.exampleEn = '', this.exampleAr = ''});
"""
new = """  final String exampleEn;
  final String exampleAr;
  final String semester;
  final String unit;
  final String lesson;
  final String sourcePage;

  const WordItem({
    required this.id,
    required this.grade,
    required this.en,
    required this.ar,
    this.exampleEn = '',
    this.exampleAr = '',
    this.semester = '',
    this.unit = '',
    this.lesson = '',
    this.sourcePage = '',
  });
"""
if old in s:
    s = s.replace(old, new, 1)

old = """        exampleAr: '${j['example_ar'] ?? j['sentence_ar'] ?? j['exampleArabic'] ?? j['example_arabic'] ?? j['sentenceArabic'] ?? j['sentence_arabic'] ?? j['sentenceTranslation'] ?? j['sentence_translation'] ?? j['translation'] ?? j['ترجمة الجملة'] ?? j['ترجمة المثال'] ?? j['ترجمة المثال إلى العربية'] ?? ''}'.trim(),
      );
"""
new = """        exampleAr: '${j['example_ar'] ?? j['sentence_ar'] ?? j['exampleArabic'] ?? j['example_arabic'] ?? j['sentenceArabic'] ?? j['sentence_arabic'] ?? j['sentenceTranslation'] ?? j['sentence_translation'] ?? j['translation'] ?? j['ترجمة الجملة'] ?? j['ترجمة المثال'] ?? j['ترجمة المثال إلى العربية'] ?? ''}'.trim(),
        semester: '${j['semester'] ?? j['term'] ?? j['الفصل الدراسي'] ?? j['الفصل_الدراسي'] ?? ''}'.trim(),
        unit: '${j['unit'] ?? j['الوحدة'] ?? ''}'.trim(),
        lesson: '${j['lesson'] ?? j['الدرس'] ?? ''}'.trim(),
        sourcePage: '${j['page'] ?? j['source_page'] ?? j['رقم الصفحة'] ?? j['الصفحة'] ?? ''}'.trim(),
      );
"""
if old in s:
    s = s.replace(old, new, 1)

old = """        'example_en': exampleEn,
        'example_ar': exampleAr,
      };
"""
new = """        'example_en': exampleEn,
        'example_ar': exampleAr,
        'semester': semester,
        'unit': unit,
        'lesson': lesson,
        'source_page': sourcePage,
      };
"""
if old in s:
    s = s.replace(old, new, 1)

# Curriculum helpers and smarter search data source.
anchor = "  List<WordItem> byGrade(String g) => words.where((w) => w.grade == g).toList(growable: false);\n"
insert = anchor + """  List<WordItem> byCurriculum({required String grade, String semester = '', String unit = '', String lesson = ''}) => words.where((w) {
    if (w.grade != grade) return false;
    if (semester.isNotEmpty && w.semester != semester) return false;
    if (unit.isNotEmpty && w.unit != unit) return false;
    if (lesson.isNotEmpty && w.lesson != lesson) return false;
    return true;
  }).toList(growable: false);

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
      if (exEn.contains(q) || exAr.contains(q)) return 3;
      return 99;
    }
    final result = words.where((w) => rank(w) < 99).toList(growable: false);
    result.sort((a, b) {
      final r = rank(a).compareTo(rank(b));
      if (r != 0) return r;
      return a.en.toLowerCase().compareTo(b.en.toLowerCase());
    });
    return result;
  }
"""
if anchor in s and 'List<WordItem> smartSearch' not in s:
    s = s.replace(anchor, insert, 1)

# Excel/CSV curriculum columns.
old = """      exampleAr: _valueByHeaders(row, ['example_ar', 'sentence_ar', 'examplearabic', 'example_arabic', 'sentencearabic', 'sentence_arabic', 'translation', 'sentencetranslation', 'sentence_translation', 'ترجمه_الجمله', 'ترجمه_المثال', 'ترجمه_المثال_الي_العربيه', 'مثال_عربي']),
    );
"""
new = """      exampleAr: _valueByHeaders(row, ['example_ar', 'sentence_ar', 'examplearabic', 'example_arabic', 'sentencearabic', 'sentence_arabic', 'translation', 'sentencetranslation', 'sentence_translation', 'ترجمه_الجمله', 'ترجمه_المثال', 'ترجمه_المثال_الي_العربيه', 'مثال_عربي']),
      semester: _valueByHeaders(row, ['semester', 'term', 'الفصل_الدراسي', 'الفصل الدراسي']),
      unit: _valueByHeaders(row, ['unit', 'الوحده', 'الوحدة']),
      lesson: _valueByHeaders(row, ['lesson', 'الدرس']),
      sourcePage: _valueByHeaders(row, ['source_page', 'page', 'رقم_الصفحه', 'رقم الصفحة', 'الصفحه', 'الصفحة']),
    );
"""
if old in s:
    s = s.replace(old, new, 1)

# Preserve curriculum scope when merging imported data.
s = s.replace("'${w.grade}|${w.en.trim().toLowerCase()}': w,", "'${w.grade}|${w.semester}|${w.unit}|${w.lesson}|${w.en.trim().toLowerCase()}': w,")
s = s.replace("final key = '${word.grade}|${word.en.trim().toLowerCase()}';", "final key = '${word.grade}|${word.semester}|${word.unit}|${word.lesson}|${word.en.trim().toLowerCase()}';")

# Replace the shell with the new five-part navigation.
start = s.find('class HomeShell extends StatefulWidget')
end = s.find('class HomePage extends StatelessWidget')
if start == -1 or end == -1 or end <= start:
    raise SystemExit('HomeShell/HomePage anchors not found')
new_shell = r'''class HomeShell extends StatefulWidget {
  final Store store;
  const HomeShell({super.key, required this.store});
  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int index = 0;
  late final pages = [
    HomePage(store: widget.store),
    SmartSearchPage(store: widget.store),
    CurriculumPage(store: widget.store),
    LearnHubPage(store: widget.store),
    MorePage(store: widget.store),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(child: IndexedStack(index: index, children: pages)),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (v) => setState(() => index = v),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_rounded), label: 'الرئيسية'),
          NavigationDestination(icon: Icon(Icons.search_rounded), label: 'البحث'),
          NavigationDestination(icon: Icon(Icons.auto_stories_rounded), label: 'المنهاج'),
          NavigationDestination(icon: Icon(Icons.extension_rounded), label: 'التعلم'),
          NavigationDestination(icon: Icon(Icons.grid_view_rounded), label: 'المزيد'),
        ],
      ),
    );
  }
}

class SmartSearchPage extends StatefulWidget {
  final Store store;
  const SmartSearchPage({super.key, required this.store});
  @override
  State<SmartSearchPage> createState() => _SmartSearchPageState();
}

class _SmartSearchPageState extends State<SmartSearchPage> {
  final controller = TextEditingController();
  String query = '';

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final results = widget.store.smartSearch(query);
    return Scaffold(
      appBar: AppBar(title: const Text('بحث ذكي')),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 8),
          child: TextField(
            controller: controller,
            autofocus: false,
            onChanged: (v) => setState(() => query = v),
            decoration: InputDecoration(
              hintText: 'اكتب كلمة بالعربي أو الإنجليزي...',
              prefixIcon: const Icon(Icons.search_rounded),
              suffixIcon: query.isEmpty ? null : IconButton(
                tooltip: 'مسح',
                onPressed: () { controller.clear(); setState(() => query = ''); },
                icon: const Icon(Icons.close_rounded),
              ),
            ),
          ),
        ),
        if (query.isNotEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 5),
            child: Align(alignment: Alignment.centerRight, child: Text('${results.length} نتيجة مطابقة', style: const TextStyle(fontWeight: FontWeight.w700, color: Color(0xff64748b)))),
          ),
        Expanded(
          child: query.isEmpty
              ? const _SearchWelcome()
              : results.isEmpty
                  ? const Center(child: Text('لم أجد كلمة مطابقة'))
                  : ListView.builder(
                      keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                      padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                      itemCount: results.length,
                      itemBuilder: (_, i) {
                        final w = results[i];
                        final scope = [gradeName(w.grade), if (w.unit.isNotEmpty) w.unit, if (w.lesson.isNotEmpty) w.lesson].join(' • ');
                        return Card(
                          child: ListTile(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
                            leading: CircleAvatar(backgroundColor: Theme.of(context).colorScheme.primaryContainer, child: const Icon(Icons.translate_rounded)),
                            title: Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w900)),
                            subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              const SizedBox(height: 4),
                              Text(w.ar, style: const TextStyle(fontWeight: FontWeight.w700)),
                              const SizedBox(height: 3),
                              Text(scope, style: const TextStyle(fontSize: 12, color: Color(0xff718096))),
                            ]),
                            trailing: IconButton(
                              tooltip: 'نطق الكلمة',
                              icon: const Icon(Icons.volume_up_rounded),
                              onPressed: () => widget.store.speak(w.en),
                            ),
                            onTap: () => showWord(context, widget.store, w, source: results, initialIndex: i),
                          ),
                        );
                      },
                    ),
        ),
      ]),
    );
  }
}

class _SearchWelcome extends StatelessWidget {
  const _SearchWelcome();
  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(28),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Icon(Icons.manage_search_rounded, size: 78, color: Theme.of(context).colorScheme.primary),
        const SizedBox(height: 16),
        const Text('ابدأ بكتابة أول حرف', style: TextStyle(fontSize: 23, fontWeight: FontWeight.w900)),
        const SizedBox(height: 8),
        const Text('تظهر الكلمات المطابقة فورًا مع كل حرف تكتبه. اضغط على أي كلمة لفتح المعنى والمثال والترجمة والنطق.', textAlign: TextAlign.center, style: TextStyle(height: 1.5, color: Color(0xff64748b))),
      ]),
    ),
  );
}

class CurriculumPage extends StatelessWidget {
  final Store store;
  const CurriculumPage({super.key, required this.store});

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('المنهاج الأردني')),
    body: ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: grades.length,
      itemBuilder: (_, i) {
        final g = grades[i];
        final count = store.byGrade(g).length;
        return Card(child: ListTile(
          contentPadding: const EdgeInsets.all(16),
          leading: CircleAvatar(child: Text(g, style: const TextStyle(fontWeight: FontWeight.w900))),
          title: Text(gradeName(g), style: const TextStyle(fontWeight: FontWeight.w900)),
          subtitle: Text(count == 0 ? 'جاهز لإضافة وحدات ودروس المنهاج' : '$count كلمة محفوظة'),
          trailing: const Icon(Icons.chevron_left_rounded),
          onTap: () => push(context, GradeCurriculumPage(store: store, grade: g)),
        ));
      },
    ),
  );
}

class GradeCurriculumPage extends StatelessWidget {
  final Store store;
  final String grade;
  const GradeCurriculumPage({super.key, required this.store, required this.grade});

  @override
  Widget build(BuildContext context) {
    final words = store.byGrade(grade);
    final semesters = words.map((w) => w.semester.trim()).where((v) => v.isNotEmpty).toSet().toList()..sort();
    return Scaffold(
      appBar: AppBar(title: Text(gradeName(grade))),
      body: semesters.isEmpty
          ? ListView(padding: const EdgeInsets.all(18), children: [
              Card(child: Padding(padding: const EdgeInsets.all(24), child: Column(children: [
                Icon(Icons.auto_stories_rounded, size: 58, color: Theme.of(context).colorScheme.primary),
                const SizedBox(height: 14),
                const Text('المحتوى الحالي غير مصنف حسب الفصل والوحدة والدرس', textAlign: TextAlign.center, style: TextStyle(fontSize: 19, fontWeight: FontWeight.w900)),
                const SizedBox(height: 8),
                const Text('عند استيراد ملفات المنهاج أو استخدام مختبر الكتاب ستظهر هنا الفصول ثم الوحدات والدروس تلقائيًا.', textAlign: TextAlign.center),
                if (words.isNotEmpty) ...[
                  const SizedBox(height: 18),
                  FilledButton.icon(onPressed: () => push(context, GradeWordsPage(store: store, grade: grade)), icon: const Icon(Icons.list_alt_rounded), label: Text('عرض ${words.length} كلمة الحالية')),
                ],
              ]))),
            ])
          : ListView(padding: const EdgeInsets.all(16), children: semesters.map((semester) {
              final semesterWords = store.byCurriculum(grade: grade, semester: semester);
              final units = semesterWords.map((w) => w.unit).where((v) => v.isNotEmpty).toSet();
              return Card(child: ExpansionTile(
                title: Text(semester, style: const TextStyle(fontWeight: FontWeight.w900)),
                subtitle: Text('${semesterWords.length} كلمة • ${units.length} وحدة'),
                children: units.map((unit) {
                  final unitWords = store.byCurriculum(grade: grade, semester: semester, unit: unit);
                  final lessons = unitWords.map((w) => w.lesson).where((v) => v.isNotEmpty).toSet();
                  return ListTile(
                    leading: const Icon(Icons.menu_book_rounded),
                    title: Text(unit, style: const TextStyle(fontWeight: FontWeight.w800)),
                    subtitle: Text('${unitWords.length} كلمة • ${lessons.length} درس'),
                    onTap: () => push(context, CurriculumWordsPage(store: store, title: unit, words: unitWords)),
                  );
                }).toList(),
              ));
            }).toList()),
    );
  }
}

class CurriculumWordsPage extends StatelessWidget {
  final Store store;
  final String title;
  final List<WordItem> words;
  const CurriculumWordsPage({super.key, required this.store, required this.title, required this.words});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(title)),
    body: ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: words.length,
      itemBuilder: (_, i) {
        final w = words[i];
        return Card(child: ListTile(
          title: Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
          subtitle: Text([w.ar, if (w.lesson.isNotEmpty) w.lesson].join(' • ')),
          trailing: IconButton(icon: const Icon(Icons.volume_up_rounded), tooltip: 'نطق الكلمة', onPressed: () => store.speak(w.en)),
          onTap: () => showWord(context, store, w, source: words, initialIndex: i),
        ));
      },
    ),
  );
}

class LearnHubPage extends StatelessWidget {
  final Store store;
  const LearnHubPage({super.key, required this.store});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('التعلم والتمرين')),
    body: ListView(padding: const EdgeInsets.all(16), children: [
      Row(children: [
        Expanded(child: QuickCard(icon: Icons.style_rounded, title: 'البطاقات', subtitle: 'تعلم كلمة كلمة', onTap: () => push(context, FlashCardsPage(store: store)))),
        const SizedBox(width: 12),
        Expanded(child: QuickCard(icon: Icons.quiz_rounded, title: 'اختبار ذكي', subtitle: 'اختبر فهمك', onTap: () => push(context, QuizSetupPage(store: store)))),
      ]),
      Row(children: [
        Expanded(child: QuickCard(icon: Icons.psychology_alt_rounded, title: 'الصعبة', subtitle: '${store.difficult.length} تحتاج مراجعة', onTap: () => push(context, DifficultPage(store: store)))),
        const SizedBox(width: 12),
        Expanded(child: QuickCard(icon: Icons.format_quote_rounded, title: 'الجمل', subtitle: 'جمل مع النطق', onTap: () => push(context, SentencesPage(store: store)))),
      ]),
    ]),
  );
}

class MorePage extends StatelessWidget {
  final Store store;
  const MorePage({super.key, required this.store});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('المزيد')),
    body: ListView(padding: const EdgeInsets.all(16), children: [
      SettingsTile(icon: Icons.auto_awesome_rounded, title: 'مختبر الكتاب', subtitle: 'رفع كتاب أو وحدة وتحويلها إلى قاموس منظم', onTap: () => push(context, BookLabPage(store: store))),
      SettingsTile(icon: Icons.insights_rounded, title: 'التقدم والإحصائيات', subtitle: 'تابع الكلمات المتقنة والصعبة', onTap: () => push(context, StatsPage(store: store))),
      SettingsTile(icon: Icons.people_alt_rounded, title: 'ملفات الطلاب', subtitle: 'التبديل بين الطلاب', onTap: () => push(context, ProfilesPage(store: store))),
      SettingsTile(icon: Icons.settings_rounded, title: 'الإعدادات والملفات', subtitle: 'النطق والاستيراد والنسخ الاحتياطي', onTap: () => push(context, SettingsPage(store: store))),
    ]),
  );
}

class BookLabPage extends StatefulWidget {
  final Store store;
  const BookLabPage({super.key, required this.store});
  @override
  State<BookLabPage> createState() => _BookLabPageState();
}

class _BookLabPageState extends State<BookLabPage> {
  String grade = '7';
  String semester = 'الفصل الأول';
  String fileName = '';

  Future<void> pickPdf() async {
    final picked = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['pdf']);
    if (picked == null || picked.files.isEmpty) return;
    setState(() => fileName = picked.files.first.name);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('مختبر الكتاب')),
    body: ListView(padding: const EdgeInsets.all(18), children: [
      Card(child: Padding(padding: const EdgeInsets.all(22), child: Column(children: [
        Icon(Icons.auto_awesome_rounded, size: 62, color: Theme.of(context).colorScheme.primary),
        const SizedBox(height: 12),
        const Text('حوّل كتابًا أو وحدة إلى قاموس منظم', textAlign: TextAlign.center, style: TextStyle(fontSize: 21, fontWeight: FontWeight.w900)),
        const SizedBox(height: 7),
        const Text('ارفع PDF ثم اختر الصف والفصل. ستتم مراجعة الكلمات والجمل قبل إضافتها.', textAlign: TextAlign.center),
      ]))),
      const SizedBox(height: 12),
      DropdownButtonFormField<String>(initialValue: grade, decoration: const InputDecoration(labelText: 'الصف'), items: grades.map((g) => DropdownMenuItem(value: g, child: Text(gradeName(g)))).toList(), onChanged: (v) => setState(() => grade = v ?? '7')),
      const SizedBox(height: 12),
      DropdownButtonFormField<String>(initialValue: semester, decoration: const InputDecoration(labelText: 'الفصل الدراسي'), items: const ['الفصل الأول', 'الفصل الثاني'].map((v) => DropdownMenuItem(value: v, child: Text(v))).toList(), onChanged: (v) => setState(() => semester = v ?? 'الفصل الأول')),
      const SizedBox(height: 14),
      OutlinedButton.icon(onPressed: pickPdf, icon: const Icon(Icons.picture_as_pdf_rounded), label: Text(fileName.isEmpty ? 'اختيار كتاب أو وحدة PDF' : fileName)),
      const SizedBox(height: 14),
      FilledButton.icon(
        onPressed: fileName.isEmpty ? null : () => snack(context, 'تم تجهيز الملف للمعالجة. ربط الاستخراج الذكي سيكون في المرحلة التالية من مختبر الكتاب.'),
        icon: const Icon(Icons.auto_awesome_rounded),
        label: const Text('بدء التحليل الذكي'),
      ),
      const SizedBox(height: 12),
      const Text('لن تُضاف أي كلمة مباشرة. ستظهر شاشة مراجعة تتضمن الكلمة، المعنى، الجملة، الترجمة، الوحدة، الدرس ورقم الصفحة قبل الاعتماد.', textAlign: TextAlign.center, style: TextStyle(color: Color(0xff64748b), height: 1.5)),
    ]),
  );
}

'''
s = s[:start] + new_shell + s[end:]

# Home screen: include fast access to search/curriculum/book lab and use a brighter Jordan identity.
old_rows = """            Row(children: [
              Expanded(child: QuickCard(icon: Icons.style, title: 'بطاقات سريعة', subtitle: 'راجع من آخر كلمة', onTap: () => push(context, FlashCardsPage(store: store)))),
              const SizedBox(width: 12),
              Expanded(child: QuickCard(icon: Icons.quiz_outlined, title: 'اختبار ذكي', subtitle: '20 سؤالاً متنوعاً', onTap: () => push(context, QuizSetupPage(store: store)))),
            ]),
            Row(children: [
              Expanded(child: QuickCard(icon: Icons.warning_amber_rounded, title: 'الكلمات الصعبة', subtitle: '${store.difficult.length} كلمة', onTap: () => push(context, DifficultPage(store: store)))),
              const SizedBox(width: 12),
              Expanded(child: QuickCard(icon: Icons.people_alt_outlined, title: 'الملفات الشخصية', subtitle: '${store.profiles.length} ملفات', onTap: () => push(context, ProfilesPage(store: store)))),
            ]),
"""
new_rows = """            Row(children: [
              Expanded(child: QuickCard(icon: Icons.search_rounded, title: 'ابحث عن كلمة', subtitle: 'نتائج لحظية مع كل حرف', onTap: () => push(context, SmartSearchPage(store: store)))),
              const SizedBox(width: 12),
              Expanded(child: QuickCard(icon: Icons.auto_stories_rounded, title: 'المنهاج', subtitle: 'صف • فصل • وحدة • درس', onTap: () => push(context, CurriculumPage(store: store)))),
            ]),
            Row(children: [
              Expanded(child: QuickCard(icon: Icons.style_rounded, title: 'بطاقات سريعة', subtitle: 'تعلم مع النطق', onTap: () => push(context, FlashCardsPage(store: store)))),
              const SizedBox(width: 12),
              Expanded(child: QuickCard(icon: Icons.quiz_rounded, title: 'اختبار ذكي', subtitle: 'اختبر فهمك', onTap: () => push(context, QuizSetupPage(store: store)))),
            ]),
            Row(children: [
              Expanded(child: QuickCard(icon: Icons.auto_awesome_rounded, title: 'مختبر الكتاب', subtitle: 'ارفع PDF وحوله لقاموس', onTap: () => push(context, BookLabPage(store: store)))),
              const SizedBox(width: 12),
              Expanded(child: QuickCard(icon: Icons.insights_rounded, title: 'تقدمي', subtitle: '${store.mastered.length} كلمة متقنة', onTap: () => push(context, StatsPage(store: store)))),
            ]),
"""
if old_rows in s:
    s = s.replace(old_rows, new_rows, 1)

# Friendly Jordan-school naming in backups/exports without breaking format compatibility.
s = s.replace("'app': 'قاموسي المدرسي'", "'app': 'القاموس المدرسي الأردني'")
s = s.replace("subject: 'كلمات قاموسي المدرسي'", "subject: 'كلمات القاموس المدرسي الأردني'")

p.write_text(s, encoding='utf-8')
print('Applied Jordan School Dictionary v3.0.0 redesign')
