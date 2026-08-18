import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:archive/archive.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:path_provider/path_provider.dart';
import 'package:pdfrx/pdfrx.dart';
import 'package:share_plus/share_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:xml/xml.dart';

const grades = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];
const appVersion = '3.1.2';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await pdfrxFlutterInitialize();
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
      title: 'القاموس المدرسي الأردني',
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
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            minimumSize: const Size(64, 52),
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
            tapTargetSize: MaterialTapTargetSize.padded,
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            minimumSize: const Size(64, 52),
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            side: const BorderSide(color: Color(0xffcbd9ee)),
            textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
            tapTargetSize: MaterialTapTargetSize.padded,
          ),
        ),
        textButtonTheme: TextButtonThemeData(
          style: TextButton.styleFrom(
            minimumSize: const Size(48, 48),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
            tapTargetSize: MaterialTapTargetSize.padded,
          ),
        ),
        iconButtonTheme: IconButtonThemeData(
          style: IconButton.styleFrom(
            minimumSize: const Size(48, 48),
            padding: const EdgeInsets.all(12),
            tapTargetSize: MaterialTapTargetSize.padded,
          ),
        ),
        navigationBarTheme: const NavigationBarThemeData(
          height: 72,
          labelTextStyle: WidgetStatePropertyAll(TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700)),
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

  factory WordItem.fromJson(Map<String, dynamic> j) => WordItem(
        id: int.tryParse('${j['id'] ?? 0}') ?? 0,
        grade: normalizeGrade('${j['grade'] ?? ''}'),
        en: '${j['word_en'] ?? j['word'] ?? ''}'.trim(),
        ar: '${j['meaning_ar'] ?? j['meaning'] ?? ''}'.trim(),
        exampleEn: '${j['example_en'] ?? j['sentence_en'] ?? j['exampleEnglish'] ?? j['example_english'] ?? j['sentenceEnglish'] ?? j['sentence_english'] ?? j['exampleSentence'] ?? j['example_sentence'] ?? j['book_example'] ?? j['example'] ?? j['sentence'] ?? j['جملة مثال'] ?? j['مثال من الكتاب'] ?? j['الجملة الإنجليزية'] ?? ''}'.trim(),
        exampleAr: '${j['example_ar'] ?? j['sentence_ar'] ?? j['exampleArabic'] ?? j['example_arabic'] ?? j['sentenceArabic'] ?? j['sentence_arabic'] ?? j['sentenceTranslation'] ?? j['sentence_translation'] ?? j['translation'] ?? j['ترجمة الجملة'] ?? j['ترجمة المثال'] ?? j['ترجمة المثال إلى العربية'] ?? ''}'.trim(),
        semester: '${j['semester'] ?? j['term'] ?? j['الفصل الدراسي'] ?? j['الفصل_الدراسي'] ?? ''}'.trim(),
        unit: '${j['unit'] ?? j['الوحدة'] ?? ''}'.trim(),
        lesson: '${j['lesson'] ?? j['الدرس'] ?? ''}'.trim(),
        sourcePage: '${j['page'] ?? j['source_page'] ?? j['رقم الصفحة'] ?? j['الصفحة'] ?? ''}'.trim(),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'grade': grade,
        'word_en': en,
        'meaning_ar': ar,
        'example_en': exampleEn,
        'example_ar': exampleAr,
        'semester': semester,
        'unit': unit,
        'lesson': lesson,
        'source_page': sourcePage,
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
  bool ttsReady = false;
  bool freshInstall = false;
  String ttsLanguage = 'en-US';
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
    freshInstall = prefs.getBool('installation_initialized') != true;
    await prefs.setBool('installation_initialized', true);
    sound = prefs.getBool('sound') ?? true;
    activeProfile = prefs.getInt('activeProfile') ?? 1;
    final rawProfiles = prefs.getString('profiles');
    profiles = rawProfiles == null
        ? [Profile(1, 'الطالب 1')]
        : (jsonDecode(rawProfiles) as List).map((e) => Profile.fromJson(Map<String, dynamic>.from(e))).toList();
    await _loadWords();
    await loadProgress();
    await _configureTts();
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
  List<WordItem> byCurriculum({required String grade, String semester = '', String unit = '', String lesson = ''}) => words.where((w) {
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

  Future<bool> speak(String text) async {
    final value = text.trim();
    if (!sound || value.isEmpty) return false;
    try {
      if (!ttsReady && !await _configureTts()) return false;
      await tts.stop();
      await tts.setLanguage(ttsLanguage);
      await tts.setSpeechRate(.42);
      await tts.setPitch(1.0);
      await tts.setVolume(1.0);
      final result = await tts.speak(value);
      return result == 1 || result == true || result == null;
    } catch (_) {
      ttsReady = false;
      if (!await _configureTts()) return false;
      try {
        final result = await tts.speak(value);
        return result == 1 || result == true || result == null;
      } catch (_) {
        return false;
      }
    }
  }

  Future<bool> testPronunciation() async {
    if (!sound) return false;
    return speak('Welcome to my school dictionary');
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
      'app': 'القاموس المدرسي الأردني',
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


  Future<bool> savePersistentBackupToDevice() async {
    final payload = {
      'app': 'القاموس المدرسي الأردني',
      'format': 'qamoosi-backup',
      'formatVersion': 2,
      'appVersion': appVersion,
      'createdAt': DateTime.now().toIso8601String(),
      'preferences': _allPrefsSnapshot(),
      'words': words.map((e) => e.toJson()).toList(),
    };
    final bytes = Uint8List.fromList(
      utf8.encode(const JsonEncoder.withIndent('  ').convert(payload)),
    );
    final saved = await FilePicker.platform.saveFile(
      dialogTitle: 'حفظ نسخة احتياطية دائمة',
      fileName: 'qamoosi_backup_latest.json',
      type: FileType.custom,
      allowedExtensions: ['json'],
      bytes: bytes,
    );
    return saved != null;
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
      for (final w in words) '${w.grade}|${w.semester}|${w.unit}|${w.lesson}|${w.en.trim().toLowerCase()}': w,
    };
    var added = 0;
    for (final word in valid) {
      final key = '${word.grade}|${word.semester}|${word.unit}|${word.lesson}|${word.en.trim().toLowerCase()}';
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
      .replaceAll(RegExp(r'[ـ:：]'), '')
      .replaceAll(RegExp(r'[أإآ]'), 'ا')
      .replaceAll('ة', 'ه')
      .replaceAll('ى', 'ي')
      .replaceAll(RegExp(r'\s+'), '_')
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
      exampleEn: _valueByHeaders(row, ['example_en', 'sentence_en', 'exampleenglish', 'example_english', 'sentenceenglish', 'sentence_english', 'examplesentence', 'example_sentence', 'book_example', 'example', 'sentence', 'الجمله_الانجليزيه', 'جمله_مثال', 'مثال_جمله', 'مثال_من_الكتاب', 'مثال_انجليزي']),
      exampleAr: _valueByHeaders(row, ['example_ar', 'sentence_ar', 'examplearabic', 'example_arabic', 'sentencearabic', 'sentence_arabic', 'translation', 'sentencetranslation', 'sentence_translation', 'ترجمه_الجمله', 'ترجمه_المثال', 'ترجمه_المثال_الي_العربيه', 'مثال_عربي']),
      semester: _valueByHeaders(row, ['semester', 'term', 'الفصل_الدراسي', 'الفصل الدراسي']),
      unit: _valueByHeaders(row, ['unit', 'الوحده', 'الوحدة']),
      lesson: _valueByHeaders(row, ['lesson', 'الدرس']),
      sourcePage: _valueByHeaders(row, ['source_page', 'page', 'رقم_الصفحه', 'رقم الصفحة', 'الصفحه', 'الصفحة']),
    );
  }

  List<List<String>> _readXlsxRows(Uint8List bytes) {
    final archive = ZipDecoder().decodeBytes(bytes, verify: true);
    final files = <String, List<int>>{};
    for (final file in archive.files) {
      if (!file.isFile) continue;
      files[file.name] = List<int>.from(file.content as List<int>);
    }

    final shared = <String>[];
    final sharedBytes = files['xl/sharedStrings.xml'];
    if (sharedBytes != null) {
      final doc = XmlDocument.parse(utf8.decode(sharedBytes, allowMalformed: true));
      for (final si in doc.descendants.whereType<XmlElement>().where((e) => e.name.local == 'si')) {
        shared.add(si.descendants.whereType<XmlElement>().where((e) => e.name.local == 't').map((e) => e.innerText).join());
      }
    }

    int columnIndex(String reference) {
      final letters = RegExp(r'^[A-Za-z]+').firstMatch(reference)?.group(0)?.toUpperCase() ?? 'A';
      var value = 0;
      for (final code in letters.codeUnits) value = value * 26 + code - 64;
      return value - 1;
    }

    final sheetNames = files.keys.where((name) => RegExp(r'^xl/worksheets/sheet\d+\.xml$').hasMatch(name)).toList()
      ..sort((a, b) {
        final na = int.tryParse(RegExp(r'\d+').firstMatch(a)?.group(0) ?? '') ?? 0;
        final nb = int.tryParse(RegExp(r'\d+').firstMatch(b)?.group(0) ?? '') ?? 0;
        return na.compareTo(nb);
      });
    if (sheetNames.isEmpty) throw Exception('ملف Excel لا يحتوي على أوراق قابلة للقراءة');

    final allRows = <List<String>>[];
    for (final name in sheetNames) {
      final doc = XmlDocument.parse(utf8.decode(files[name]!, allowMalformed: true));
      for (final rowElement in doc.descendants.whereType<XmlElement>().where((e) => e.name.local == 'row')) {
        final values = <int, String>{};
        var maxColumn = -1;
        for (final cell in rowElement.children.whereType<XmlElement>().where((e) => e.name.local == 'c')) {
          final ref = cell.getAttribute('r') ?? 'A1';
          final col = columnIndex(ref);
          maxColumn = max(maxColumn, col);
          final type = cell.getAttribute('t') ?? '';
          String value = '';
          if (type == 'inlineStr') {
            value = cell.descendants.whereType<XmlElement>().where((e) => e.name.local == 't').map((e) => e.innerText).join();
          } else {
            final raw = cell.descendants.whereType<XmlElement>().where((e) => e.name.local == 'v').map((e) => e.innerText).firstOrNull ?? '';
            if (type == 's') {
              final index = int.tryParse(raw) ?? -1;
              value = index >= 0 && index < shared.length ? shared[index] : '';
            } else if (type == 'b') {
              value = raw == '1' ? 'true' : 'false';
            } else {
              value = raw;
            }
          }
          values[col] = value.trim();
        }
        if (maxColumn >= 0) {
          allRows.add(List<String>.generate(maxColumn + 1, (i) => values[i] ?? ''));
        }
      }
    }
    return allRows;
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

    if (extension == 'csv') {
      final lines = const LineSplitter().convert(utf8.decode(bytes, allowMalformed: true).replaceFirst('\ufeff', ''));
      if (lines.isEmpty) throw Exception('ملف CSV فارغ');
      final headers = parseCsvLine(lines.first).map(_normalizeHeader).toList();
      for (final line in lines.skip(1)) {
        if (line.trim().isEmpty) continue;
        final cells = parseCsvLine(line);
        final row = <String, String>{};
        for (var i = 0; i < headers.length; i++) row[headers[i]] = i < cells.length ? cells[i].trim() : '';
        final word = _wordFromImportRow(row, nextId);
        if (word != null) { imported.add(word); nextId++; }
      }
    } else {
      final rows = _readXlsxRows(Uint8List.fromList(bytes));
      if (rows.isEmpty) throw Exception('ورقة Excel فارغة');
      var headers = <String>[];
      for (final cells in rows) {
        if (cells.every((v) => v.trim().isEmpty)) continue;
        if (headers.isEmpty) {
          headers = cells.map(_normalizeHeader).toList();
          continue;
        }
        final row = <String, String>{};
        for (var i = 0; i < headers.length; i++) row[headers[i]] = i < cells.length ? cells[i].trim() : '';
        final word = _wordFromImportRow(row, nextId);
        if (word != null) { imported.add(word); nextId++; }
      }
    }
    if (imported.isEmpty) throw Exception('لم يتم العثور على كلمات صالحة. يجب أن يحتوي الصف الأول على عناوين الأعمدة');
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
    await Share.shareXFiles([XFile(file.path)], subject: 'كلمات القاموس المدرسي الأردني');
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
    store.init().then((_) {
      if (!mounted) return;
      setState(() => ready = true);
      if (store.freshInstall) {
        WidgetsBinding.instance.addPostFrameCallback((_) => _offerRecovery());
      }
    });
  }

  Future<void> _offerRecovery() async {
    if (!mounted) return;
    final restore = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('استعادة بياناتك السابقة؟'),
        content: const Text('إذا كنت قد حذفت التطبيق سابقاً ولديك نسخة محفوظة في الجهاز، يمكنك استعادتها الآن. لن يستطيع التطبيق قراءة النسخ الخارجية دون اختيارك للملف.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('ليس الآن')),
          FilledButton.icon(
            onPressed: () => Navigator.pop(dialogContext, true),
            icon: const Icon(Icons.restore_rounded),
            label: const Text('استعادة من الجهاز'),
          ),
        ],
      ),
    );
    if (restore != true || !mounted) return;
    try {
      await store.restoreBackup(replace: true);
      if (mounted) snack(context, 'تمت استعادة بياناتك السابقة بنجاح');
    } catch (e) {
      if (mounted) snack(context, 'تعذر استعادة النسخة: $e');
    }
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

class BookCandidate {
  final String word;
  String meaning;
  String exampleEn;
  String exampleAr;
  final String unit;
  final String lesson;
  final String page;
  int frequency;
  bool selected;

  BookCandidate({
    required this.word,
    this.meaning = '',
    this.exampleEn = '',
    this.exampleAr = '',
    this.unit = '',
    this.lesson = '',
    this.page = '',
    this.frequency = 1,
    this.selected = true,
  });
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
  bool busy = false;
  List<BookCandidate> candidates = [];
  int pagesRead = 0;

  static const _stopWords = <String>{
    'the','and','for','with','this','that','these','those','from','into','onto','than','then','when','where','what','which','who','whom','whose','why','how',
    'you','your','yours','they','their','theirs','them','there','here','have','has','had','having','does','did','done','doing','are','was','were','been','being',
    'can','could','will','would','shall','should','may','might','must','not','yes','no','very','more','most','some','any','many','much','few','each','every','both',
    'about','above','after','again','against','along','among','around','before','below','between','during','inside','outside','over','under','through','without','within',
    'lesson','unit','page','pages','student','students','teacher','teachers','book','workbook','exercise','exercises','activity','activities','read','write','listen','look',
    'answer','answers','question','questions','complete','match','choose','circle','check','tick','work','pair','pairs','group','groups','english','arabic','example','examples'
  };

  bool _validWord(String raw, {required bool midSentenceTitleCase}) {
    final w = raw.trim();
    if (!RegExp(r"^[A-Za-z][A-Za-z'-]*$").hasMatch(w)) return false;
    final lower = w.toLowerCase();
    if (lower.length < 3 || lower.length > 28) return false;
    if (_stopWords.contains(lower)) return false;
    if (RegExp(r'^([a-z])\1+$').hasMatch(lower)) return false;
    if (midSentenceTitleCase && RegExp(r'^[A-Z][a-z]+$').hasMatch(w)) return false;
    return true;
  }

  String _sentenceFor(String pageText, String word) {
    final normalized = pageText.replaceAll(RegExp(r'\s+'), ' ').trim();
    final parts = normalized.split(RegExp(r'(?<=[.!?])\s+'));
    final re = RegExp('\\b${RegExp.escape(word)}\\b', caseSensitive: false);
    for (final sentence in parts) {
      final t = sentence.trim();
      if (t.length >= 20 && t.length <= 190 && re.hasMatch(t) && RegExp(r'[A-Za-z]{3}').hasMatch(t)) return t;
    }
    return '';
  }

  WordItem? _existingWord(String word) {
    final q = word.toLowerCase();
    for (final item in widget.store.words) {
      if (item.en.toLowerCase() == q) return item;
    }
    return null;
  }

  Future<void> pickAndAnalyzePdf() async {
    final picked = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['pdf']);
    if (picked == null || picked.files.isEmpty) return;
    final file = picked.files.first;
    if (file.path == null) {
      if (mounted) snack(context, 'تعذر الوصول إلى مسار ملف PDF على هذا الجهاز');
      return;
    }
    setState(() { busy = true; fileName = file.name; candidates = []; pagesRead = 0; });
    try {
      final document = await PdfDocument.openFile(file.path!);
      final pages = <String>[];
      try {
        for (final page in document.pages) {
          final pageText = await page.loadText();
          pages.add(pageText?.fullText ?? '');
        }
      } finally {
        await document.dispose();
      }
      final map = <String, BookCandidate>{};
      String currentUnit = '';
      String currentLesson = '';
      for (var pi = 0; pi < pages.length; pi++) {
        final text = pages[pi];
        final unitMatch = RegExp(r'\bUnit\s+([0-9]+|[A-Za-z]+)', caseSensitive: false).firstMatch(text);
        final lessonMatch = RegExp(r'\bLesson\s+([0-9]+|[A-Za-z]+)', caseSensitive: false).firstMatch(text);
        if (unitMatch != null) currentUnit = 'Unit ${unitMatch.group(1)}';
        if (lessonMatch != null) currentLesson = 'Lesson ${lessonMatch.group(1)}';

        final tokens = RegExp(r"[A-Za-z][A-Za-z'-]*").allMatches(text).toList();
        for (var ti = 0; ti < tokens.length; ti++) {
          final raw = tokens[ti].group(0)!;
          final prefixStart = tokens[ti].start > 2 ? tokens[ti].start - 2 : 0;
          final prefix = text.substring(prefixStart, tokens[ti].start);
          final startsSentence = ti == 0 || RegExp(r'[.!?]\s*$').hasMatch(prefix);
          if (!_validWord(raw, midSentenceTitleCase: !startsSentence)) continue;
          final key = '${currentUnit.toLowerCase()}|${currentLesson.toLowerCase()}|${raw.toLowerCase()}';
          final existing = _existingWord(raw);
          final found = map[key];
          if (found != null) {
            found.frequency++;
            if (found.exampleEn.isEmpty) found.exampleEn = _sentenceFor(text, raw);
          } else {
            map[key] = BookCandidate(
              word: raw.toLowerCase(),
              meaning: existing?.ar ?? '',
              exampleEn: _sentenceFor(text, raw),
              exampleAr: existing?.exampleAr ?? '',
              unit: currentUnit,
              lesson: currentLesson,
              page: '${pi + 1}',
            );
          }
        }
      }
      final list = map.values.where((e) => e.frequency >= 2 || e.exampleEn.isNotEmpty).toList();
      list.sort((a, b) {
        final f = b.frequency.compareTo(a.frequency);
        if (f != 0) return f;
        return a.word.compareTo(b.word);
      });
      setState(() { candidates = list; pagesRead = pages.length; });
      if (mounted && list.isEmpty) snack(context, 'تمت قراءة الملف لكن لم يتم العثور على كلمات تعليمية مناسبة');
    } catch (e) {
      if (mounted) snack(context, 'تعذر تحليل PDF: $e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _editCandidate(BookCandidate c) async {
    final meaning = TextEditingController(text: c.meaning);
    final exampleEn = TextEditingController(text: c.exampleEn);
    final exampleAr = TextEditingController(text: c.exampleAr);
    final save = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(c.word, textDirection: TextDirection.ltr),
        content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
          Align(alignment: Alignment.centerLeft, child: IconButton(onPressed: () => widget.store.speak(c.word), icon: const Icon(Icons.volume_up_rounded), tooltip: 'نطق الكلمة')),
          TextField(controller: meaning, decoration: const InputDecoration(labelText: 'المعنى العربي')),
          const SizedBox(height: 10),
          TextField(controller: exampleEn, textDirection: TextDirection.ltr, maxLines: 3, decoration: const InputDecoration(labelText: 'مثال إنجليزي من الكتاب')),
          const SizedBox(height: 8),
          Align(alignment: Alignment.centerLeft, child: IconButton(onPressed: () => widget.store.speak(exampleEn.text), icon: const Icon(Icons.record_voice_over_rounded), tooltip: 'نطق المثال')),
          TextField(controller: exampleAr, maxLines: 3, decoration: const InputDecoration(labelText: 'ترجمة المثال')),
        ])),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('إلغاء')),
          FilledButton(onPressed: () => Navigator.pop(dialogContext, true), child: const Text('حفظ التعديل')),
        ],
      ),
    );
    if (save == true) {
      setState(() {
        c.meaning = meaning.text.trim();
        c.exampleEn = exampleEn.text.trim();
        c.exampleAr = exampleAr.text.trim();
      });
    }
    meaning.dispose(); exampleEn.dispose(); exampleAr.dispose();
  }

  Future<void> saveSelected() async {
    final chosen = candidates.where((c) => c.selected && c.meaning.trim().isNotEmpty).toList();
    if (chosen.isEmpty) {
      snack(context, 'أضف معنى عربيًا لكلمة واحدة على الأقل قبل الحفظ');
      return;
    }
    var nextId = widget.store.words.isEmpty ? 1 : widget.store.words.map((w) => w.id).reduce(max) + 1;
    final items = <WordItem>[];
    for (final c in chosen) {
      items.add(WordItem(
        id: nextId++,
        grade: grade,
        en: c.word,
        ar: c.meaning,
        exampleEn: c.exampleEn,
        exampleAr: c.exampleAr,
        semester: semester,
        unit: c.unit,
        lesson: c.lesson,
        sourcePage: c.page,
      ));
    }
    final added = await widget.store._mergeImportedWords(items);
    if (mounted) snack(context, added == 0 ? 'تم تحديث الكلمات الموجودة دون تكرار' : 'تم حفظ $added كلمة جديدة في القاموس');
  }

  @override
  Widget build(BuildContext context) {
    final selectedCount = candidates.where((c) => c.selected).length;
    return Scaffold(
      appBar: AppBar(title: const Text('مختبر الكتاب')),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 10),
          child: Column(children: [
            Row(children: [
              Expanded(child: DropdownButtonFormField<String>(value: grade, items: grades.map((g) => DropdownMenuItem(value: g, child: Text(gradeName(g)))).toList(), onChanged: busy ? null : (v) => setState(() => grade = v ?? grade), decoration: const InputDecoration(labelText: 'الصف'))),
              const SizedBox(width: 10),
              Expanded(child: DropdownButtonFormField<String>(value: semester, items: const [DropdownMenuItem(value: 'الفصل الأول', child: Text('الفصل الأول')), DropdownMenuItem(value: 'الفصل الثاني', child: Text('الفصل الثاني'))], onChanged: busy ? null : (v) => setState(() => semester = v ?? semester), decoration: const InputDecoration(labelText: 'الفصل'))),
            ]),
            const SizedBox(height: 10),
            SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: busy ? null : pickAndAnalyzePdf, icon: const Icon(Icons.picture_as_pdf_rounded), label: Text(busy ? 'جاري قراءة الكتاب...' : 'اختر كتاب PDF وابدأ الاستخراج'))),
            if (fileName.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 8), child: Text('$fileName • $pagesRead صفحة', style: const TextStyle(color: Color(0xff64748b)))),
          ]),
        ),
        if (busy) const LinearProgressIndicator(),
        if (!busy && candidates.isNotEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Row(children: [
              Expanded(child: Text('${candidates.length} كلمة مرشحة • $selectedCount محددة', style: const TextStyle(fontWeight: FontWeight.w800))),
              TextButton(onPressed: () => setState(() { final all = selectedCount != candidates.length; for (final c in candidates) c.selected = all; }), child: Text(selectedCount == candidates.length ? 'إلغاء الكل' : 'تحديد الكل')),
            ]),
          ),
        Expanded(
          child: candidates.isEmpty
              ? Center(child: Padding(padding: const EdgeInsets.all(28), child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Icon(Icons.auto_awesome_rounded, size: 78, color: Theme.of(context).colorScheme.primary),
                  const SizedBox(height: 14),
                  const Text('حوّل الكتاب إلى قاموس', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 8),
                  const Text('يقرأ PDF، يكتشف الوحدة والدرس، يستخرج الكلمات التعليمية ويستبعد الأسماء والأماكن والأرقام والحروف والرموز، ثم يعرض النتائج للمراجعة قبل الحفظ.', textAlign: TextAlign.center, style: TextStyle(height: 1.5, color: Color(0xff64748b))),
                ])))
              : ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 90),
                  itemCount: candidates.length,
                  itemBuilder: (_, i) {
                    final c = candidates[i];
                    final scope = [if (c.unit.isNotEmpty) c.unit, if (c.lesson.isNotEmpty) c.lesson, 'ص ${c.page}'].join(' • ');
                    return Card(child: ListTile(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      leading: Checkbox(value: c.selected, onChanged: (v) => setState(() => c.selected = v ?? false)),
                      title: Row(children: [Expanded(child: Text(c.word, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900))), IconButton(onPressed: () => widget.store.speak(c.word), icon: const Icon(Icons.volume_up_rounded), tooltip: 'نطق')]),
                      subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(c.meaning.isEmpty ? 'المعنى يحتاج مراجعة' : c.meaning, style: TextStyle(fontWeight: FontWeight.w700, color: c.meaning.isEmpty ? Theme.of(context).colorScheme.error : null)),
                        const SizedBox(height: 3),
                        Text(scope, style: const TextStyle(fontSize: 12, color: Color(0xff64748b))),
                        if (c.exampleEn.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 5), child: Text(c.exampleEn, textDirection: TextDirection.ltr, maxLines: 2, overflow: TextOverflow.ellipsis)),
                      ]),
                      trailing: IconButton(onPressed: () => _editCandidate(c), icon: const Icon(Icons.edit_rounded), tooltip: 'مراجعة وتعديل'),
                    ));
                  },
                ),
        ),
      ]),
      floatingActionButton: candidates.isEmpty ? null : FloatingActionButton.extended(onPressed: busy ? null : saveSelected, icon: const Icon(Icons.library_add_check_rounded), label: const Text('اعتماد وإضافة للقاموس')),
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
        const SliverAppBar(title: Text('القاموس المدرسي الأردني'), floating: true),
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
            decoration: InputDecoration(prefixIcon: const Icon(Icons.search), hintText: 'ابحث بالعربي أو الإنجليزي', suffixIcon: widget.store.query.isEmpty ? null : IconButton(tooltip: 'مسح البحث', icon: const Icon(Icons.close), onPressed: () => setState(() => widget.store.query = ''))),
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
                trailing: IconButton(tooltip: 'نطق الكلمة', icon: const Icon(Icons.volume_up_rounded), onPressed: () => widget.store.speak(w.en)),
                onTap: () => showWord(context, widget.store, w, source: list, initialIndex: i),
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
              if (context.mounted) showWord(context, store, w, source: list, initialIndex: i);
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
  bool showMeaning = false;
  bool showExample = false;

  void move(int delta, int length) {
    if (length == 0) return;
    setState(() {
      index = (index + delta) % length;
      if (index < 0) index += length;
      showMeaning = false;
      showExample = false;
    });
    widget.store.saveLastIndex(grade, index);
  }

  Future<void> pronounce(BuildContext context, String value) async {
    final ok = await widget.store.speak(value);
    if (!ok && context.mounted) snack(context, 'تعذر تشغيل النطق. فعّل محرك تحويل النص إلى كلام الإنجليزي من إعدادات الهاتف');
  }

  @override
  Widget build(BuildContext context) {
    final list = widget.store.byGrade(grade);
    if (list.isNotEmpty && index >= list.length) index = 0;
    final word = list.isEmpty ? null : list[index];
    final hasExample = word != null && (word.exampleEn.isNotEmpty || word.exampleAr.isNotEmpty);
    return Scaffold(
      appBar: AppBar(title: const Text('البطاقات التعليمية')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          DropdownButtonFormField<String>(
            initialValue: grade,
            items: grades.map((g) => DropdownMenuItem(value: g, child: Text(gradeName(g)))).toList(),
            onChanged: (value) => setState(() {
              grade = value ?? '1';
              index = widget.store.lastIndex(grade);
              showMeaning = false;
              showExample = false;
            }),
          ),
          const SizedBox(height: 12),
          if (word != null) Text('${index + 1} / ${list.length}', style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          Expanded(
            child: word == null
                ? const Center(child: Text('لا توجد كلمات في هذا الصف'))
                : GestureDetector(
                    onHorizontalDragEnd: (details) {
                      final v = details.primaryVelocity ?? 0;
                      if (v < -100) move(1, list.length);
                      if (v > 100) move(-1, list.length);
                    },
                    child: Card(
                      child: ListView(
                        padding: const EdgeInsets.all(24),
                        children: [
                          const SizedBox(height: 22),
                          Text(word.en, textDirection: TextDirection.ltr, textAlign: TextAlign.center, style: const TextStyle(fontSize: 42, fontWeight: FontWeight.w900)),
                          const SizedBox(height: 24),
                          FilledButton.tonalIcon(
                            onPressed: () => pronounce(context, word.en),
                            icon: const Icon(Icons.volume_up_rounded),
                            label: const Text('لفظ الكلمة'),
                          ),
                          const SizedBox(height: 12),
                          if (hasExample) OutlinedButton.icon(
                            onPressed: () => setState(() => showExample = !showExample),
                            icon: const Icon(Icons.format_quote_rounded),
                            label: Text(showExample ? 'إخفاء مثال الجملة' : 'إظهار مثال الجملة'),
                          ),
                          if (hasExample) const SizedBox(height: 12),
                          FilledButton.icon(
                            onPressed: () => setState(() => showMeaning = !showMeaning),
                            icon: const Icon(Icons.translate_rounded),
                            label: Text(showMeaning ? 'إخفاء المعنى' : 'إظهار المعنى'),
                          ),
                          if (showMeaning) Padding(
                            padding: const EdgeInsets.only(top: 24),
                            child: Text(word.ar, textAlign: TextAlign.center, style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w900)),
                          ),
                          if (showExample) Container(
                            margin: const EdgeInsets.only(top: 20),
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(color: Theme.of(context).colorScheme.secondaryContainer, borderRadius: BorderRadius.circular(18)),
                            child: Column(children: [
                              if (word.exampleEn.isNotEmpty) ...[
                                const Text('الجملة الإنجليزية', style: TextStyle(fontWeight: FontWeight.w800)),
                                const SizedBox(height: 8),
                                Text(word.exampleEn, textDirection: TextDirection.ltr, textAlign: TextAlign.center, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w700)),
                                const SizedBox(height: 8),
                                FilledButton.tonalIcon(onPressed: () => pronounce(context, word.exampleEn), icon: const Icon(Icons.volume_up_rounded), label: const Text('لفظ الجملة')),
                              ],
                              if (word.exampleEn.isEmpty && word.exampleAr.isNotEmpty) ...[
                                const Text('الجملة الإنجليزية غير محفوظة لهذه الكلمة', textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.w800)),
                                const SizedBox(height: 8),
                                const Text('أعد استيراد ملف Excel نفسه مرة واحدة لتحديث الجملة الإنجليزية دون تكرار الكلمة.', textAlign: TextAlign.center),
                              ],
                              if (word.exampleAr.isNotEmpty) ...[
                                const SizedBox(height: 14),
                                const Divider(),
                                const SizedBox(height: 8),
                                const Text('ترجمة الجملة', style: TextStyle(fontWeight: FontWeight.w800)),
                                const SizedBox(height: 6),
                                Text(word.exampleAr, textAlign: TextAlign.center, style: const TextStyle(fontSize: 17)),
                              ],
                            ]),
                          ),
                        ],
                      ),
                    ),
                  ),
          ),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(child: OutlinedButton.icon(onPressed: word == null ? null : () => move(-1, list.length), icon: const Icon(Icons.arrow_forward_rounded), label: const Text('السابق'))),
            const SizedBox(width: 10),
            Expanded(child: FilledButton.icon(onPressed: word == null ? null : () => move(1, list.length), icon: const Icon(Icons.arrow_back_rounded), label: const Text('التالي'))),
          ]),
          const SizedBox(height: 8),
          Row(children: [
            Expanded(child: OutlinedButton.icon(onPressed: word == null ? null : () async { await widget.store.answer(word, false); move(1, list.length); }, icon: const Icon(Icons.refresh), label: const Text('تحتاج مراجعة'))),
            const SizedBox(width: 10),
            Expanded(child: FilledButton.icon(onPressed: word == null ? null : () async { await widget.store.answer(word, true); move(1, list.length); }, icon: const Icon(Icons.check), label: const Text('أتقنتها'))),
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
        Card(child: Padding(padding: const EdgeInsets.all(28), child: Column(children: [Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 35, fontWeight: FontWeight.w900)), const SizedBox(height: 14), FilledButton.tonalIcon(onPressed: () => widget.store.speak(w.en), icon: const Icon(Icons.volume_up_rounded), label: const Text('اسمع الكلمة'))]))),
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
      actions: [TextButton(onPressed: () => Navigator.pop(context, null), child: const Text('إلغاء')), FilledButton(onPressed: () => Navigator.pop(context, false), child: const Text('دمج وحفظ الحالي')), FilledButton(style: FilledButton.styleFrom(backgroundColor: Theme.of(context).colorScheme.error, foregroundColor: Theme.of(context).colorScheme.onError), onPressed: () => Navigator.pop(context, true), child: const Text('استبدال وحذف الحالي'))],
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
          SettingsTile(
            icon: Icons.save_alt_rounded,
            title: 'حفظ نسخة دائمة على الجهاز',
            subtitle: 'تبقى في تطبيق الملفات حتى بعد حذف التطبيق وإعادة تثبيته',
            onTap: () async {
              try {
                final ok = await store.savePersistentBackupToDevice();
                if (!context.mounted) return;
                if (ok) snack(context, 'تم حفظ النسخة الدائمة. احتفظ بملف qamoosi_backup_latest.json في الجهاز');
              } catch (e) {
                if (context.mounted) snack(context, 'تعذر حفظ النسخة على الجهاز: $e');
              }
            },
          ),
          SettingsTile(icon: Icons.cloud_upload_outlined, title: 'مشاركة نسخة احتياطية', subtitle: 'إرسال النسخة إلى Drive أو واتساب أو أي مكان آمن', onTap: () async { try { await store.shareBackup(); } catch (e) { if (context.mounted) snack(context, 'تعذر إنشاء النسخة: $e'); } }),
          SettingsTile(icon: Icons.restore_rounded, title: 'استعادة نسخة من الجهاز', subtitle: 'بعد إعادة التثبيت اختر ملف qamoosi_backup_latest.json أو أي نسخة سابقة', onTap: () => restoreDialog(context)),
          SettingsTile(icon: Icons.table_view_outlined, title: 'تصدير ملف Excel/CSV', subtitle: 'للمراجعة أو الفتح على الكمبيوتر', onTap: () async { try { await store.exportCsv(); } catch (e) { if (context.mounted) snack(context, 'تعذر التصدير: $e'); } }),
          const SectionTitle('حول التطبيق'),
          const SettingsTile(icon: Icons.info_outline, title: 'القاموس المدرسي الأردني', subtitle: 'الإصدار $appVersion • يعمل دون إنترنت'),
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

void showWord(BuildContext context, Store store, WordItem word, {List<WordItem>? source, int? initialIndex}) {
  final list = (source == null || source.isEmpty) ? store.byGrade(word.grade) : source;
  var index = initialIndex ?? list.indexWhere((item) => item.id == word.id);
  if (index < 0) index = 0;
  push(context, WordCardPage(store: store, words: list.isEmpty ? [word] : list, initialIndex: index));
}

class WordCardPage extends StatefulWidget {
  final Store store;
  final List<WordItem> words;
  final int initialIndex;
  const WordCardPage({super.key, required this.store, required this.words, required this.initialIndex});

  @override
  State<WordCardPage> createState() => _WordCardPageState();
}

class _WordCardPageState extends State<WordCardPage> {
  late int index;
  bool showMeaning = false;
  bool showExample = false;

  @override
  void initState() {
    super.initState();
    index = widget.initialIndex.clamp(0, widget.words.length - 1);
  }

  void move(int delta) {
    setState(() {
      index = (index + delta) % widget.words.length;
      if (index < 0) index += widget.words.length;
      showMeaning = false;
      showExample = false;
    });
  }

  Future<void> pronounce(String value) async {
    final ok = await widget.store.speak(value);
    if (!ok && mounted) snack(context, 'تعذر تشغيل النطق. ثبّت أو فعّل صوت اللغة الإنجليزية في إعدادات الهاتف');
  }

  @override
  Widget build(BuildContext context) {
    final word = widget.words[index];
    final hasExample = word.exampleEn.isNotEmpty || word.exampleAr.isNotEmpty;
    return Scaffold(
      appBar: AppBar(title: Text('بطاقة الكلمة ${index + 1} / ${widget.words.length}')),
      body: SafeArea(
        child: GestureDetector(
          onHorizontalDragEnd: (details) {
            final v = details.primaryVelocity ?? 0;
            if (v < -100) move(1);
            if (v > 100) move(-1);
          },
          child: ListView(
            padding: const EdgeInsets.all(18),
            children: [
              Card(child: Padding(
                padding: const EdgeInsets.fromLTRB(22, 34, 22, 28),
                child: Column(children: [
                  Text(word.en, textDirection: TextDirection.ltr, textAlign: TextAlign.center, style: const TextStyle(fontSize: 43, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 8),
                  Text(gradeName(word.grade), style: const TextStyle(color: Color(0xff6f7d94))),
                  const SizedBox(height: 24),
                  SizedBox(width: double.infinity, child: FilledButton.tonalIcon(onPressed: () => pronounce(word.en), icon: const Icon(Icons.volume_up_rounded), label: const Text('لفظ الكلمة'))),
                  const SizedBox(height: 12),
                  if (hasExample) SizedBox(width: double.infinity, child: OutlinedButton.icon(onPressed: () => setState(() => showExample = !showExample), icon: const Icon(Icons.format_quote_rounded), label: Text(showExample ? 'إخفاء مثال الجملة' : 'إظهار مثال الجملة'))),
                  if (hasExample) const SizedBox(height: 12),
                  SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: () => setState(() => showMeaning = !showMeaning), icon: const Icon(Icons.translate_rounded), label: Text(showMeaning ? 'إخفاء المعنى' : 'إظهار المعنى'))),
                  if (showMeaning) Container(width: double.infinity, margin: const EdgeInsets.only(top: 20), padding: const EdgeInsets.all(20), decoration: BoxDecoration(color: Theme.of(context).colorScheme.primaryContainer, borderRadius: BorderRadius.circular(20)), child: Text(word.ar, textAlign: TextAlign.center, style: const TextStyle(fontSize: 31, fontWeight: FontWeight.w900))),
                  if (showExample) Container(width: double.infinity, margin: const EdgeInsets.only(top: 20), padding: const EdgeInsets.all(18), decoration: BoxDecoration(color: Theme.of(context).colorScheme.secondaryContainer, borderRadius: BorderRadius.circular(20)), child: Column(children: [
                    if (word.exampleEn.isNotEmpty) ...[
                      const Text('الجملة الإنجليزية', style: TextStyle(fontWeight: FontWeight.w800)),
                      const SizedBox(height: 8),
                      Text(word.exampleEn, textDirection: TextDirection.ltr, textAlign: TextAlign.center, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w700)),
                      const SizedBox(height: 10),
                      SizedBox(width: double.infinity, child: FilledButton.tonalIcon(onPressed: () => pronounce(word.exampleEn), icon: const Icon(Icons.volume_up_rounded), label: const Text('لفظ الجملة'))),
                    ],
                    if (word.exampleAr.isNotEmpty) ...[
                      const SizedBox(height: 14),
                      const Divider(),
                      const Text('ترجمة الجملة', style: TextStyle(fontWeight: FontWeight.w800)),
                      const SizedBox(height: 6),
                      Text(word.exampleAr, textAlign: TextAlign.center, style: const TextStyle(fontSize: 17)),
                    ],
                  ])),
                ]),
              )),
              const SizedBox(height: 12),
              Row(children: [
                Expanded(child: OutlinedButton.icon(onPressed: () => move(-1), icon: const Icon(Icons.arrow_forward_rounded), label: const Text('السابق'))),
                const SizedBox(width: 12),
                Expanded(child: FilledButton.icon(onPressed: () => move(1), icon: const Icon(Icons.arrow_back_rounded), label: const Text('التالي'))),
              ]),
            ],
          ),
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
