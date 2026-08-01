import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:excel/excel.dart' as excel_lib;
import 'package:archive/archive.dart';
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
    await tts.setSpeechRate(.38);
    await tts.setPitch(1.0);
    await tts.setVolume(1.0);
    await tts.awaitSpeakCompletion(true);
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

  Future<void> addWord({
    required String english,
    required String arabic,
    required String grade,
    String exampleEnglish = '',
    String exampleArabic = '',
  }) async {
    final cleanEnglish = english.trim();
    final cleanArabic = arabic.trim();
    if (cleanEnglish.isEmpty || cleanArabic.isEmpty) return;
    final nextId = words.isEmpty ? 1 : words.map((w) => w.id).reduce(max) + 1;
    words.add(WordItem(
      id: nextId,
      grade: grade,
      en: cleanEnglish,
      ar: cleanArabic,
      exampleEn: exampleEnglish.trim(),
      exampleAr: exampleArabic.trim(),
    ));
    await persistWords();
    notifyListeners();
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

  Future<int> _mergeImportedWords(List<WordItem> imported) async {
    final valid = imported
        .where((w) => w.en.trim().isNotEmpty && w.ar.trim().isNotEmpty && grades.contains(w.grade))
        .toList();
    final index = <String, WordItem>{
      for (final w in words) '${w.grade}|${w.en.trim().toLowerCase()}': w,
    };
    var added = 0;
    for (final word in valid) {
      final key = '${word.grade}|${word.en.trim().toLowerCase()}';
      if (!index.containsKey(key)) added++;
      index[key] = word;
    }
    words = index.values.toList(growable: true);
    await persistWords();
    notifyListeners();
    return added;
  }

  Future<int> importJsonWords() async {
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['json'],
      withData: true,
    );
    if (picked == null || picked.files.isEmpty) return -1;
    final bytes = picked.files.first.bytes;
    if (bytes == null) throw Exception('تعذر قراءة ملف JSON');
    final decoded = jsonDecode(utf8.decode(bytes));

    dynamic rawWords;
    if (decoded is List) {
      rawWords = decoded;
    } else if (decoded is Map) {
      rawWords = decoded['words'];
      if (rawWords == null && decoded['data'] is Map) {
        rawWords = decoded['data']['words'];
      }
    }
    if (rawWords is! List) {
      throw Exception('لم يتم العثور على قائمة words داخل الملف');
    }

    final imported = <WordItem>[];
    for (final item in rawWords) {
      if (item is Map) {
        imported.add(WordItem.fromJson(Map<String, dynamic>.from(item)));
      }
    }
    if (imported.isEmpty) throw Exception('لا توجد كلمات صالحة في الملف');
    return _mergeImportedWords(imported);
  }

  String _cellText(dynamic value) {
    if (value == null) return '';
    return value.toString().trim();
  }

  String _normalizeHeader(String value) => value
      .trim()
      .toLowerCase()
      .replaceAll(' ', '_')
      .replaceAll('-', '_');

  String _valueByHeaders(Map<String, String> row, List<String> names) {
    for (final name in names) {
      final value = row[_normalizeHeader(name)];
      if (value != null && value.trim().isNotEmpty) return value.trim();
    }
    return '';
  }

  WordItem? _wordFromImportRow(Map<String, String> row, int fallbackId) {
    final en = _valueByHeaders(row, ['word_en', 'english', 'word', 'الكلمة_الإنجليزية', 'الكلمة']);
    final ar = _valueByHeaders(row, ['meaning_ar', 'arabic', 'meaning', 'المعنى_العربي', 'المعنى']);
    if (en.isEmpty || ar.isEmpty) return null;
    final rawGrade = _valueByHeaders(row, ['grade', 'class', 'الصف']);
    final grade = normalizeGrade(rawGrade.isEmpty ? '1' : rawGrade);
    if (!grades.contains(grade)) return null;
    final rawId = _valueByHeaders(row, ['id', 'الرقم']);
    return WordItem(
      id: int.tryParse(rawId) ?? fallbackId,
      grade: grade,
      en: en,
      ar: ar,
      exampleEn: _valueByHeaders(row, ['example_en', 'sentence_en', 'example', 'الجملة_الإنجليزية', 'مثال_إنجليزي']),
      exampleAr: _valueByHeaders(row, ['example_ar', 'sentence_ar', 'translation', 'ترجمة_الجملة', 'مثال_عربي']),
    );
  }

  excel_lib.Excel _decodeExcelCompat(Uint8List bytes) {
    try {
      return excel_lib.Excel.decodeBytes(bytes);
    } catch (_) {
      final archive = ZipDecoder().decodeBytes(bytes, verify: true);
      final repaired = Archive();

      for (final file in archive.files) {
        if (!file.isFile || file.name == 'xl/styles.xml') continue;

        var data = List<int>.from(file.content as List<int>);
        if (file.name == '[Content_Types].xml' ||
            file.name == 'xl/_rels/workbook.xml.rels') {
          var xml = utf8.decode(data, allowMalformed: true);
          xml = xml.replaceAll(
            RegExp(r'<Override[^>]*PartName="/xl/styles.xml"[^>]*/>'),
            '',
          );
          xml = xml.replaceAll(
            RegExp(r'<Relationship[^>]*Type="[^"]*/styles"[^>]*/>'),
            '',
          );
          data = utf8.encode(xml);
        }

        repaired.addFile(ArchiveFile(file.name, data.length, data));
      }

      final encoded = ZipEncoder().encode(repaired);
      if (encoded == null) rethrow;
      return excel_lib.Excel.decodeBytes(Uint8List.fromList(encoded));
    }
  }

  Future<int> importExcelWords() async {
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['xlsx', 'csv'],
      withData: true,
    );
    if (picked == null || picked.files.isEmpty) return -1;
    final file = picked.files.first;
    final bytes = file.bytes;
    if (bytes == null) throw Exception('تعذر قراءة الملف');
    final extension = (file.extension ?? '').toLowerCase();
    final imported = <WordItem>[];
    var nextId = words.isEmpty ? 1 : words.map((w) => w.id).reduce(max) + 1;

    if (extension == 'csv') {
      final lines = const LineSplitter().convert(utf8.decode(bytes).replaceFirst('\ufeff', ''));
      if (lines.isEmpty) throw Exception('ملف CSV فارغ');
      List<String> parseCsvLine(String line) {
        final values = <String>[];
        final current = StringBuffer();
        var quoted = false;
        for (var i = 0; i < line.length; i++) {
          final char = line[i];
          if (char == '"') {
            if (quoted && i + 1 < line.length && line[i + 1] == '"') {
              current.write('"');
              i++;
            } else {
              quoted = !quoted;
            }
          } else if (char == ',' && !quoted) {
            values.add(current.toString());
            current.clear();
          } else {
            current.write(char);
          }
        }
        values.add(current.toString());
        return values;
      }
      final headers = parseCsvLine(lines.first).map(_normalizeHeader).toList();
      for (final line in lines.skip(1)) {
        if (line.trim().isEmpty) continue;
        final values = parseCsvLine(line);
        final row = <String, String>{};
        for (var i = 0; i < headers.length; i++) {
          row[headers[i]] = i < values.length ? values[i].trim() : '';
        }
        final word = _wordFromImportRow(row, nextId);
        if (word != null) {
          imported.add(word);
          nextId++;
        }
      }
    } else {
      final workbook = _decodeExcelCompat(Uint8List.fromList(bytes));
      if (workbook.tables.isEmpty) throw Exception('ملف Excel لا يحتوي على أوراق');
      final sheet = workbook.tables.values.first;
      if (sheet.rows.isEmpty) throw Exception('ورقة Excel فارغة');
      final headers = sheet.rows.first.map((cell) => _normalizeHeader(_cellText(cell?.value))).toList();
      for (final cells in sheet.rows.skip(1)) {
        final row = <String, String>{};
        for (var i = 0; i < headers.length; i++) {
          row[headers[i]] = i < cells.length ? _cellText(cells[i]?.value) : '';
        }
        final word = _wordFromImportRow(row, nextId);
        if (word != null) {
          imported.add(word);
          nextId++;
        }
      }
    }

    if (imported.isEmpty) {
      throw Exception('لم يتم العثور على صفوف صالحة. تأكد من أسماء الأعمدة');
    }
    return _mergeImportedWords(imported);
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
            trailing: Row(
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
            },
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
    final word = list.isEmpty ? null : list[index % list.length];

    return Scaffold(
      appBar: AppBar(title: const Text('البطاقات التعليمية')),
      body: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          children: [
            DropdownButtonFormField<String>(
              initialValue: grade,
              items: grades
                  .map(
                    (g) => DropdownMenuItem<String>(
                      value: g,
                      child: Text(gradeName(g)),
                    ),
                  )
                  .toList(),
              onChanged: (value) {
                setState(() {
                  grade = value ?? '1';
                  index = widget.store.lastIndex(grade);
                  reveal = false;
                });
              },
            ),
            const SizedBox(height: 22),
            Expanded(
              child: word == null
                  ? const Center(child: Text('لا توجد كلمات'))
                  : Card(
                      child: InkWell(
                        borderRadius: BorderRadius.circular(24),
                        onTap: () => setState(() => reveal = !reveal),
                        child: Center(
                          child: Padding(
                            padding: const EdgeInsets.all(30),
                            child: AnimatedSwitcher(
                              duration: const Duration(milliseconds: 220),
                              child: reveal
                                  ? Column(
                                      key: const ValueKey(1),
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Text(
                                          word.ar,
                                          style: const TextStyle(
                                            fontSize: 34,
                                            fontWeight: FontWeight.w900,
                                          ),
                                        ),
                                        if (word.exampleAr.isNotEmpty)
                                          Padding(
                                            padding: const EdgeInsets.only(top: 14),
                                            child: Text(word.exampleAr),
                                          ),
                                      ],
                                    )
                                  : Column(
                                      key: const ValueKey(2),
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Text(
                                          word.en,
                                          textDirection: TextDirection.ltr,
                                          style: const TextStyle(
                                            fontSize: 40,
                                            fontWeight: FontWeight.w900,
                                          ),
                                        ),
                                        IconButton(
                                          iconSize: 34,
                                          icon: const Icon(Icons.volume_up_rounded),
                                          onPressed: () => widget.store.speak(word.en),
                                        ),
                                        const Text('اضغط لإظهار المعنى'),
                                      ],
                                    ),
                            ),
                          ),
                        ),
                      ),
                    ),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: word == null
                        ? null
                        : () async {
                            await widget.store.answer(word, false);
                            if (!mounted) return;
                            setState(() {
                              index = (index + 1) % list.length;
                              reveal = false;
                            });
                          },
                    icon: const Icon(Icons.refresh),
                    label: const Text('تحتاج مراجعة'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: word == null
                        ? null
                        : () async {
                            await widget.store.answer(word, true);
                            final next = (index + 1) % list.length;
                            await widget.store.saveLastIndex(grade, next);
                            if (!mounted) return;
                            setState(() {
                              index = next;
                              reveal = false;
                            });
                          },
                    icon: const Icon(Icons.check),
                    label: const Text('أتقنتها'),
                  ),
                ),
              ],
            ),
          ],
        ),
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
        body: ListView(padding: const EdgeInsets.all(16), children: grades.map((g) => Card(child: ListTile(title: Text(gradeName(g)), subtitle: Text('${store.byGrade(g).length} كلمة'), trailing: const Icon(Icons.play_circle_fill), onTap: () => push(context, QuizPage(store: store, grade: g))))).toList()),
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
    return Scaffold(appBar: AppBar(title: const Text('الكلمات الصعبة')), body: list.isEmpty ? const Center(child: Text('ممتاز! لا توجد كلمات صعبة')) : ListView.builder(padding: const EdgeInsets.all(16), itemCount: list.length, itemBuilder: (_, i) => Card(child: ListTile(
      title: Text(list[i].en, textDirection: TextDirection.ltr),
      subtitle: Text(list[i].ar),
      trailing: IconButton(
        tooltip: 'نطق الكلمة',
        icon: const Icon(Icons.volume_up_rounded),
        onPressed: () => store.speak(list[i].en),
      ),
      onTap: () => showWord(context, store, list[i]),
    ))));
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
        body: ListView(padding: const EdgeInsets.all(16), children: widget.store.profiles.map((p) => Card(child: ListTile(leading: CircleAvatar(child: Text('${p.id}')), title: Text(p.name), trailing: p.id == widget.store.activeProfile ? const Icon(Icons.check_circle, color: Colors.green) : null, onTap: () async { await widget.store.setActive(p.id); if (mounted) setState(() {}); }))).toList()),
      );
}

class AddWordPage extends StatefulWidget {
  final Store store;
  const AddWordPage({super.key, required this.store});

  @override
  State<AddWordPage> createState() => _AddWordPageState();
}

class _AddWordPageState extends State<AddWordPage> {
  final english = TextEditingController();
  final arabic = TextEditingController();
  final exampleEnglish = TextEditingController();
  final exampleArabic = TextEditingController();
  String grade = '1';

  @override
  void dispose() {
    english.dispose();
    arabic.dispose();
    exampleEnglish.dispose();
    exampleArabic.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('إضافة كلمة')),
        body: ListView(
          padding: const EdgeInsets.all(18),
          children: [
            DropdownButtonFormField<String>(
              initialValue: grade,
              items: grades.map((g) => DropdownMenuItem(value: g, child: Text(gradeName(g)))).toList(),
              onChanged: (value) => setState(() => grade = value ?? '1'),
              decoration: const InputDecoration(labelText: 'الصف'),
            ),
            const SizedBox(height: 12),
            TextField(controller: english, textDirection: TextDirection.ltr, decoration: const InputDecoration(labelText: 'الكلمة الإنجليزية')),
            const SizedBox(height: 12),
            TextField(controller: arabic, decoration: const InputDecoration(labelText: 'المعنى العربي')),
            const SizedBox(height: 12),
            TextField(controller: exampleEnglish, textDirection: TextDirection.ltr, decoration: const InputDecoration(labelText: 'جملة إنجليزية - اختياري')),
            const SizedBox(height: 12),
            TextField(controller: exampleArabic, decoration: const InputDecoration(labelText: 'ترجمة الجملة - اختياري')),
            const SizedBox(height: 22),
            FilledButton.icon(
              onPressed: () async {
                if (english.text.trim().isEmpty || arabic.text.trim().isEmpty) {
                  snack(context, 'اكتب الكلمة والمعنى أولاً');
                  return;
                }
                await widget.store.addWord(
                  english: english.text,
                  arabic: arabic.text,
                  grade: grade,
                  exampleEnglish: exampleEnglish.text,
                  exampleArabic: exampleArabic.text,
                );
                if (context.mounted) Navigator.pop(context);
              },
              icon: const Icon(Icons.save_rounded),
              label: const Text('حفظ الكلمة'),
            ),
          ],
        ),
      );
}

class SentencesPage extends StatelessWidget {
  final Store store;
  const SentencesPage({super.key, required this.store});

  @override
  Widget build(BuildContext context) {
    final items = store.words.where((w) => w.exampleEn.isNotEmpty || w.exampleAr.isNotEmpty).toList();
    return Scaffold(
      appBar: AppBar(title: const Text('الجمل التعليمية')),
      body: items.isEmpty
          ? const Center(child: Text('لا توجد جمل مضافة بعد'))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: items.length,
              itemBuilder: (_, index) {
                final word = items[index];
                final sentence = word.exampleEn.isEmpty ? word.en : word.exampleEn;
                return Card(
                  child: ListTile(
                    contentPadding: const EdgeInsets.all(16),
                    title: Text(sentence, textDirection: TextDirection.ltr),
                    subtitle: Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(word.exampleAr.isEmpty ? word.ar : word.exampleAr),
                    ),
                    trailing: IconButton(
                      tooltip: 'نطق الجملة',
                      icon: const Icon(Icons.volume_up_rounded),
                      onPressed: () => store.speak(sentence),
                    ),
                    onTap: () => showWord(context, store, word),
                  ),
                );
              },
            ),
    );
  }
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
          ),
          const SectionTitle('إدارة المحتوى'),
          SettingsTile(icon: Icons.add_circle_outline_rounded, title: 'إضافة كلمة', subtitle: 'إضافة كلمة ومعنى وجملة مثال', onTap: () => push(context, AddWordPage(store: store))),
          SettingsTile(icon: Icons.people_alt_outlined, title: 'إدارة الملفات الشخصية', subtitle: 'إضافة طالب أو التبديل بين الملفات', onTap: () => push(context, ProfilesPage(store: store))),
          SettingsTile(icon: Icons.format_quote_rounded, title: 'الجمل التعليمية', subtitle: 'عرض الجمل الإنجليزية وترجمتها مع النطق', onTap: () => push(context, SentencesPage(store: store))),
          const SectionTitle('النسخ الاحتياطي ونقل البيانات'),
          SettingsTile(
            icon: Icons.data_object_rounded,
            title: 'رفع ملف JSON',
            subtitle: 'استيراد الكلمات ودمجها دون تكرار',
            onTap: () async {
              try {
                final count = await store.importJsonWords();
                if (!context.mounted || count < 0) return;
                snack(context, count == 0 ? 'تم تحديث الكلمات الموجودة دون إضافة مكررات' : 'تم استيراد $count كلمة جديدة');
              } catch (e) {
                if (context.mounted) snack(context, 'تعذر استيراد JSON: $e');
              }
            },
          ),
          SettingsTile(
            icon: Icons.upload_file_rounded,
            title: 'رفع ملف Excel أو CSV',
            subtitle: 'يدعم XLSX وCSV مع دمج الكلمات تلقائياً',
            onTap: () async {
              try {
                final count = await store.importExcelWords();
                if (!context.mounted || count < 0) return;
                snack(context, count == 0 ? 'تم تحديث الكلمات الموجودة دون إضافة مكررات' : 'تم استيراد $count كلمة جديدة');
              } catch (e) {
                if (context.mounted) snack(context, 'تعذر استيراد الملف: $e');
              }
            },
          ),
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

void push(BuildContext context, Widget page) => Navigator.push(context, MaterialPageRoute(builder: (_) => page));
void snack(BuildContext context, String text) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
String gradeName(String grade) => grade == 'KG' ? 'الروضة' : 'الصف $grade';
String normalizeGrade(String value) {
  final s = value.trim().toUpperCase().replaceAll('GRADE', '').replaceAll('الصف', '').replaceAll('صف', '').replaceAll(RegExp(r'\s+'), '');
  if (s.contains('KG') || s.contains('روضة')) return 'KG';
  final n = RegExp(r'\d+').firstMatch(s)?.group(0);
  return n != null && grades.contains(n) ? n : value.trim();
}
