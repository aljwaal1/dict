from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

imp = "import 'package:google_mlkit_translation/google_mlkit_translation.dart';\n"
if imp not in s:
    s = s.replace("import 'package:flutter_tts/flutter_tts.dart';\n", "import 'package:flutter_tts/flutter_tts.dart';\n" + imp, 1)

s = s.replace("const appVersion = '3.1.2';", "const appVersion = '3.2.0';", 1)

# Remove common grammar/function words that should not become school-vocabulary cards.
old = "if (_stopWords.contains(lower)) return false;"
new = """if (_stopWords.contains(lower)) return false;
    const extraNoise = <String>{
      'him','his','her','hers','she','he','its','our','ours','us','me','my','mine','we','it','itself','himself','herself','myself','yourself','ourselves','themselves',
      'a','an','of','to','in','on','at','by','as','or','if','so','but','nor','yet','too','also','just','only','even','still','already','ever','never','once','twice',
      'do','go','get','got','make','made','say','said','tell','told','ask','asked','use','used','see','saw','come','came','take','took','give','gave',
      'one','two','three','four','five','six','seven','eight','nine','ten'
    };
    if (extraNoise.contains(lower)) return false;"""
if old in s and 'extraNoise' not in s:
    s = s.replace(old, new, 1)

anchor = "  Future<void> _editCandidate(BookCandidate c) async {"
helper = r'''  Future<void> _autoFillMeanings(List<BookCandidate> list) async {
    final missing = list.where((c) => c.meaning.trim().isEmpty).toList();
    if (missing.isEmpty) return;

    final manager = OnDeviceTranslatorModelManager();
    final source = TranslateLanguage.english;
    final target = TranslateLanguage.arabic;
    try {
      final enReady = await manager.isModelDownloaded(source.bcpCode);
      if (!enReady) await manager.downloadModel(source.bcpCode);
      final arReady = await manager.isModelDownloaded(target.bcpCode);
      if (!arReady) await manager.downloadModel(target.bcpCode);

      final translator = OnDeviceTranslator(sourceLanguage: source, targetLanguage: target);
      try {
        for (var i = 0; i < missing.length; i++) {
          final c = missing[i];
          try {
            final translated = (await translator.translateText(c.word)).trim();
            if (translated.isNotEmpty && translated.toLowerCase() != c.word.toLowerCase()) {
              c.meaning = translated;
            }
          } catch (_) {}
          if (mounted && (i % 25 == 0 || i == missing.length - 1)) {
            setState(() {});
          }
        }
      } finally {
        translator.close();
      }
    } catch (_) {
      // Keep unresolved items editable; extraction itself must never fail because translation model download failed.
    }
  }

'''
if anchor in s and '_autoFillMeanings(List<BookCandidate>' not in s:
    s = s.replace(anchor, helper + anchor, 1)

old_set = """      setState(() { candidates = list; pagesRead = pages.length; });
      if (mounted && list.isEmpty) snack(context, 'تمت قراءة الملف لكن لم يتم العثور على كلمات تعليمية مناسبة');"""
new_set = """      setState(() { candidates = list; pagesRead = pages.length; });
      if (list.isNotEmpty) {
        await _autoFillMeanings(list);
        if (mounted) setState(() { candidates = List<BookCandidate>.from(list); });
      }
      if (mounted && list.isEmpty) snack(context, 'تمت قراءة الملف لكن لم يتم العثور على كلمات تعليمية مناسبة');"""
if old_set in s:
    s = s.replace(old_set, new_set, 1)
elif '_autoFillMeanings(list)' not in s:
    raise SystemExit('Candidate result anchor not found')

p.write_text(s, encoding='utf-8')
print('Jordan v3.2.0 automatic Arabic meanings patch applied')
