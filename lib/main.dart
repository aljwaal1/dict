import 'dart:convert';
import 'dart:math';

import 'package:excel/excel.dart' as xls;
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

const String developerEmail = 'yaya15112016@gmail.com';
const String dictionaryJsonUrl = 'https://raw.githubusercontent.com/YOUR_USER/qamoosi-school-content/main/words.json';
const List<String> gradesList = ['KG', '1', '2', '3', '4', '5', '6', '7', '8'];

void main() => runApp(const QamoosiApp());

class QamoosiApp extends StatelessWidget {
  const QamoosiApp({super.key});

  @override
  Widget build(BuildContext context) {
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
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff42a5f5)),
        scaffoldBackgroundColor: const Color(0xfff7fbff),
        cardTheme: CardThemeData(
          elevation: 0,
          color: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
        ),
      ),
      home: const AppRoot(),
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
  final String source;

  const WordItem({
    required this.id,
    required this.grade,
    required this.en,
    required this.ar,
    this.exampleEn = '',
    this.exampleAr = '',
    this.source = '',
  });

  factory WordItem.fromJson(Map<String, dynamic> json) {
    return WordItem(
      id: int.tryParse('${json['id'] ?? 0}') ?? 0,
      grade: normalizeGrade('${json['grade'] ?? ''}'),
      en: '${json['word_en'] ?? json['word'] ?? ''}'.trim(),
      ar: '${json['meaning_ar'] ?? json['meaning'] ?? ''}'.trim(),
      exampleEn: '${json['example_en'] ?? json['example'] ?? ''}'.trim(),
      exampleAr: '${json['example_ar'] ?? json['translation'] ?? ''}'.trim(),
      source: '${json['source'] ?? ''}',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'grade': grade,
        'word_en': en,
        'meaning_ar': ar,
        'example_en': exampleEn,
        'example_ar': exampleAr,
        'source': source,
      };

  String difficultyText() {
    final length = en.replaceAll(' ', '').length;
    if (length <= 5) return 'سهل';
    if (length <= 9) return 'متوسط';
    return 'صعب';
  }
}

class Profile {
  final int id;
  String name;
  Profile(this.id, this.name);

  Map<String, dynamic> toJson() => {'id': id, 'name': name};
  factory Profile.fromJson(Map<String, dynamic> json) => Profile(json['id'] as int, '${json['name']}');
}

class ImportSummary {
  final int total;
  final int added;
  final int updated;
  final int skipped;

  const ImportSummary({required this.total, required this.added, required this.updated, required this.skipped});

  String get message => 'تم استيراد Excel بنجاح\nالإجمالي: $total\nإضافة: $added\nتحديث: $updated\nتجاهل: $skipped';
}

class Store extends ChangeNotifier {
  final FlutterTts tts = FlutterTts();
  SharedPreferences? prefs;

  List<WordItem> words = [];
  List<Profile> profiles = [];
  int activeProfile = 1;
  bool sound = true;
  double points = 0;
  Set<String> mastered = {};
  Set<String> difficult = {};
  Map<String, int> wrongCounts = {};
  Map<String, int> lastIndexByGrade = {};

  String get key => 'p$activeProfile';

  Future<void> init() async {
    prefs = await SharedPreferences.getInstance();
    sound = prefs!.getBool('sound') ?? true;
    activeProfile = prefs!.getInt('activeProfile') ?? 1;
    final savedProfiles = prefs!.getString('profiles');
    profiles = savedProfiles == null
        ? [Profile(1, 'الطالب 1')]
        : (jsonDecode(savedProfiles) as List).map((e) => Profile.fromJson(Map<String, dynamic>.from(e))).toList();
    await _loadWords();
    await loadProgress();
    await tts.setLanguage('en-US');
    await tts.setSpeechRate(0.42);
  }

  Future<void> _loadWords() async {
    final saved = prefs!.getString('words_json');
    final text = saved ?? await rootBundle.loadString('assets/data/words.json');
    final data = jsonDecode(text) as Map<String, dynamic>;
    final rawWords = data['words'] as List;
    words = rawWords
        .map((e) => WordItem.fromJson(Map<String, dynamic>.from(e)))
        .where((w) => w.en.isNotEmpty && w.ar.isNotEmpty && gradesList.contains(w.grade))
        .toList();
  }

  Future<void> _persistWords() async {
    await prefs!.setString('words_json', jsonEncode({'version': 2, 'words': words.map((w) => w.toJson()).toList()}));
  }

  Future<void> loadProgress() async {
    mastered = (prefs!.getStringList('$key.mastered') ?? []).toSet();
    difficult = (prefs!.getStringList('$key.difficult') ?? []).toSet();
    wrongCounts = _readIntMap('$key.wrongCounts');
    lastIndexByGrade = _readIntMap('$key.lastIndex');
    points = prefs!.getDouble('$key.points') ?? 0;
    notifyListeners();
  }

  Map<String, int> _readIntMap(String prefKey) {
    final raw = jsonDecode(prefs!.getString(prefKey) ?? '{}') as Map<String, dynamic>;
    return raw.map((k, v) => MapEntry(k, int.tryParse('$v') ?? 0));
  }

  Future<void> saveProgress() async {
    await prefs!.setStringList('$key.mastered', mastered.toList());
    await prefs!.setStringList('$key.difficult', difficult.toList());
    await prefs!.setString('$key.wrongCounts', jsonEncode(wrongCounts));
    await prefs!.setString('$key.lastIndex', jsonEncode(lastIndexByGrade));
    await prefs!.setDouble('$key.points', points);
    notifyListeners();
  }

  Future<void> saveProfiles() async {
    await prefs!.setString('profiles', jsonEncode(profiles.map((p) => p.toJson()).toList()));
    notifyListeners();
  }

  Future<void> setActive(int id) async {
    activeProfile = id;
    await prefs!.setInt('activeProfile', id);
    await loadProgress();
  }

  Future<void> setSound(bool value) async {
    sound = value;
    await prefs!.setBool('sound', value);
    notifyListeners();
  }

  List<WordItem> byGrade(String grade) => words.where((w) => w.grade == grade).toList();

  int masteredGrade(String grade) => byGrade(grade).where((w) => mastered.contains('${w.id}')).length;

  int lastIndex(String grade) {
    final total = byGrade(grade).length;
    if (total == 0) return 0;
    return (lastIndexByGrade[grade] ?? 0).clamp(0, total - 1).toInt();
  }

  Future<void> saveLastIndex(String grade, int index) async {
    lastIndexByGrade[grade] = index;
    await saveProgress();
  }

  Future<void> resetLastIndex(String grade) async {
    lastIndexByGrade[grade] = 0;
    await saveProgress();
  }

  Future<void> click() async {
    if (sound) await SystemSound.play(SystemSoundType.click);
  }

  Future<void> revealSound() async {
    if (!sound) return;
    await SystemSound.play(SystemSoundType.click);
    await Future.delayed(const Duration(milliseconds: 70));
    await SystemSound.play(SystemSoundType.click);
  }

  Future<void> successSound() async {
    if (!sound) return;
    await SystemSound.play(SystemSoundType.click);
    await Future.delayed(const Duration(milliseconds: 90));
    await SystemSound.play(SystemSoundType.click);
  }

  Future<void> wrongSound() async {
    if (sound) await SystemSound.play(SystemSoundType.click);
  }

  Future<void> speak(String text) async {
    await click();
    await tts.stop();
    await tts.speak(text);
  }

  Future<void> answer(WordItem word, bool ok) async {
    if (ok) {
      points += .5;
      mastered.add('${word.id}');
    } else {
      difficult.add('${word.id}');
      wrongCounts['${word.id}'] = (wrongCounts['${word.id}'] ?? 0) + 1;
    }
    await saveProgress();
  }

  Future<void> addWord(String en, String ar, String grade, {String exampleEn = '', String exampleAr = ''}) async {
    final next = (words.map((e) => e.id).fold<int>(0, max)) + 1;
    words.add(WordItem(id: next, grade: grade, en: en.trim(), ar: ar.trim(), exampleEn: exampleEn.trim(), exampleAr: exampleAr.trim(), source: 'manual'));
    await _persistWords();
    notifyListeners();
  }

  Future<String> updateFromUrl() async {
    final response = await http.get(Uri.parse(dictionaryJsonUrl));
    if (response.statusCode != 200) throw Exception('تعذر تحميل ملف JSON');
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    if (data['words'] is! List) throw Exception('ملف JSON غير صحيح');
    words = (data['words'] as List)
        .map((e) => WordItem.fromJson(Map<String, dynamic>.from(e)))
        .where((w) => w.en.isNotEmpty && w.ar.isNotEmpty && gradesList.contains(w.grade))
        .toList();
    await _persistWords();
    notifyListeners();
    return 'تم تحديث القاموس من JSON: ${words.length} كلمة';
  }

  Future<ImportSummary?> importExcelManually() async {
    final picked = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['xlsx'], withData: true);
    if (picked == null || picked.files.isEmpty) return null;
    final bytes = picked.files.first.bytes;
    if (bytes == null) throw Exception('تعذر قراءة ملف Excel');

    final book = xls.Excel.decodeBytes(bytes);
    final index = <String, int>{};
    for (var i = 0; i < words.length; i++) {
      index['${words[i].grade}|${words[i].en.toLowerCase()}'] = i;
    }

    var added = 0;
    var updated = 0;
    var skipped = 0;
    var total = 0;
    var nextId = (words.map((e) => e.id).fold<int>(0, max)) + 1;

    for (final sheetName in book.tables.keys) {
      final sheet = book.tables[sheetName];
      if (sheet == null || sheet.rows.isEmpty) continue;

      final header = sheet.rows.first.map(cellText).map(cleanHeader).toList();
      int findCol(List<String> names) {
        for (final name in names) {
          final i = header.indexOf(cleanHeader(name));
          if (i >= 0) return i;
        }
        return -1;
      }

      final gradeCol = findCol(['grade', 'الصف', 'صف']);
      final wordCol = findCol(['word_en', 'word', 'الكلمة', 'كلمة', 'english word']);
      final meaningCol = findCol(['meaning_ar', 'meaning', 'المعنى', 'معنى', 'arabic meaning']);
      final exampleEnCol = findCol(['example_en', 'example', 'جملة مثال', 'مثال بالإنجليزية', 'مثال انجليزي']);
      final exampleArCol = findCol(['example_ar', 'translation', 'ترجمة الجملة', 'ترجمة المثال']);

      if (wordCol < 0 || meaningCol < 0) {
        skipped += max(0, sheet.rows.length - 1);
        continue;
      }

      for (var rowIndex = 1; rowIndex < sheet.rows.length; rowIndex++) {
        final row = sheet.rows[rowIndex];
        String valueAt(int col) => col >= 0 && col < row.length ? cellText(row[col]).trim() : '';
        final en = valueAt(wordCol);
        final ar = valueAt(meaningCol);
        final grade = normalizeGrade(gradeCol >= 0 ? valueAt(gradeCol) : sheetName);
        if (en.isEmpty || ar.isEmpty || !gradesList.contains(grade)) {
          skipped++;
          continue;
        }

        total++;
        final key = '$grade|${en.toLowerCase()}';
        final oldIndex = index[key];
        final item = WordItem(
          id: oldIndex == null ? nextId++ : words[oldIndex].id,
          grade: grade,
          en: en,
          ar: ar,
          exampleEn: valueAt(exampleEnCol),
          exampleAr: valueAt(exampleArCol),
          source: 'excel',
        );
        if (oldIndex == null) {
          words.add(item);
          index[key] = words.length - 1;
          added++;
        } else {
          words[oldIndex] = item;
          updated++;
        }
      }
    }

    await _persistWords();
    notifyListeners();
    return ImportSummary(total: total, added: added, updated: updated, skipped: skipped);
  }
}

class AppRoot extends StatefulWidget {
  const AppRoot({super.key});

  @override
  State<AppRoot> createState() => _AppRootState();
}

class _AppRootState extends State<AppRoot> {
  final Store store = Store();
  bool ready = false;

  @override
  void initState() {
    super.initState();
    store.init().then((_) => setState(() => ready = true));
  }

  @override
  Widget build(BuildContext context) {
    if (!ready) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    return AnimatedBuilder(animation: store, builder: (_, __) => HomePage(store: store));
  }
}

class PageFrame extends StatelessWidget {
  final String title;
  final Widget child;
  const PageFrame({super.key, required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title), centerTitle: true),
      body: Column(children: [adBox('مساحة إعلان علوية - لاحقاً'), Expanded(child: child), adBox('مساحة إعلان سفلية - لاحقاً')]),
    );
  }
}

Widget adBox(String text) => Container(
      height: 42,
      margin: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
      decoration: BoxDecoration(color: const Color(0xfffff8e1), borderRadius: BorderRadius.circular(16), border: Border.all(color: const Color(0xffffecb3))),
      child: Center(child: Text(text, style: const TextStyle(color: Colors.orange, fontWeight: FontWeight.bold))),
    );

class HomePage extends StatelessWidget {
  final Store store;
  const HomePage({super.key, required this.store});

  @override
  Widget build(BuildContext context) {
    final profile = store.profiles.firstWhere((p) => p.id == store.activeProfile, orElse: () => store.profiles.first);
    return PageFrame(
      title: 'قاموسي المدرسي',
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: ListTile(
              leading: const CircleAvatar(child: Icon(Icons.school)),
              title: Text('أهلاً ${profile.name}'),
              subtitle: Text('النقاط: ${store.points.toStringAsFixed(1)} | الكلمات: ${store.words.length}'),
            ),
          ),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.15,
            children: [
              tile(context, 'الصفوف', Icons.grid_view, GradesPage(store: store)),
              tile(context, 'القاموس', Icons.search, DictionaryPage(store: store)),
              tile(context, 'إضافة كلمة', Icons.add_circle, AddWordPage(store: store)),
              tile(context, 'البطاقات', Icons.style, FlashPage(store: store)),
              tile(context, 'الاختبار', Icons.quiz, QuizSetupPage(store: store)),
              tile(context, 'الكلمات الصعبة', Icons.warning_amber, DifficultPage(store: store)),
              tile(context, 'الإحصائيات', Icons.bar_chart, StatsPage(store: store)),
              tile(context, 'الملف الشخصي', Icons.person, ProfilesPage(store: store)),
              tile(context, 'الإعدادات والتواصل', Icons.settings, SettingsPage(store: store)),
            ],
          ),
        ],
      ),
    );
  }

  Widget tile(BuildContext context, String title, IconData icon, Widget page) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(22),
        onTap: () async {
          await store.click();
          if (context.mounted) push(context, page);
        },
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(icon, size: 38, color: Theme.of(context).colorScheme.primary), const SizedBox(height: 10), Text(title, style: const TextStyle(fontWeight: FontWeight.bold))]),
      ),
    );
  }
}

class GradesPage extends StatelessWidget {
  final Store store;
  const GradesPage({super.key, required this.store});

  @override
  Widget build(BuildContext context) {
    return PageFrame(
      title: 'الصفوف',
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: gradesList.length,
        itemBuilder: (_, i) {
          final grade = gradesList[i];
          final total = store.byGrade(grade).length;
          final done = store.masteredGrade(grade);
          return Card(
            child: ListTile(
              title: Text(gradeName(grade), style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('$done / $total كلمة متقنة'), if (total > 0) Text('آخر وصول: الكلمة ${store.lastIndex(grade) + 1} من $total'), LinearProgressIndicator(value: total == 0 ? 0 : done / total)]),
              trailing: const Icon(Icons.arrow_forward_ios),
              onTap: () => push(context, GradeWordsPage(store: store, grade: grade)),
            ),
          );
        },
      ),
    );
  }
}

class GradeWordsPage extends StatefulWidget {
  final Store store;
  final String grade;
  const GradeWordsPage({super.key, required this.store, required this.grade});

  @override
  State<GradeWordsPage> createState() => _GradeWordsPageState();
}

class _GradeWordsPageState extends State<GradeWordsPage> {
  late final ScrollController controller;

  @override
  void initState() {
    super.initState();
    controller = ScrollController(initialScrollOffset: widget.store.lastIndex(widget.grade) * 86.0);
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final list = widget.store.byGrade(widget.grade);
    final last = widget.store.lastIndex(widget.grade);
    if (list.isEmpty) return PageFrame(title: gradeName(widget.grade), child: const Center(child: Text('لا توجد كلمات في هذا الصف')));
    return PageFrame(
      title: gradeName(widget.grade),
      child: ListView.builder(
        controller: controller,
        padding: const EdgeInsets.all(16),
        itemCount: list.length + 1,
        itemBuilder: (_, i) {
          if (i == 0) {
            return Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  Text('آخر وصول: الكلمة ${last + 1} من ${list.length}', style: const TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  ElevatedButton.icon(onPressed: () => controller.animateTo(last * 86.0, duration: const Duration(milliseconds: 300), curve: Curves.easeOut), icon: const Icon(Icons.play_arrow), label: const Text('متابعة من حيث توقفت')),
                  TextButton.icon(
                    onPressed: () async {
                      await widget.store.resetLastIndex(widget.grade);
                      if (mounted) setState(() {});
                      controller.animateTo(0, duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
                    },
                    icon: const Icon(Icons.restart_alt),
                    label: const Text('ابدأ الصف من البداية'),
                  ),
                ]),
              ),
            );
          }
          final wordIndex = i - 1;
          final word = list[wordIndex];
          return Card(
            child: ListTile(
              title: Text(word.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              subtitle: Text('الكلمة ${wordIndex + 1} | ${word.difficultyText()}'),
              trailing: IconButton(icon: const Icon(Icons.volume_up), onPressed: () => widget.store.speak(word.en)),
              onTap: () async {
                await widget.store.saveLastIndex(widget.grade, wordIndex);
                if (context.mounted) push(context, WordCardPage(store: widget.store, word: word));
              },
            ),
          );
        },
      ),
    );
  }
}

class WordCardPage extends StatefulWidget {
  final Store store;
  final WordItem word;
  const WordCardPage({super.key, required this.store, required this.word});

  @override
  State<WordCardPage> createState() => _WordCardPageState();
}

class _WordCardPageState extends State<WordCardPage> {
  bool show = false;

  @override
  Widget build(BuildContext context) {
    return PageFrame(
      title: 'بطاقة كلمة',
      child: Center(
        child: Card(
          margin: const EdgeInsets.all(20),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              InkWell(onTap: () => widget.store.speak(widget.word.en), child: Text(widget.word.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 36, fontWeight: FontWeight.bold))),
              const SizedBox(height: 18),
              ElevatedButton.icon(onPressed: () async { await widget.store.revealSound(); setState(() => show = !show); }, icon: const Icon(Icons.translate), label: Text(show ? 'إخفاء المعنى' : 'إظهار المعنى')),
              if (show) Padding(padding: const EdgeInsets.all(18), child: WordDetails(word: widget.word)),
            ]),
          ),
        ),
      ),
    );
  }
}

class WordDetails extends StatelessWidget {
  final WordItem word;
  const WordDetails({super.key, required this.word});

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Text(word.ar, textAlign: TextAlign.center, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
      if (word.exampleEn.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 12), child: Text(word.exampleEn, textDirection: TextDirection.ltr, textAlign: TextAlign.center, style: const TextStyle(fontSize: 18))),
      if (word.exampleAr.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 6), child: Text(word.exampleAr, textAlign: TextAlign.center)),
    ]);
  }
}

class DictionaryPage extends StatefulWidget {
  final Store store;
  const DictionaryPage({super.key, required this.store});

  @override
  State<DictionaryPage> createState() => _DictionaryPageState();
}

class _DictionaryPageState extends State<DictionaryPage> {
  String q = '';

  @override
  Widget build(BuildContext context) {
    final list = widget.store.words.where((w) => w.en.toLowerCase().contains(q.toLowerCase()) || w.ar.contains(q)).take(100).toList();
    return PageFrame(
      title: 'القاموس',
      child: Column(children: [
        Padding(padding: const EdgeInsets.all(12), child: TextField(decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: 'ابحث عن كلمة...', border: OutlineInputBorder()), onChanged: (value) => setState(() => q = value))),
        Expanded(child: ListView.builder(itemCount: list.length, itemBuilder: (_, i) => WordSearchTile(store: widget.store, word: list[i]))),
      ]),
    );
  }
}

class WordSearchTile extends StatefulWidget {
  final Store store;
  final WordItem word;
  const WordSearchTile({super.key, required this.store, required this.word});

  @override
  State<WordSearchTile> createState() => _WordSearchTileState();
}

class _WordSearchTileState extends State<WordSearchTile> {
  bool show = false;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          InkWell(onTap: () => widget.store.speak(widget.word.en), child: Text(widget.word.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold))),
          const SizedBox(height: 8),
          ElevatedButton(onPressed: () async { await widget.store.revealSound(); setState(() => show = !show); }, child: Text(show ? 'إخفاء المعنى' : 'إظهار المعنى')),
          if (show) WordDetails(word: widget.word),
        ]),
      ),
    );
  }
}

class AddWordPage extends StatefulWidget {
  final Store store;
  const AddWordPage({super.key, required this.store});

  @override
  State<AddWordPage> createState() => _AddWordPageState();
}

class _AddWordPageState extends State<AddWordPage> {
  final en = TextEditingController();
  final ar = TextEditingController();
  final exampleEn = TextEditingController();
  final exampleAr = TextEditingController();
  String grade = 'KG';

  @override
  Widget build(BuildContext context) {
    return PageFrame(
      title: 'إضافة كلمة',
      child: ListView(padding: const EdgeInsets.all(18), children: [
        DropdownButtonFormField<String>(value: grade, items: gradesList.map((g) => DropdownMenuItem<String>(value: g, child: Text(gradeName(g)))).toList(), onChanged: (v) => setState(() => grade = v ?? 'KG')),
        TextField(controller: en, decoration: const InputDecoration(labelText: 'English word'), textDirection: TextDirection.ltr),
        TextField(controller: ar, decoration: const InputDecoration(labelText: 'المعنى العربي')),
        TextField(controller: exampleEn, decoration: const InputDecoration(labelText: 'جملة مثال - اختياري'), textDirection: TextDirection.ltr),
        TextField(controller: exampleAr, decoration: const InputDecoration(labelText: 'ترجمة الجملة - اختياري')),
        const SizedBox(height: 20),
        ElevatedButton(onPressed: () async { if (en.text.trim().isEmpty || ar.text.trim().isEmpty) return; await widget.store.addWord(en.text, ar.text, grade, exampleEn: exampleEn.text, exampleAr: exampleAr.text); if (context.mounted) Navigator.pop(context); }, child: const Text('حفظ')),
      ]),
    );
  }
}

class FlashPage extends StatelessWidget {
  final Store store;
  const FlashPage({super.key, required this.store});

  @override
  Widget build(BuildContext context) {
    return PageFrame(title: 'البطاقات التعليمية', child: ListView(padding: const EdgeInsets.all(16), children: gradesList.map((g) => Card(child: ListTile(title: Text(gradeName(g)), subtitle: Text('${store.byGrade(g).length} كلمة | آخر وصول: ${store.lastIndex(g) + 1}'), trailing: const Icon(Icons.style), onTap: () => push(context, FlashRunPage(store: store, grade: g))))).toList()));
  }
}

class FlashRunPage extends StatefulWidget {
  final Store store;
  final String grade;
  const FlashRunPage({super.key, required this.store, required this.grade});

  @override
  State<FlashRunPage> createState() => _FlashRunPageState();
}

class _FlashRunPageState extends State<FlashRunPage> {
  late int index;
  bool show = false;

  @override
  void initState() {
    super.initState();
    index = widget.store.lastIndex(widget.grade);
  }

  @override
  Widget build(BuildContext context) {
    final list = widget.store.byGrade(widget.grade);
    if (list.isEmpty) return PageFrame(title: 'بطاقات ${gradeName(widget.grade)}', child: const Center(child: Text('لا توجد كلمات في هذا الصف')));
    final word = list[index % list.length];
    return PageFrame(
      title: 'بطاقات ${gradeName(widget.grade)}',
      child: Center(
        child: Card(
          margin: const EdgeInsets.all(20),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Text('${index + 1} / ${list.length}'),
              const SizedBox(height: 12),
              InkWell(onTap: () => widget.store.speak(word.en), child: Text(word.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 36, fontWeight: FontWeight.bold))),
              const SizedBox(height: 18),
              ElevatedButton(onPressed: () async { await widget.store.revealSound(); setState(() => show = !show); }, child: Text(show ? 'إخفاء المعنى' : 'إظهار المعنى')),
              if (show) Padding(padding: const EdgeInsets.all(12), child: WordDetails(word: word)),
              ElevatedButton.icon(onPressed: () async { final next = (index + 1) % list.length; await widget.store.saveLastIndex(widget.grade, next); setState(() { index = next; show = false; }); }, icon: const Icon(Icons.navigate_next), label: const Text('التالي')),
            ]),
          ),
        ),
      ),
    );
  }
}

class QuizSetupPage extends StatelessWidget {
  final Store store;
  const QuizSetupPage({super.key, required this.store});

  @override
  Widget build(BuildContext context) {
    return PageFrame(title: 'الاختبار', child: ListView(padding: const EdgeInsets.all(16), children: gradesList.map((g) => Card(child: Column(children: [ListTile(title: Text(gradeName(g)), subtitle: const Text('English → Arabic'), trailing: const Icon(Icons.play_arrow), onTap: () => push(context, QuizPage(store: store, grade: g, enToAr: true))), ListTile(title: Text(gradeName(g)), subtitle: const Text('Arabic → English'), trailing: const Icon(Icons.play_arrow), onTap: () => push(context, QuizPage(store: store, grade: g, enToAr: false)))]))).toList()));
  }
}

class QuizPage extends StatefulWidget {
  final Store store;
  final String grade;
  final bool enToAr;
  const QuizPage({super.key, required this.store, required this.grade, required this.enToAr});

  @override
  State<QuizPage> createState() => _QuizPageState();
}

class _QuizPageState extends State<QuizPage> {
  late List<WordItem> questions;
  int idx = 0;
  int ok = 0;
  int bad = 0;
  final rand = Random();

  @override
  void initState() {
    super.initState();
    questions = [...widget.store.byGrade(widget.grade)]..shuffle();
    questions = questions.take(20).toList();
  }

  @override
  Widget build(BuildContext context) {
    if (questions.isEmpty) return PageFrame(title: 'اختبار ${gradeName(widget.grade)}', child: const Center(child: Text('لا توجد كلمات للاختبار')));
    if (idx >= questions.length) return ResultPage(total: questions.length, ok: ok, bad: bad);
    final word = questions[idx];
    final options = <String>{widget.enToAr ? word.ar : word.en};
    while (options.length < 4 && widget.store.words.isNotEmpty) {
      final randomWord = widget.store.words[rand.nextInt(widget.store.words.length)];
      options.add(widget.enToAr ? randomWord.ar : randomWord.en);
    }
    final list = options.toList()..shuffle();
    return PageFrame(
      title: 'اختبار ${gradeName(widget.grade)}',
      child: ListView(padding: const EdgeInsets.all(18), children: [
        Text('السؤال ${idx + 1} / ${questions.length}', style: const TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 20),
        Card(child: Padding(padding: const EdgeInsets.all(24), child: Column(children: [Text(widget.enToAr ? word.en : word.ar, textDirection: widget.enToAr ? TextDirection.ltr : TextDirection.rtl, style: const TextStyle(fontSize: 30, fontWeight: FontWeight.bold)), if (widget.enToAr) IconButton(icon: const Icon(Icons.volume_up), onPressed: () => widget.store.speak(word.en))]))),
        ...list.map((option) => Card(child: ListTile(title: Text(option, textDirection: widget.enToAr ? TextDirection.rtl : TextDirection.ltr), onTap: () async { final correct = option == (widget.enToAr ? word.ar : word.en); await widget.store.answer(word, correct); if (correct) { await widget.store.successSound(); } else { await widget.store.wrongSound(); } setState(() { if (correct) ok++; else bad++; idx++; }); }))),
      ]),
    );
  }
}

class ResultPage extends StatelessWidget {
  final int total;
  final int ok;
  final int bad;
  const ResultPage({super.key, required this.total, required this.ok, required this.bad});

  @override
  Widget build(BuildContext context) {
    return PageFrame(title: 'نتيجة الاختبار', child: Center(child: Card(margin: const EdgeInsets.all(20), child: Padding(padding: const EdgeInsets.all(24), child: Column(mainAxisSize: MainAxisSize.min, children: [const Icon(Icons.emoji_events, size: 60, color: Colors.amber), Text('عدد الأسئلة: $total'), Text('الصحيح: $ok'), Text('الخطأ: $bad'), Text('النقاط المكتسبة: ${(ok * .5).toStringAsFixed(1)}'), ElevatedButton(onPressed: () => Navigator.pop(context), child: const Text('العودة'))])))));
  }
}

class DifficultPage extends StatelessWidget {
  final Store store;
  const DifficultPage({super.key, required this.store});

  @override
  Widget build(BuildContext context) {
    final list = store.words.where((w) => store.difficult.contains('${w.id}')).toList();
    return PageFrame(title: 'الكلمات الصعبة', child: list.isEmpty ? const Center(child: Text('لا توجد كلمات صعبة بعد')) : ListView(children: list.map((w) => WordSearchTile(store: store, word: w)).toList()));
  }
}

class StatsPage extends StatelessWidget {
  final Store store;
  const StatsPage({super.key, required this.store});

  @override
  Widget build(BuildContext context) {
    return PageFrame(title: 'الإحصائيات', child: ListView(padding: const EdgeInsets.all(16), children: [Card(child: ListTile(title: const Text('النقاط'), trailing: Text(store.points.toStringAsFixed(1)))), Card(child: ListTile(title: const Text('الكلمات الصعبة'), trailing: Text('${store.difficult.length}'))), ...gradesList.map((g) { final total = store.byGrade(g).length; final done = store.masteredGrade(g); return Card(child: ListTile(title: Text(gradeName(g)), subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [LinearProgressIndicator(value: total == 0 ? 0 : done / total), if (total > 0) Text('آخر وصول: ${store.lastIndex(g) + 1} / $total')]), trailing: Text('$done/$total'))); })]));
  }
}

class ProfilesPage extends StatefulWidget {
  final Store store;
  const ProfilesPage({super.key, required this.store});

  @override
  State<ProfilesPage> createState() => _ProfilesPageState();
}

class _ProfilesPageState extends State<ProfilesPage> {
  Future<void> addProfile() async {
    if (widget.store.profiles.length >= 3) {
      msg(context, 'الحد الأعلى 3 ملفات فقط');
      return;
    }
    final nextId = List.generate(3, (i) => i + 1).firstWhere((id) => !widget.store.profiles.any((p) => p.id == id), orElse: () => widget.store.profiles.length + 1);
    final profile = Profile(nextId, 'الطالب $nextId');
    widget.store.profiles.add(profile);
    await widget.store.saveProfiles();
    await widget.store.setActive(profile.id);
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return PageFrame(title: 'الملفات الشخصية', child: ListView(padding: const EdgeInsets.all(16), children: [
      ...widget.store.profiles.map((p) => Card(child: ListTile(leading: Icon(p.id == widget.store.activeProfile ? Icons.check_circle : Icons.person, color: p.id == widget.store.activeProfile ? Colors.green : null), title: Text(p.name), subtitle: Text(p.id == widget.store.activeProfile ? 'محدد حالياً' : 'اضغط لاختياره'), onTap: () async { await widget.store.setActive(p.id); if (mounted) setState(() {}); }))),
      if (widget.store.profiles.length < 3) ElevatedButton.icon(onPressed: addProfile, icon: const Icon(Icons.add), label: const Text('إضافة ملف جديد')),
    ]));
  }
}

class SettingsPage extends StatelessWidget {
  final Store store;
  const SettingsPage({super.key, required this.store});

  @override
  Widget build(BuildContext context) {
    return PageFrame(title: 'الإعدادات والتواصل', child: ListView(padding: const EdgeInsets.all(16), children: [
      SwitchListTile(title: const Text('أصوات الضغط والتفاعل'), value: store.sound, onChanged: (v) async { await store.setSound(v); if (v) await store.successSound(); }),
      Card(child: ListTile(leading: const Icon(Icons.update), title: const Text('تحديث القاموس من GitHub JSON'), subtitle: const Text('هذا هو الخيار الأساسي للتحديث عن بعد'), onTap: () async { try { final m = await store.updateFromUrl(); if (context.mounted) msg(context, m); } catch (_) { if (context.mounted) msg(context, 'فشل التحديث. غيّر رابط JSON داخل main.dart لاحقاً.'); } })),
      Card(child: ListTile(leading: const Icon(Icons.table_chart), title: const Text('استيراد Excel يدوي - خيار إضافي'), subtitle: const Text('يبقى JSON هو الأساسي. Excel للرفع اليدوي من الهاتف فقط.'), onTap: () async { try { final s = await store.importExcelManually(); if (context.mounted && s != null) msg(context, s.message); } catch (e) { if (context.mounted) msg(context, 'فشل استيراد Excel: $e'); } })),
      Card(child: ListTile(leading: const Icon(Icons.email), title: const Text('إرسال بريد للمطور'), onTap: () => launchUrl(Uri.parse('mailto:$developerEmail?subject=قاموسي المدرسي')))),
      const Padding(padding: EdgeInsets.all(12), child: Text('الإصدار 1.2.1 - متابعة من آخر كلمة - JSON أساسي - Excel يدوي اختياري')),
    ]));
  }
}

void push(BuildContext context, Widget page) => Navigator.push(context, MaterialPageRoute(builder: (_) => page));
void msg(BuildContext context, String text) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
String gradeName(String grade) => grade == 'KG' ? 'الروضة' : 'الصف $grade';
String cleanHeader(String value) => value.trim().toLowerCase().replaceAll('_', '').replaceAll(' ', '');
String normalizeGrade(String value) {
  final s = value.trim().toUpperCase().replaceAll('GRADE', '').replaceAll('الصف', '').replaceAll('صف', '').replaceAll(RegExp(r'\s+'), '');
  if (s.contains('KG') || s.contains('روضة')) return 'KG';
  final n = RegExp(r'\d+').firstMatch(s)?.group(0);
  if (n != null && gradesList.contains(n)) return n;
  return value.trim();
}
String cellText(xls.Data? data) => '${data?.value ?? ''}'.trim();
