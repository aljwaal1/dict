from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

# Branding/version.
s = s.replace("const appVersion = '3.4.1';", "const appVersion = '3.4.2';")
s = s.replace("قاموسي AI", "Easy English AI")
s = s.replace("القاموس الذكي للطلاب العرب", "تعلم الإنجليزية بسهولة")

# HTTP client for dictionary example fallback.
if "package:http/http.dart" not in s:
    anchor = "import 'package:google_mlkit_translation/google_mlkit_translation.dart';\n"
    s = s.replace(anchor, anchor + "import 'package:http/http.dart' as http;\n")

# Flash-card: prevent the whole card from shrinking and hiding content.
s = s.replace(
"""child: FittedBox(\n                              fit: BoxFit.scaleDown,\n                              alignment: Alignment.center,\n                              child: SizedBox(""",
"""child: SingleChildScrollView(\n                              child: SizedBox("""
)

# Let full example/translation/meaning remain visible instead of ellipsis.
s = s.replace("Text(word.exampleEn, textDirection: TextDirection.ltr, textAlign: TextAlign.center, maxLines: 3, overflow: TextOverflow.ellipsis, style:", "Text(word.exampleEn, textDirection: TextDirection.ltr, textAlign: TextAlign.center, style:")
s = s.replace("Text(word.exampleAr, textAlign: TextAlign.center, maxLines: 3, overflow: TextOverflow.ellipsis, style:", "Text(word.exampleAr, textAlign: TextAlign.center, style:")
s = s.replace("Text(word.ar, textAlign: TextAlign.center, maxLines: 2, overflow: TextOverflow.ellipsis, style:", "Text(word.ar, textAlign: TextAlign.center, style:")

# Fixed, non-mirrored navigation arrows for Arabic UI.
# Previous = right arrow, Next = left arrow. Force LTR so RTL does not mirror them.
s = s.replace("icon: const Icon(Icons.arrow_forward_rounded, size: 19), label: const Text('السابق')", "icon: const Icon(Icons.arrow_forward_rounded, size: 22, textDirection: TextDirection.ltr), label: const Text('السابق')")
s = s.replace("icon: const Icon(Icons.arrow_back_rounded, size: 19), label: const Text('التالي')", "icon: const Icon(Icons.arrow_back_rounded, size: 22, textDirection: TextDirection.ltr), label: const Text('التالي')")

old_helpers = r'''  String _sentenceFor(String pageText, String word) {
    final normalized = pageText.replaceAll(RegExp(r'\s+'), ' ').trim();
    final parts = normalized.split(RegExp(r'(?<=[.!?])\s+'));
    final re = RegExp('\\b${RegExp.escape(word)}\\b', caseSensitive: false);
    for (final sentence in parts) {
      final t = sentence.trim();
      if (t.length >= 20 && t.length <= 190 && re.hasMatch(t) && RegExp(r'[A-Za-z]{3}').hasMatch(t)) return t;
    }
    return '';
  }

  String _generatedExample(String word) {
    final safe = word.trim().toLowerCase();
    return 'We learned the word "$safe" in class today.';
  }
'''

new_helpers = r'''  bool _instructionLike(String text) {
    final t = text.toLowerCase().trim();
    const starts = <String>[
      'read ', 'write ', 'listen ', 'look ', 'choose ', 'circle ', 'match ',
      'complete ', 'answer ', 'check ', 'tick ', 'underline ', 'work in ',
      'work with ', 'discuss ', 'ask your ', 'talk to ', 'fill in ', 'put the '
    ];
    if (starts.any(t.startsWith)) return true;
    final instructionHits = RegExp(r'\b(question|exercise|activity|workbook|teacher|student|pair|group|page|unit|lesson)\b', caseSensitive: false).allMatches(t).length;
    return instructionHits >= 2;
  }

  String _cleanSentence(String value) {
    var t = value.replaceAll(RegExp(r'\s+'), ' ').trim();
    t = t.replaceAll(RegExp(r'^[\-•▪►*\d\s.)]+'), '').trim();
    t = t.replaceAll(RegExp(r'\s+([,.!?;:])'), r'$1');
    return t;
  }

  String _sentenceFor(String pageText, String word) {
    final re = RegExp('\\b${RegExp.escape(word)}\\b', caseSensitive: false);
    final rawParts = <String>[
      ...pageText.split(RegExp(r'[\r\n]+')),
      ...pageText.replaceAll(RegExp(r'\s+'), ' ').split(RegExp(r'(?<=[.!?])\s+')),
    ];
    String best = '';
    var bestScore = -999;
    for (final part in rawParts) {
      final t = _cleanSentence(part);
      if (!re.hasMatch(t) || _instructionLike(t)) continue;
      final words = RegExp(r"[A-Za-z][A-Za-z'-]*").allMatches(t).length;
      if (t.length < 18 || t.length > 220 || words < 4 || words > 30) continue;
      if (!RegExp(r'[A-Za-z]{3}').hasMatch(t)) continue;
      var score = 0;
      if (RegExp(r'[.!?]$').hasMatch(t)) score += 4;
      if (words >= 6 && words <= 18) score += 4;
      if (t.toLowerCase().split(word.toLowerCase()).length - 1 == 1) score += 2;
      if (RegExp(r'^[A-Z]').hasMatch(t)) score += 1;
      if (t.contains(':')) score -= 1;
      if (score > bestScore) { bestScore = score; best = t; }
    }
    return best;
  }

  String _generatedExample(String word) {
    final safe = word.trim().toLowerCase();
    return 'I saw the word "$safe" while reading and understood it from the sentence.';
  }

  Future<String> _fetchDictionaryExample(String word) async {
    try {
      final uri = Uri.https('api.dictionaryapi.dev', '/api/v2/entries/en/${Uri.encodeComponent(word)}');
      final response = await http.get(uri).timeout(const Duration(seconds: 4));
      if (response.statusCode != 200) return '';
      final decoded = jsonDecode(response.body);
      if (decoded is! List) return '';
      for (final entry in decoded) {
        if (entry is! Map) continue;
        final meanings = entry['meanings'];
        if (meanings is! List) continue;
        for (final meaning in meanings) {
          if (meaning is! Map) continue;
          final defs = meaning['definitions'];
          if (defs is! List) continue;
          for (final def in defs) {
            if (def is! Map) continue;
            final example = (def['example'] ?? '').toString().trim();
            if (example.length >= 15 && example.length <= 220 && !_instructionLike(example)) return example;
          }
        }
      }
    } catch (_) {}
    return '';
  }

  Future<void> _fillQualityExamples(List<BookCandidate> list) async {
    final missing = list.where((c) => c.exampleEn.trim().isEmpty).toList();
    const batchSize = 8;
    for (var start = 0; start < missing.length; start += batchSize) {
      final end = min(start + batchSize, missing.length);
      final batch = missing.sublist(start, end);
      await Future.wait(batch.map((c) async {
        final online = await _fetchDictionaryExample(c.word);
        if (online.isNotEmpty) {
          c.exampleEn = online;
          c.exampleGenerated = true;
        }
      }));
      if (mounted) setState(() {});
    }
    for (final c in missing) {
      if (c.exampleEn.trim().isEmpty) {
        c.exampleEn = _generatedExample(c.word);
        c.exampleGenerated = true;
      }
    }
  }
'''

if old_helpers not in s:
    raise SystemExit('PDF helper block not found')
s = s.replace(old_helpers, new_helpers)

# Stronger vocabulary filter.
s = s.replace(
"final list = map.values.where((e) => e.frequency >= 2 || e.meaning.trim().isNotEmpty || (e.frequency == 1 && e.word.length >= 5 && e.exampleEn.isNotEmpty)).toList();",
"final list = map.values.where((e) => e.meaning.trim().isNotEmpty || e.exampleEn.trim().isNotEmpty || e.frequency >= 3).where((e) => !_stopWords.contains(e.word.toLowerCase())).toList();"
)

# Prefer book examples, then dictionary examples, then fallback before Arabic translation.
s = s.replace(
"""      if (list.isNotEmpty) {
        await _autoFillMeanings(list);""",
"""      if (list.isNotEmpty) {
        await _fillQualityExamples(list);
        await _autoFillMeanings(list);"""
)

s = s.replace(
"""    // Give every candidate a usable English example before translation.
    for (final c in list) {
      if (c.exampleEn.trim().isEmpty) {
        c.exampleEn = _generatedExample(c.word);
        c.exampleGenerated = true;
      }
    }

""",
"""    // Examples were prepared before translation: book context first, then dictionary fallback.
"""
)

p.write_text(s, encoding='utf-8')

pub = Path('pubspec.yaml')
ps = pub.read_text(encoding='utf-8')
ps = re.sub(r'^description:.*$', 'description: Easy English AI - تعلم الإنجليزية بسهولة بالكلمات والجمل والنطق والتعلم الذكي من PDF.', ps, flags=re.M)
ps = re.sub(r'^version:\s*3\.4\.1\+30$', 'version: 3.4.2+31', ps, flags=re.M)
pub.write_text(ps, encoding='utf-8')

print('Easy English AI v3.4.2 upgrade applied')
