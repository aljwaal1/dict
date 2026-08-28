from pathlib import Path
import re

main = Path('lib/main.dart')
s = main.read_text(encoding='utf-8')

s = s.replace("const appVersion = '3.4.4';", "const appVersion = '3.4.5';")

# Faster cold start: initialize only what is needed to paint the first frame.
s = s.replace(
"""Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await pdfrxFlutterInitialize();
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.dark,
  ));
  runApp(const QamoosiApp());
}
""",
"""Future<void>? _pdfRuntimeInit;
Future<void> ensurePdfRuntime() => _pdfRuntimeInit ??= pdfrxFlutterInitialize();

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.dark,
    systemNavigationBarColor: Colors.white,
    systemNavigationBarIconBrightness: Brightness.dark,
  ));
  runApp(const QamoosiApp());
}
""")

# Professional visual polish: lighter canvas, tighter controls, calmer radii.
s = s.replace("scaffoldBackgroundColor: const Color(0xfff4f8ff),", "scaffoldBackgroundColor: const Color(0xfff7f9fc),")
s = s.replace("titleTextStyle: TextStyle(fontSize: 21, fontWeight: FontWeight.w800, color: Color(0xff14213d)),", "titleTextStyle: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: -.2, color: Color(0xff14213d)),")
s = s.replace("borderRadius: BorderRadius.circular(24),", "borderRadius: BorderRadius.circular(20),", 1)
s = s.replace("borderRadius: BorderRadius.circular(18), borderSide: BorderSide.none", "borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none")
s = s.replace("borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color: Color(0xffe3ecfb))", "borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: Color(0xffe3ecfb))")
s = s.replace("borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color: seed, width: 1.6)", "borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: seed, width: 1.5)")
s = s.replace("minimumSize: const Size(64, 52),", "minimumSize: const Size(64, 48),")
s = s.replace("borderRadius: BorderRadius.circular(16)", "borderRadius: BorderRadius.circular(14)")
s = s.replace("height: 72,", "height: 68,")
s = s.replace("elevation: 2,", "elevation: 1,")

# Do not block app opening on TTS configuration/warm-up. TTS is already lazy-safe in speak().
old_init_tail = """    onProgress?.call('جاري استعادة تقدمك وإعداداتك…', .62, freshInstall);
    await loadProgress();
    onProgress?.call('جاري تجهيز النطق والترجمة…', .80, freshInstall);
    await _configureTts();
    await _prepareTts();
    onProgress?.call('جاهز تقريبًا…', .98, freshInstall);
"""
new_init_tail = """    onProgress?.call('جاري استعادة تقدمك وإعداداتك…', .72, freshInstall);
    await loadProgress();
    onProgress?.call('جاهز…', .98, freshInstall);
"""
if old_init_tail not in s:
    raise SystemExit('Store.init tail not found')
s = s.replace(old_init_tail, new_init_tail)
s = s.replace("onProgress?.call('جاري تجهيز قاموس الكلمات…', .38, freshInstall);", "onProgress?.call('جاري تجهيز الكلمات…', .42, freshInstall);")

# Optimize search so edit distance is calculated once per candidate rather than repeatedly during sort/filter.
old_search = """  List<WordItem> smartSearch(String value) {
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
    final result = words.where((w) => rank(w) < 99).toList(growable: false);
    result.sort((a, b) {
      final r = rank(a).compareTo(rank(b));
      if (r != 0) return r;
      return a.en.toLowerCase().compareTo(b.en.toLowerCase());
    });
    return result;
  }
"""
new_search = """  List<WordItem> smartSearch(String value) {
    final q = value.trim().toLowerCase();
    if (q.isEmpty) return const [];
    int rank(WordItem w) {
      final en = w.en.toLowerCase();
      final ar = w.ar.toLowerCase();
      if (en == q || ar == q) return 0;
      if (en.startsWith(q) || ar.startsWith(q)) return 1;
      if (en.contains(q) || ar.contains(q)) return 2;
      if (q.length >= 3 && (en.length - q.length).abs() <= 2 && _editDistance(en, q) <= (q.length >= 6 ? 2 : 1)) return 3;
      if (w.exampleEn.toLowerCase().contains(q) || w.exampleAr.toLowerCase().contains(q)) return 4;
      return 99;
    }
    final scored = <MapEntry<WordItem, int>>[];
    for (final word in words) {
      final r = rank(word);
      if (r < 99) scored.add(MapEntry(word, r));
    }
    scored.sort((a, b) {
      final r = a.value.compareTo(b.value);
      if (r != 0) return r;
      return a.key.en.toLowerCase().compareTo(b.key.en.toLowerCase());
    });
    return scored.map((e) => e.key).toList(growable: false);
  }
"""
if old_search not in s:
    raise SystemExit('smartSearch block not found')
s = s.replace(old_search, new_search)

# Lazy-create tab pages: only Home is built at launch; other tabs are created after first visit.
old_shell = """class _HomeShellState extends State<HomeShell> {
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
"""
new_shell = """class _HomeShellState extends State<HomeShell> {
  int index = 0;
  late final List<Widget?> pages = <Widget?>[
    HomePage(store: widget.store),
    null,
    null,
    null,
    null,
  ];

  Widget _createPage(int i) => switch (i) {
    0 => HomePage(store: widget.store),
    1 => SmartSearchPage(store: widget.store),
    2 => CurriculumPage(store: widget.store),
    3 => LearnHubPage(store: widget.store),
    _ => MorePage(store: widget.store),
  };

  void _selectPage(int value) {
    if (value == index) return;
    setState(() {
      pages[value] ??= _createPage(value);
      index = value;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: IndexedStack(
          index: index,
          children: List<Widget>.generate(pages.length, (i) => pages[i] ?? const SizedBox.shrink()),
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: _selectPage,
"""
if old_shell not in s:
    raise SystemExit('HomeShell block not found')
s = s.replace(old_shell, new_shell)

# Lazy PDF runtime: pay the initialization cost only when the user opens a PDF.
needle = """    setState(() { busy = true; fileName = file.name; candidates = []; pagesRead = 0; });
    try {
      final document = await PdfDocument.openFile(file.path!);
"""
replace = """    setState(() { busy = true; fileName = file.name; candidates = []; pagesRead = 0; });
    try {
      await ensurePdfRuntime();
      final document = await PdfDocument.openFile(file.path!);
"""
if needle not in s:
    raise SystemExit('PDF open block not found')
s = s.replace(needle, replace)

# Naming consistency and cleaner customer-facing copy.
s = s.replace("return speak('Welcome to Qamoosi AI, the smart dictionary for Arab students');", "return speak('Welcome to Easy English AI');")
s = s.replace("appBar: AppBar(title: const Text('بحث AI الذكي'))", "appBar: AppBar(title: const Text('AI بحث'))")
s = s.replace("appBar: AppBar(title: const Text('المفردات حسب الصف'))", "appBar: AppBar(title: const Text('الصفوف والمفردات'))")
s = s.replace("title: 'التقدم والإحصائيات', subtitle: 'تابع الكلمات المتقنة والصعبة'", "title: 'التقدم', subtitle: 'ملخص واضح للكلمات المتقنة والتي تحتاج مراجعة'")
s = s.replace("title: 'ملفات الطلاب', subtitle: 'التبديل بين الطلاب'", "title: 'الطلاب', subtitle: 'إدارة الملفات والتبديل بين الطلاب'")
s = s.replace("title: 'الإعدادات والملفات', subtitle: 'النطق والاستيراد والنسخ الاحتياطي'", "title: 'الإعدادات والبيانات', subtitle: 'النطق والاستيراد والنسخ الاحتياطي'")
s = s.replace("subject: 'نسخة احتياطية - قاموسي المدرسي'", "subject: 'نسخة احتياطية - Easy English AI'")
s = s.replace("qamoosi_backup_", "easy_english_ai_backup_")
s = s.replace("qamoosi_words_", "easy_english_ai_words_")
s = s.replace("firstInstallPreparing\n                        ? 'في أول تشغيل يحتاج التطبيق إلى لحظات لتجهيز الكلمات والنطق وخدمات الترجمة. الرجاء الانتظار قليلًا ولا تغلق التطبيق.'\n                        : 'نحمّل بياناتك ونجهّز أدوات التعلم. لن يستغرق ذلك طويلًا.'", "firstInstallPreparing\n                        ? 'يتم تجهيز بيانات التطبيق لأول استخدام. سيبدأ تلقائيًا خلال لحظات.'\n                        : 'نجهّز بياناتك…'")

main.write_text(s, encoding='utf-8')

pub = Path('pubspec.yaml')
ps = pub.read_text(encoding='utf-8')
ps = ps.replace('version: 3.4.4+33', 'version: 3.4.5+34')
pub.write_text(ps, encoding='utf-8')

print('Easy English AI v3.4.5 performance/UX upgrade applied')
