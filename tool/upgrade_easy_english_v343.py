from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

s = s.replace("const appVersion = '3.4.2';", "const appVersion = '3.4.3';")

old_init = '''  Future<void> init() async {\n    prefs = await SharedPreferences.getInstance();\n    freshInstall = prefs.getBool('installation_initialized') != true;\n    await prefs.setBool('installation_initialized', true);\n    sound = prefs.getBool('sound') ?? true;\n    activeProfile = prefs.getInt('activeProfile') ?? 1;\n    final rawProfiles = prefs.getString('profiles');\n    profiles = rawProfiles == null\n        ? [Profile(1, 'الطالب 1')]\n        : (jsonDecode(rawProfiles) as List).map((e) => Profile.fromJson(Map<String, dynamic>.from(e))).toList();\n    await _loadWords();\n    await loadProgress();\n    await _configureTts();\n    await _prepareTts();\n  }\n'''
new_init = '''  Future<void> init({void Function(String message, double progress, bool firstInstall)? onProgress}) async {\n    onProgress?.call('جاري بدء Easy English AI…', .06, false);\n    prefs = await SharedPreferences.getInstance();\n    freshInstall = prefs.getBool('installation_initialized') != true;\n    onProgress?.call(\n      freshInstall ? 'نجهّز التطبيق لأول استخدام…' : 'جاري تحميل بياناتك…',\n      .16,\n      freshInstall,\n    );\n    await prefs.setBool('installation_initialized', true);\n    sound = prefs.getBool('sound') ?? true;\n    activeProfile = prefs.getInt('activeProfile') ?? 1;\n    final rawProfiles = prefs.getString('profiles');\n    profiles = rawProfiles == null\n        ? [Profile(1, 'الطالب 1')]\n        : (jsonDecode(rawProfiles) as List).map((e) => Profile.fromJson(Map<String, dynamic>.from(e))).toList();\n    onProgress?.call('جاري تجهيز قاموس الكلمات…', .38, freshInstall);\n    await _loadWords();\n    onProgress?.call('جاري استعادة تقدمك وإعداداتك…', .62, freshInstall);\n    await loadProgress();\n    onProgress?.call('جاري تجهيز النطق والترجمة…', .80, freshInstall);\n    await _configureTts();\n    await _prepareTts();\n    onProgress?.call('جاهز تقريبًا…', .98, freshInstall);\n  }\n'''
if old_init not in s:
    raise SystemExit('Store.init block not found')
s = s.replace(old_init, new_init)

old_boot = '''class _AppBootstrapState extends State<AppBootstrap> {\n  final store = Store();\n  bool ready = false;\n  bool introDone = false;\n\n  @override\n  void initState() {\n    super.initState();\n    store.init().then((_) {\n      if (!mounted) return;\n      setState(() => ready = true);\n    });\n  }\n'''
new_boot = '''class _AppBootstrapState extends State<AppBootstrap> {\n  final store = Store();\n  bool ready = false;\n  bool introDone = false;\n  bool firstInstallPreparing = false;\n  double bootProgress = .04;\n  String bootMessage = 'جاري تشغيل Easy English AI…';\n\n  @override\n  void initState() {\n    super.initState();\n    store.init(onProgress: (message, progress, firstInstall) {\n      if (!mounted) return;\n      setState(() {\n        bootMessage = message;\n        bootProgress = progress;\n        firstInstallPreparing = firstInstall;\n      });\n    }).then((_) {\n      if (!mounted) return;\n      setState(() {\n        bootProgress = 1;\n        ready = true;\n      });\n    });\n  }\n'''
if old_boot not in s:
    raise SystemExit('AppBootstrap init block not found')
s = s.replace(old_boot, new_boot)

old_ready = "    if (!ready) return const Scaffold(body: Center(child: CircularProgressIndicator()));"
new_ready = '''    if (!ready) {\n      return Scaffold(\n        body: SafeArea(\n          child: Center(\n            child: SingleChildScrollView(\n              padding: const EdgeInsets.all(28),\n              child: ConstrainedBox(\n                constraints: const BoxConstraints(maxWidth: 440),\n                child: Column(mainAxisSize: MainAxisSize.min, children: [\n                  Container(\n                    width: 108,\n                    height: 108,\n                    decoration: BoxDecoration(\n                      color: Theme.of(context).colorScheme.primaryContainer,\n                      borderRadius: BorderRadius.circular(32),\n                    ),\n                    child: Icon(Icons.auto_awesome_rounded, size: 58, color: Theme.of(context).colorScheme.primary),\n                  ),\n                  const SizedBox(height: 24),\n                  const Text('Easy English AI', textAlign: TextAlign.center, style: TextStyle(fontSize: 29, fontWeight: FontWeight.w900)),\n                  const SizedBox(height: 12),\n                  Text(bootMessage, textAlign: TextAlign.center, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),\n                  const SizedBox(height: 18),\n                  ClipRRect(\n                    borderRadius: BorderRadius.circular(20),\n                    child: LinearProgressIndicator(value: bootProgress.clamp(0, 1), minHeight: 10),\n                  ),\n                  const SizedBox(height: 16),\n                  Text(\n                    firstInstallPreparing\n                        ? 'في أول تشغيل يحتاج التطبيق إلى لحظات لتجهيز الكلمات والنطق وخدمات الترجمة. الرجاء الانتظار قليلًا ولا تغلق التطبيق.'\n                        : 'نحمّل بياناتك ونجهّز أدوات التعلم. لن يستغرق ذلك طويلًا.',\n                    textAlign: TextAlign.center,\n                    style: const TextStyle(height: 1.55, color: Color(0xff64748b)),\n                  ),\n                ]),\n              ),\n            ),\n          ),\n        ),\n      );\n    }'''
if old_ready not in s:
    raise SystemExit('bootstrap loading line not found')
s = s.replace(old_ready, new_ready)

# Insert online translation fallback helpers before _autoFillMeanings.
marker = "  Future<void> _autoFillMeanings(List<BookCandidate> list) async {"
if marker not in s:
    raise SystemExit('_autoFillMeanings marker not found')
helpers = r'''  final Map<String, String> _onlineTranslationCache = <String, String>{};

  Future<String> _translateOnline(String value) async {
    final text = value.trim();
    if (text.isEmpty) return '';
    final cacheKey = text.toLowerCase();
    final cached = _onlineTranslationCache[cacheKey];
    if (cached != null) return cached;
    try {
      final uri = Uri.https('api.mymemory.translated.net', '/get', {
        'q': text,
        'langpair': 'en|ar',
      });
      final response = await http.get(uri, headers: const {'Accept': 'application/json'}).timeout(const Duration(seconds: 7));
      if (response.statusCode != 200) return '';
      final decoded = jsonDecode(response.body);
      if (decoded is! Map) return '';
      final responseData = decoded['responseData'];
      if (responseData is! Map) return '';
      final translated = (responseData['translatedText'] ?? '').toString().trim();
      if (translated.isEmpty || translated.toLowerCase() == text.toLowerCase()) return '';
      _onlineTranslationCache[cacheKey] = translated;
      return translated;
    } catch (_) {
      return '';
    }
  }

  Future<void> _fillUnresolvedOnline(List<BookCandidate> list) async {
    final unresolved = list.where((c) => c.meaning.trim().isEmpty || (c.exampleEn.trim().isNotEmpty && c.exampleAr.trim().isEmpty)).toList();
    const batchSize = 4;
    for (var start = 0; start < unresolved.length; start += batchSize) {
      final end = min(start + batchSize, unresolved.length);
      final batch = unresolved.sublist(start, end);
      await Future.wait(batch.map((c) async {
        if (c.meaning.trim().isEmpty) {
          final onlineMeaning = await _translateOnline(c.word);
          if (onlineMeaning.isNotEmpty) c.meaning = onlineMeaning;
        }
        if (c.exampleEn.trim().isNotEmpty && c.exampleAr.trim().isEmpty) {
          final onlineSentence = await _translateOnline(c.exampleEn);
          if (onlineSentence.isNotEmpty) c.exampleAr = onlineSentence;
        }
      }));
      if (mounted) setState(() {});
    }
  }

'''
s = s.replace(marker, helpers + marker, 1)

# After local ML translation attempt, resolve anything still empty from the internet.
old_tail = '''    } catch (_) {\n      // Extraction remains usable even if the language models could not be downloaded.\n      // Generated English examples stay editable and unresolved Arabic fields remain reviewable.\n    }\n  }\n'''
new_tail = '''    } catch (_) {\n      // If the on-device model is unavailable, continue below with the internet fallback.\n    }\n\n    // Internet is a fallback, not the first choice. This prevents ordinary words such as\n    // school/class/great from being marked for manual review merely because the local\n    // translation model was unavailable on a device.\n    await _fillUnresolvedOnline(list);\n  }\n'''
if old_tail not in s:
    raise SystemExit('_autoFillMeanings tail not found')
s = s.replace(old_tail, new_tail, 1)

# Make the remaining warning precise: it is a technical unresolved state, not word difficulty.
s = s.replace("c.meaning.isEmpty ? 'المعنى يحتاج مراجعة' : c.meaning", "c.meaning.isEmpty ? 'تعذر جلب المعنى تلقائيًا' : c.meaning")

# Remove duplicated Unit/ Lesson labels like "Unit Unit" and "Lesson Appearance" caused by loose heading matches.
s = s.replace("if (unitMatch != null) currentUnit = 'Unit ${unitMatch.group(1)}';", "if (unitMatch != null) { final v = (unitMatch.group(1) ?? '').trim(); if (v.isNotEmpty && v.toLowerCase() != 'unit') currentUnit = 'Unit $v'; }")
s = s.replace("if (lessonMatch != null) currentLesson = 'Lesson ${lessonMatch.group(1)}';", "if (lessonMatch != null) { final v = (lessonMatch.group(1) ?? '').trim(); if (v.isNotEmpty && v.toLowerCase() != 'lesson') currentLesson = 'Lesson $v'; }")

p.write_text(s, encoding='utf-8')

pub = Path('pubspec.yaml')
ps = pub.read_text(encoding='utf-8')
ps = re.sub(r'^version:\s*3\.4\.2\+31$', 'version: 3.4.3+32', ps, flags=re.M)
pub.write_text(ps, encoding='utf-8')

print('Easy English AI v3.4.3 upgrade applied')
