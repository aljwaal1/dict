import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

const grades = ['KG', '1', '2', '3', '4', '5', '6', '7', '8'];
const appVersion = '2.0.0';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.dark,
  ));
  runApp(const QamoosiApp());
}

class QamoosiApp extends StatelessWidget {
  const QamoosiApp({super.key});

  @override
  Widget build(BuildContext context) {
    const seed = Color(0xff1769e0);
    final scheme = ColorScheme.fromSeed(seedColor: seed, brightness: Brightness.light);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'قاموسي المدرسي',
      locale: const Locale('ar'),
      supportedLocales: const [Locale('ar'), Locale('en')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: scheme,
        scaffoldBackgroundColor: const Color(0xfff4f8ff),
        fontFamily: 'sans',
        appBarTheme: const AppBarTheme(
          elevation: 0,
          centerTitle: true,
          backgroundColor: Colors.transparent,
          foregroundColor: Color(0xff14213d),
          titleTextStyle: TextStyle(fontSize: 21, fontWeight: FontWeight.w800, color: Color(0xff14213d)),
        ),
        cardTheme: CardThemeData(
          color: Colors.white,
          elevation: 0,
          margin: const EdgeInsets.symmetric(vertical: 6),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
            side: const BorderSide(color: Color(0xffe3ecfb)),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: BorderSide.none),
          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color: Color(0xffe3ecfb))),
          focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color: seed, width: 1.6)),
        ),
      ),
      home: const AppBootstrap(),
    );
  }
}

class WordItem {
  final int id;
  final String grade;
  final String en;
  final String ar;
  final String exampleEn;
  final String exampleAr;

  const WordItem({required this.id, required this.grade, required this.en, required this.ar, this.exampleEn = '', this.exampleAr = ''});

  factory WordItem.fromJson(Map<String, dynamic> j) => WordItem(
        id: int.tryParse('${j['id'] ?? 0}') ?? 0,
        grade: normalizeGrade('${j['grade'] ?? ''}'),
        en: '${j['word_en'] ?? j['word'] ?? ''}'.trim(),
        ar: '${j['meaning_ar'] ?? j['meaning'] ?? ''}'.trim(),
        exampleEn: '${j['example_en'] ?? j['example'] ?? ''}'.trim(),
        exampleAr: '${j['example_ar'] ?? j['translation'] ?? ''}'.trim(),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'grade': grade,
        'word_en': en,
        'meaning_ar': ar,
        'example_en': exampleEn,
        'example_ar': exampleAr,
      };
}

class Profile {
  final int id;
  String name;
  Profile(this.id, this.name);
  Map<String, dynamic> toJson() => {'id': id, 'name': name};
  factory Profile.fromJson(Map<String, dynamic> j) => Profile(int.tryParse('${j['id']}') ?? 1, '${j['name'] ?? 'الطالب'}');
}

class Store extends ChangeNotifier {
  final tts = FlutterTts();
  late SharedPreferences prefs;
  List<WordItem> words = [];
  List<Profile> profiles = [];
  int activeProfile = 1;
  bool sound = true;
  double points = 0;
  Set<String> mastered = {};
  Set<String> difficult = {};
  Map<String, int> wrongCounts = {};
  Map<String, int> lastIndexByGrade = {};
  String query = '';

  String get pkey => 'p$activeProfile';

  Future<void> init() async {
    prefs = await SharedPreferences.getInstance();
    sound = prefs.getBool('sound') ?? true;
    activeProfile = prefs.getInt('activeProfile') ?? 1;
    final rawProfiles = prefs.getString('profiles');
    profiles = rawProfiles == null
        ? [Profile(1, 'الطالب 1')]
        : (jsonDecode(rawProfiles) as List).map((e) => Profile.fromJson(Map<String, dynamic>.from(e))).toList();
    await _loadWords();
    await loadProgress();
    await tts.setLanguage('en-US');
    await tts.setSpeechRate(.42);
  }

  Future<void> _loadWords() async {
    final raw = prefs.getString('words_json') ?? await rootBundle.loadString('assets/data/words.json');
    final data = jsonDecode(raw) as Map<String, dynamic>;
    words = (data['words'] as List? ?? [])
        .map((e) => WordItem.fromJson(Map<String, dynamic>.from(e)))
        .where((w) => w.en.isNotEmpty && w.ar.isNotEmpty && grades.contains(w.grade))
        .toList(growable: true);
  }

  Future<void> persistWords() => prefs.setString('words_json', jsonEncode({'version': 2, 'words': words.map((e) => e.toJson()).toList()}));

  Future<void> loadProgress() async {
    mastered = (prefs.getStringList('$pkey.mastered') ?? []).toSet();
    difficult = (prefs.getStringList('$pkey.difficult') ?? []).toSet();
    wrongCounts = _readMap('$pkey.wrongCounts');
    lastIndexByGrade = _readMap('$pkey.lastIndex');
    points = prefs.getDouble('$pkey.points') ?? 0;
    notifyListeners();
  }

  Map<String, int> _readMap(String key) {
    try {
      final map = jsonDecode(prefs.getString(key) ?? '{}') as Map<String, dynamic>;
      return map.map((k, v) => MapEntry(k, int.tryParse('$v') ?? 0));
    } catch (_) {
      return {};
    }
  }

  Future<void> saveProgress() async {
    await Future.wait([
      prefs.setStringList('$pkey.mastered', mastered.toList()),
      prefs.setStringList('$pkey.difficult', difficult.toList()),
      prefs.setString('$pkey.wrongCounts', jsonEncode(wrongCounts)),
      prefs.setString('$pkey.lastIndex', jsonEncode(lastIndexByGrade)),
      prefs.setDouble('$pkey.points', points),
    ]);
    notifyListeners();
  }

  List<WordItem> byGrade(String g) => words.where((w) => w.grade == g).toList(growable: false);
  int masteredGrade(String g) => byGrade(g).where((w) => mastered.contains('${w.id}')).length;
  int lastIndex(String g) => byGrade(g).isEmpty ? 0 : (lastIndexByGrade[g] ?? 0).clamp(0, byGrade(g).length - 1);
  List<WordItem> get filteredWords {
    final q = query.trim().toLowerCase();
    if (q.isEmpty) return words;
    return words.where((w) => w.en.toLowerCase().contains(q) || w.ar.contains(q)).toList(growable: false);
  }

  Future<void> setActive(int id) async {
    activeProfile = id;
    await prefs.setInt('activeProfile', id);
    await loadProgress();
  }

  Future<void> setSound(bool v) async {
    sound = v;
    await prefs.setBool('sound', v);
    notifyListeners();
  }

  Future<void> speak(String text) async {
    if (sound) SystemSound.play(SystemSoundType.click);
    await tts.stop();
    await tts.speak(text);
  }

  Future<void> answer(WordItem word, bool correct) async {
    if (correct) {
      points += .5;
      mastered.add('${word.id}');
    } else {
      difficult.add('${word.id}');
      wrongCounts['${word.id}'] = (wrongCounts['${word.id}'] ?? 0) + 1;
    }
    await saveProgress();
  }

  Future<void> saveLastIndex(String grade, int index) async {
    lastIndexByGrade[grade] = index;
    await saveProgress();
  }

  Map<String, dynamic> _allPrefsSnapshot() {
    final data = <String, dynamic>{};
    for (final key in prefs.getKeys()) {
      final value = prefs.get(key);
      if (value is String || value is bool || value is int || value is double || value is List<String>) data[key] = value;
    }
    return data;
  }

  Future<File> createBackupFile() async {
    final payload = {
      'app': 'قاموسي المدرسي',
      'format': 'qamoosi-backup',
      'formatVersion': 2,
      'appVersion': appVersion,
      'createdAt': DateTime.now().toIso8601String(),
      'preferences': _allPrefsSnapshot(),
      'words': words.map((e) => e.toJson()).toList(),
    };
    final dir = await getTemporaryDirectory();
    final stamp = DateTime.now().toIso8601String().replaceAll(':', '-').split('.').first;
    final file = File('${dir.path}/qamoosi_backup_$stamp.json');
    return file.writeAsString(const JsonEncoder.withIndent('  ').convert(payload), flush: true);
  }

  Future<void> shareBackup() async {
    final file = await createBackupFile();
    await Share.shareXFiles([XFile(file.path)], subject: 'نسخة احتياطية - قاموسي المدرسي', text: 'نسخة احتياطية كاملة للكلمات والتقدم والملفات الشخصية.');
  }

  Future<void> restoreBackup({required bool replace}) async {
    final picked = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['json'], withData: true);
    if (picked == null || picked.files.isEmpty) return;
    final bytes = picked.files.first.bytes;
    if (bytes == null) throw Exception('تعذر قراءة الملف');
    final decoded = jsonDecode(utf8.decode(bytes));
    if (decoded is! Map || decoded['format'] != 'qamoosi-backup') throw Exception('هذا الملف ليس نسخة صحيحة للتطبيق');
    final incoming = Map<String, dynamic>.from(decoded);
    final prefMap = Map<String, dynamic>.from(incoming['preferences'] as Map? ?? {});
    if (replace) await prefs.clear();
    for (final entry in prefMap.entries) {
      final v = entry.value;
      if (v is String) await prefs.setString(entry.key, v);
      if (v is bool) await prefs.setBool(entry.key, v);
      if (v is int) await prefs.setInt(entry.key, v);
      if (v is double) await prefs.setDouble(entry.key, v);
      if (v is List) await prefs.setStringList(entry.key, v.map((e) => '$e').toList());
    }
    if (incoming['words'] is List) {
      final imported = (incoming['words'] as List).map((e) => WordItem.fromJson(Map<String, dynamic>.from(e))).toList();
      if (replace) {
        words = imported;
      } else {
        final index = <String, WordItem>{for (final w in words) '${w.grade}|${w.en.toLowerCase()}': w};
        for (final w in imported) index['${w.grade}|${w.en.toLowerCase()}'] = w;
        words = index.values.toList();
      }
      await persistWords();
    }
    await init();
  }

  Future<void> exportCsv() async {
    final b = StringBuffer('\ufeffgrade,word_en,meaning_ar,example_en,example_ar,mastered,difficult,wrong_count\n');
    String esc(String s) => '"${s.replaceAll('"', '""')}"';
    for (final w in words) {
      b.writeln([w.grade, esc(w.en), esc(w.ar), esc(w.exampleEn), esc(w.exampleAr), mastered.contains('${w.id}'), difficult.contains('${w.id}'), wrongCounts['${w.id}'] ?? 0].join(','));
    }
    final dir = await getTemporaryDirectory();
    final file = await File('${dir.path}/qamoosi_words_${DateTime.now().millisecondsSinceEpoch}.csv').writeAsString(b.toString(), flush: true);
    await Share.shareXFiles([XFile(file.path)], subject: 'كلمات قاموسي المدرسي');
  }
}

class AppBootstrap extends StatefulWidget {
  const AppBootstrap({super.key});
  @override
  State<AppBootstrap> createState() => _AppBootstrapState();
}

class _AppBootstrapState extends State<AppBootstrap> {
  final store = Store();
  bool ready = false;

  @override
  void initState() {
    super.initState();
    store.init().then((_) { if (mounted) setState(() => ready = true); });
  }

  @override
  Widget build(BuildContext context) {
    if (!ready) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    return AnimatedBuilder(animation: store, builder: (_, __) => HomeShell(store: store));
  }
}

class HomeShell extends StatefulWidget {
  final Store store;
  const HomeShell({super.key, required this.store});
  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int index = 0;
  late final pages = [HomePage(store: widget.store), DictionaryPage(store: widget.store), GradesPage(store: widget.store), StatsPage(store: widget.store), SettingsPage(store: widget.store)];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(child: IndexedStack(index: index, children: pages)),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (v) => setState(() => index = v),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'الرئيسية'),
          NavigationDestination(icon: Icon(Icons.search), label: 'القاموس'),
          NavigationDestination(icon: Icon(Icons.school_outlined), selectedIcon: Icon(Icons.school), label: 'الصفوف'),
          NavigationDestination(icon: Icon(Icons.insights_outlined), selectedIcon: Icon(Icons.insights), label: 'التقدم'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: 'الإعدادات'),
        ],
      ),
    );
  }
}

class HomePage extends StatelessWidget {
  final Store store;
  const HomePage({super.key, required this.store});

  @override
  Widget build(BuildContext context) {
    final profile = store.profiles.firstWhere((p) => p.id == store.activeProfile, orElse: () => store.profiles.first);
    final completion = store.words.isEmpty ? 0.0 : store.mastered.length / store.words.length;
    return CustomScrollView(
      slivers: [
        const SliverAppBar(title: Text('قاموسي المدرسي'), floating: true),
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(16, 6, 16, 24),
          sliver: SliverList.list(children: [
            Container(
              padding: const EdgeInsets.all(22),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [Color(0xff1b73e8), Color(0xff24c875)]),
                borderRadius: BorderRadius.circular(30),
                boxShadow: const [BoxShadow(color: Color(0x221767d9), blurRadius: 24, offset: Offset(0, 12))],
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('مرحباً ${profile.name}', style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w900)),
                const SizedBox(height: 8),
                Text('${store.words.length} كلمة • ${store.points.toStringAsFixed(1)} نقطة', style: const TextStyle(color: Colors.white, fontSize: 16)),
                const SizedBox(height: 18),
                ClipRRect(borderRadius: BorderRadius.circular(20), child: LinearProgressIndicator(value: completion, minHeight: 10, backgroundColor: Colors.white24, valueColor: const AlwaysStoppedAnimation(Colors.white))),
                const SizedBox(height: 7),
                Text('تم إتقان ${store.mastered.length} كلمة', style: const TextStyle(color: Colors.white)),
              ]),
            ),
            const SizedBox(height: 18),
            Row(children: [
              Expanded(child: QuickCard(icon: Icons.style, title: 'بطاقات سريعة', subtitle: 'راجع من آخر كلمة', onTap: () => push(context, FlashCardsPage(store: store)))),
              const SizedBox(width: 12),
              Expanded(child: QuickCard(icon: Icons.quiz_outlined, title: 'اختبار ذكي', subtitle: '20 سؤالاً متنوعاً', onTap: () => push(context, QuizSetupPage(store: store)))),
            ]),
            Row(children: [
              Expanded(child: QuickCard(icon: Icons.warning_amber_rounded, title: 'الكلمات الصعبة', subtitle: '${store.difficult.length} كلمة', onTap: () => push(context, DifficultPage(store: store)))),
              const SizedBox(width: 12),
              Expanded(child: QuickCard(icon: Icons.people_alt_outlined, title: 'الملفات الشخصية', subtitle: '${store.profiles.length} ملفات', onTap: () => push(context, ProfilesPage(store: store)))),
            ]),
          ]),
        ),
      ],
    );
  }
}

class QuickCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  const QuickCard({super.key, required this.icon, required this.title, required this.subtitle, required this.onTap});
  @override
  Widget build(BuildContext context) => Card(
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(24),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              CircleAvatar(backgroundColor: Theme.of(context).colorScheme.primaryContainer, child: Icon(icon)),
              const SizedBox(height: 15),
              Text(title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
              const SizedBox(height: 4),
              Text(subtitle, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Color(0xff6f7d94))),
            ]),
          ),
        ),
      );
}

class DictionaryPage extends StatefulWidget {
  final Store store;
  const DictionaryPage({super.key, required this.store});
  @override
  State<DictionaryPage> createState() => _DictionaryPageState();
}

class _DictionaryPageState extends State<DictionaryPage> {
  @override
  Widget build(BuildContext context) {
    final list = widget.store.filteredWords;
    return Scaffold(
      appBar: AppBar(title: const Text('القاموس')),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: TextField(
            onChanged: (v) => setState(() => widget.store.query = v),
            decoration: InputDecoration(prefixIcon: const Icon(Icons.search), hintText: 'ابحث بالعربي أو الإنجليزي', suffixIcon: widget.store.query.isEmpty ? null : IconButton(icon: const Icon(Icons.close), onPressed: () => setState(() => widget.store.query = ''))),
          ),
        ),
        Expanded(
          child: ListView.builder(
            keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
            itemCount: list.length,
            itemBuilder: (_, i) {
              final w = list[i];
              return Card(child: ListTile(
                contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
                title: Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
                subtitle: Text('${w.ar} • ${gradeName(w.grade)}'),
                trailing: IconButton(icon: const Icon(Icons.volume_up_rounded), onPressed: () => widget.store.speak(w.en)),
                onTap: () => showWord(context, widget.store, w),
              ));
            },
          ),
        ),
      ]),
    );
  }
}

class GradesPage extends StatelessWidget {
  final Store store;
  const GradesPage({super.key, required this.store});
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('الصفوف')),
        body: ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: grades.length,
          itemBuilder: (_, i) {
            final g = grades[i], total = store.byGrade(g).length, done = store.masteredGrade(g);
            return Card(child: ListTile(
              contentPadding: const EdgeInsets.all(16),
              leading: CircleAvatar(child: Text(g)),
              title: Text(gradeName(g), style: const TextStyle(fontWeight: FontWeight.w800)),
              subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [const SizedBox(height: 7), LinearProgressIndicator(value: total == 0 ? 0 : done / total), const SizedBox(height: 6), Text('$done من $total كلمة متقنة')]),
              trailing: const Icon(Icons.chevron_left),
              onTap: () => push(context, GradeWordsPage(store: store, grade: g)),
            ));
          },
        ),
      );
}

class GradeWordsPage extends StatelessWidget {
  final Store store;
  final String grade;
  const GradeWordsPage({super.key, required this.store, required this.grade});
  @override
  Widget build(BuildContext context) {
    final list = store.byGrade(grade);
    return Scaffold(
      appBar: AppBar(title: Text(gradeName(grade))),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: list.length,
        itemBuilder: (_, i) {
          final w = list[i];
          return Card(child: ListTile(
            title: Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            subtitle: Text(w.ar),
            trailing: Icon(store.mastered.contains('${w.id}') ? Icons.check_circle : Icons.chevron_left, color: store.mastered.contains('${w.id}') ? Colors.green : null),
            onTap: () async { await store.saveLastIndex(grade, i); if (context.mounted) showWord(context, store, w); },
          ));
        },
      ),
    );
  }
}

class FlashCardsPage extends StatefulWidget {
  final Store store;
  const FlashCardsPage({super.key, required this.store});
  @override
  State<FlashCardsPage> createState() => _FlashCardsPageState();
}

class _FlashCardsPageState extends State<FlashCardsPage> {
  String grade = '1';
  int index = 0;
  bool reveal = false;
  @override
  Widget build(BuildContext context) {
    final list = widget.store.byGrade(grade);
    final w = list.isEmpty ? null : list[index % list.length];
    return Scaffold(
      appBar: AppBar(title: const Text('البطاقات التعليمية')),
      body: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(children: [
          DropdownButtonFormField<String>(value: grade, items: grades.map((g) => DropdownMenuItem(value: g, child: Text(gradeName(g)))).toList(), onChanged: (v) => setState(() { grade = v ?? '1'; index = widget.store.lastIndex(grade); reveal = false; })),
          const SizedBox(height: 22),
          Expanded(child: w == null ? const Center(child: Text('لا توجد كلمات')) : Card(child: InkWell(
            borderRadius: BorderRadius.circular(24),
            onTap: () => setState(() => reveal = !reveal),
            child: Center(child: Padding(padding: const EdgeInsets.all(30), child: AnimatedSwitcher(duration: const Duration(milliseconds: 220), child: reveal
                ? Column(key: const ValueKey(1), mainAxisSize: MainAxisSize.min, children: [Text(w.ar, style: const TextStyle(fontSize: 34, fontWeight: FontWeight.w900)), if (w.exampleAr.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 14), child: Text(w.exampleAr))])
                : Column(key: const ValueKey(2), mainAxisSize: MainAxisSize.min, children: [Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 40, fontWeight: FontWeight.w900)), IconButton(iconSize: 34, icon: const Icon(Icons.volume_up_rounded), onPressed: () => widget.store.speak(w.en)), const Text('اضغط لإظهار المعنى')])))),
          )))),
          const SizedBox(height: 14),
          Row(children: [
            Expanded(child: OutlinedButton.icon(onPressed: w == null ? null : () async { await widget.store.answer(w, false); if (mounted) setState(() { index = (index + 1) % list.length; reveal = false; }); }, icon: const Icon(Icons.refresh), label: const Text('تحتاج مراجعة'))),
            const SizedBox(width: 12),
            Expanded(child: FilledButton.icon(onPressed: w == null ? null : () async { await widget.store.answer(w, true); final next = (index + 1) % list.length; await widget.store.saveLastIndex(grade, next); if (mounted) setState(() { index = next; reveal = false; }); }, icon: const Icon(Icons.check), label: const Text('أتقنتها'))),
          ]),
        ]),
      ),
    );
  }
}

class QuizSetupPage extends StatelessWidget {
  final Store store;
  const QuizSetupPage({super.key, required this.store});
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('اختر الصف')),
        body: ListView(padding: const EdgeInsets.all(16), children: grades.map((g) => Card(child: ListTile(title: Text(gradeName(g)), subtitle: Text('${store.byGrade(g).length} كلمة'), trailing: const Icon(Icons.play_circle_fill), onTap: () => push(context, QuizPage(store: store, grade: g)))).toList()),
      );
}

class QuizPage extends StatefulWidget {
  final Store store;
  final String grade;
  const QuizPage({super.key, required this.store, required this.grade});
  @override
  State<QuizPage> createState() => _QuizPageState();
}

class _QuizPageState extends State<QuizPage> {
  late List<WordItem> questions;
  int i = 0, score = 0;
  @override
  void initState() { super.initState(); questions = [...widget.store.byGrade(widget.grade)]..shuffle(); questions = questions.take(20).toList(); }
  @override
  Widget build(BuildContext context) {
    if (questions.isEmpty) return Scaffold(appBar: AppBar(), body: const Center(child: Text('لا توجد كلمات')));
    if (i >= questions.length) return Scaffold(appBar: AppBar(title: const Text('النتيجة')), body: Center(child: Card(child: Padding(padding: const EdgeInsets.all(30), child: Column(mainAxisSize: MainAxisSize.min, children: [const Icon(Icons.emoji_events, size: 70, color: Colors.amber), Text('$score / ${questions.length}', style: const TextStyle(fontSize: 34, fontWeight: FontWeight.w900)), FilledButton(onPressed: () => Navigator.pop(context), child: const Text('إنهاء'))])))));
    final w = questions[i];
    final choices = <String>{w.ar};
    final pool = widget.store.byGrade(widget.grade);
    while (choices.length < min(4, pool.length)) choices.add(pool[Random().nextInt(pool.length)].ar);
    final options = choices.toList()..shuffle();
    return Scaffold(
      appBar: AppBar(title: Text('السؤال ${i + 1} من ${questions.length}')),
      body: ListView(padding: const EdgeInsets.all(18), children: [
        Card(child: Padding(padding: const EdgeInsets.all(28), child: Column(children: [Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 35, fontWeight: FontWeight.w900)), IconButton(icon: const Icon(Icons.volume_up), onPressed: () => widget.store.speak(w.en))]))),
        ...options.map((o) => Card(child: ListTile(title: Text(o), onTap: () async { final ok = o == w.ar; await widget.store.answer(w, ok); if (ok) score++; if (mounted) setState(() => i++); }))),
      ]),
    );
  }
}

class DifficultPage extends StatelessWidget {
  final Store store;
  const DifficultPage({super.key, required this.store});
  @override
  Widget build(BuildContext context) {
    final list = store.words.where((w) => store.difficult.contains('${w.id}')).toList();
    return Scaffold(appBar: AppBar(title: const Text('الكلمات الصعبة')), body: list.isEmpty ? const Center(child: Text('ممتاز! لا توجد كلمات صعبة')) : ListView.builder(padding: const EdgeInsets.all(16), itemCount: list.length, itemBuilder: (_, i) => Card(child: ListTile(title: Text(list[i].en, textDirection: TextDirection.ltr), subtitle: Text(list[i].ar), onTap: () => showWord(context, store, list[i])))));
  }
}

class StatsPage extends StatelessWidget {
  final Store store;
  const StatsPage({super.key, required this.store});
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('التقدم والإحصائيات')),
        body: ListView(padding: const EdgeInsets.all(16), children: [
          Row(children: [Expanded(child: MetricCard(title: 'النقاط', value: store.points.toStringAsFixed(1), icon: Icons.stars_rounded)), const SizedBox(width: 12), Expanded(child: MetricCard(title: 'المتقنة', value: '${store.mastered.length}', icon: Icons.check_circle))]),
          Row(children: [Expanded(child: MetricCard(title: 'الصعبة', value: '${store.difficult.length}', icon: Icons.warning_rounded)), const SizedBox(width: 12), Expanded(child: MetricCard(title: 'الكلمات', value: '${store.words.length}', icon: Icons.menu_book))]),
          ...grades.map((g) { final total = store.byGrade(g).length, done = store.masteredGrade(g); return Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(gradeName(g), style: const TextStyle(fontWeight: FontWeight.w800)), const SizedBox(height: 9), LinearProgressIndicator(value: total == 0 ? 0 : done / total), const SizedBox(height: 7), Text('$done من $total')]))); }),
        ]),
      );
}

class MetricCard extends StatelessWidget {
  final String title, value;
  final IconData icon;
  const MetricCard({super.key, required this.title, required this.value, required this.icon});
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(children: [Icon(icon, color: Theme.of(context).colorScheme.primary), const SizedBox(height: 10), Text(value, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w900)), Text(title)])));
}

class ProfilesPage extends StatefulWidget {
  final Store store;
  const ProfilesPage({super.key, required this.store});
  @override
  State<ProfilesPage> createState() => _ProfilesPageState();
}

class _ProfilesPageState extends State<ProfilesPage> {
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('الملفات الشخصية')),
        floatingActionButton: widget.store.profiles.length >= 3 ? null : FloatingActionButton.extended(onPressed: () async { final id = [1,2,3].firstWhere((e) => !widget.store.profiles.any((p) => p.id == e)); widget.store.profiles.add(Profile(id, 'الطالب $id')); await widget.store.prefs.setString('profiles', jsonEncode(widget.store.profiles.map((e) => e.toJson()).toList())); await widget.store.setActive(id); if (mounted) setState(() {}); }, icon: const Icon(Icons.add), label: const Text('إضافة ملف')),
        body: ListView(padding: const EdgeInsets.all(16), children: widget.store.profiles.map((p) => Card(child: ListTile(leading: CircleAvatar(child: Text('${p.id}')), title: Text(p.name), trailing: p.id == widget.store.activeProfile ? const Icon(Icons.check_circle, color: Colors.green) : null, onTap: () async { await widget.store.setActive(p.id); if (mounted) setState(() {}); })).toList()),
      );
}

class SettingsPage extends StatelessWidget {
  final Store store;
  const SettingsPage({super.key, required this.store});

  Future<void> restoreDialog(BuildContext context) async {
    final replace = await showDialog<bool>(context: context, builder: (_) => AlertDialog(
      title: const Text('طريقة الاستعادة'),
      content: const Text('الدمج يحافظ على البيانات الحالية ويضيف بيانات النسخة. الاستبدال يمسح بيانات التطبيق الحالية أولاً.'),
      actions: [TextButton(onPressed: () => Navigator.pop(context, null), child: const Text('إلغاء')), OutlinedButton(onPressed: () => Navigator.pop(context, false), child: const Text('دمج')), FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('استبدال'))],
    ));
    if (replace == null) return;
    try { await store.restoreBackup(replace: replace); if (context.mounted) snack(context, 'تمت استعادة النسخة بنجاح'); } catch (e) { if (context.mounted) snack(context, 'فشلت الاستعادة: $e'); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('الإعدادات')),
        body: ListView(padding: const EdgeInsets.all(16), children: [
          Card(child: SwitchListTile(secondary: const Icon(Icons.volume_up_outlined), title: const Text('الأصوات والنطق'), subtitle: const Text('صوت الضغط ونطق الكلمات الإنجليزية'), value: store.sound, onChanged: store.setSound)),
          const SectionTitle('النسخ الاحتياطي ونقل البيانات'),
          SettingsTile(icon: Icons.cloud_upload_outlined, title: 'تصدير نسخة احتياطية كاملة', subtitle: 'الكلمات والتقدم والنقاط والملفات الشخصية', onTap: () async { try { await store.shareBackup(); } catch (e) { if (context.mounted) snack(context, 'تعذر إنشاء النسخة: $e'); } }),
          SettingsTile(icon: Icons.restore_rounded, title: 'استعادة نسخة احتياطية', subtitle: 'يدعم الدمج أو الاستبدال', onTap: () => restoreDialog(context)),
          SettingsTile(icon: Icons.table_view_outlined, title: 'تصدير ملف Excel/CSV', subtitle: 'للمراجعة أو الفتح على الكمبيوتر', onTap: () async { try { await store.exportCsv(); } catch (e) { if (context.mounted) snack(context, 'تعذر التصدير: $e'); } }),
          const SectionTitle('حول التطبيق'),
          const SettingsTile(icon: Icons.info_outline, title: 'قاموسي المدرسي', subtitle: 'الإصدار $appVersion • يعمل دون إنترنت'),
          const Padding(padding: EdgeInsets.all(12), child: Text('نصيحة: أنشئ نسخة احتياطية دورياً واحفظها في Google Drive أو أي مكان آمن.', style: TextStyle(color: Color(0xff6f7d94)))),
        ]),
      );
}

class SectionTitle extends StatelessWidget {
  final String text;
  const SectionTitle(this.text, {super.key});
  @override
  Widget build(BuildContext context) => Padding(padding: const EdgeInsets.fromLTRB(8, 22, 8, 8), child: Text(text, style: TextStyle(fontWeight: FontWeight.w900, color: Theme.of(context).colorScheme.primary)));
}

class SettingsTile extends StatelessWidget {
  final IconData icon;
  final String title, subtitle;
  final VoidCallback? onTap;
  const SettingsTile({super.key, required this.icon, required this.title, required this.subtitle, this.onTap});
  @override
  Widget build(BuildContext context) => Card(child: ListTile(contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7), leading: CircleAvatar(backgroundColor: Theme.of(context).colorScheme.primaryContainer, child: Icon(icon)), title: Text(title, style: const TextStyle(fontWeight: FontWeight.w800)), subtitle: Text(subtitle), trailing: onTap == null ? null : const Icon(Icons.chevron_left), onTap: onTap));
}

void showWord(BuildContext context, Store store, WordItem w) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (_) => SafeArea(child: Padding(
      padding: const EdgeInsets.fromLTRB(24, 10, 24, 28),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 36, fontWeight: FontWeight.w900)),
        IconButton(iconSize: 34, icon: const Icon(Icons.volume_up_rounded), onPressed: () => store.speak(w.en)),
        Text(w.ar, style: const TextStyle(fontSize: 27, fontWeight: FontWeight.w800)),
        if (w.exampleEn.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 18), child: Text(w.exampleEn, textDirection: TextDirection.ltr, textAlign: TextAlign.center, style: const TextStyle(fontSize: 18))),
        if (w.exampleAr.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 8), child: Text(w.exampleAr, textAlign: TextAlign.center)),
      ]),
    )),
  );
}

void push(BuildContext context, Widget page) => Navigator.push(context, MaterialPageRoute(builder: (_) => page));
void snack(BuildContext context, String text) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
String gradeName(String grade) => grade == 'KG' ? 'الروضة' : 'الصف $grade';
String normalizeGrade(String value) {
  final s = value.trim().toUpperCase().replaceAll('GRADE', '').replaceAll('الصف', '').replaceAll('صف', '').replaceAll(RegExp(r'\s+'), '');
  if (s.contains('KG') || s.contains('روضة')) return 'KG';
  final n = RegExp(r'\d+').firstMatch(s)?.group(0);
  return n != null && grades.contains(n) ? n : value.trim();
}
