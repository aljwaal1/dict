from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

s = s.replace("const appVersion = '3.2.1';", "const appVersion = '3.2.2';", 1)

# Track whether the sentence came from the textbook or was generated as a fallback.
s = s.replace(
    "  bool selected;\n\n  BookCandidate({",
    "  bool selected;\n  bool exampleGenerated;\n\n  BookCandidate({",
    1,
)
s = s.replace(
    "    this.selected = true,\n  });",
    "    this.selected = true,\n    this.exampleGenerated = false,\n  });",
    1,
)

# A safe grammatical fallback when the PDF has no usable sentence for the word.
anchor = "  WordItem? _existingWord(String word) {"
helper = r'''  String _generatedExample(String word) {
    final safe = word.trim().toLowerCase();
    return 'We learned the word "$safe" in class today.';
  }

'''
if anchor in s and '_generatedExample(String word)' not in s:
    s = s.replace(anchor, helper + anchor, 1)

# Replace the old meaning-only enrichment with one pass that also guarantees an
# English example and Arabic translation of that example.
start = s.find("  Future<void> _autoFillMeanings(List<BookCandidate> list) async {")
end = s.find("  Future<void> _editCandidate(BookCandidate c) async {", start)
if start == -1 or end == -1:
    raise SystemExit('auto-fill function anchors not found')

new_func = r'''  Future<void> _autoFillMeanings(List<BookCandidate> list) async {
    if (list.isEmpty) return;

    // Give every candidate a usable English example before translation.
    for (final c in list) {
      if (c.exampleEn.trim().isEmpty) {
        c.exampleEn = _generatedExample(c.word);
        c.exampleGenerated = true;
      }
    }

    final manager = OnDeviceTranslatorModelManager();
    final source = TranslateLanguage.english;
    final target = TranslateLanguage.arabic;
    try {
      final enReady = await manager.isModelDownloaded(source.bcpCode);
      if (!enReady) await manager.downloadModel(source.bcpCode, isWifiRequired: false);
      final arReady = await manager.isModelDownloaded(target.bcpCode);
      if (!arReady) await manager.downloadModel(target.bcpCode, isWifiRequired: false);

      final translator = OnDeviceTranslator(sourceLanguage: source, targetLanguage: target);
      try {
        for (var i = 0; i < list.length; i++) {
          final c = list[i];
          if (c.meaning.trim().isEmpty) {
            try {
              final translated = (await translator.translateText(c.word)).trim();
              if (translated.isNotEmpty && translated.toLowerCase() != c.word.toLowerCase()) {
                c.meaning = translated;
              }
            } catch (_) {}
          }

          // Always translate the actual sentence currently attached to the card.
          // This avoids reusing an Arabic sentence that belonged to another example.
          if (c.exampleEn.trim().isNotEmpty) {
            try {
              final translatedSentence = (await translator.translateText(c.exampleEn)).trim();
              if (translatedSentence.isNotEmpty && translatedSentence.toLowerCase() != c.exampleEn.toLowerCase()) {
                c.exampleAr = translatedSentence;
              }
            } catch (_) {}
          }

          if (mounted && (i % 20 == 0 || i == list.length - 1)) {
            setState(() {});
          }
        }
      } finally {
        translator.close();
      }
    } catch (_) {
      // Extraction remains usable even if the language models could not be downloaded.
      // Generated English examples stay editable and unresolved Arabic fields remain reviewable.
    }
  }

'''
s = s[:start] + new_func + s[end:]

# Make the review dialog and list clearly say where an example came from.
s = s.replace(
    "TextField(controller: exampleEn, textDirection: TextDirection.ltr, maxLines: 3, decoration: const InputDecoration(labelText: 'مثال إنجليزي من الكتاب'))",
    "TextField(controller: exampleEn, textDirection: TextDirection.ltr, maxLines: 3, decoration: InputDecoration(labelText: c.exampleGenerated ? 'مثال إنجليزي مولّد' : 'مثال إنجليزي من الكتاب'))",
    1,
)
s = s.replace(
    "if (c.exampleEn.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 5), child: Text(c.exampleEn, textDirection: TextDirection.ltr, maxLines: 2, overflow: TextOverflow.ellipsis)),",
    "if (c.exampleEn.isNotEmpty) ...[Padding(padding: const EdgeInsets.only(top: 5), child: Text(c.exampleEn, textDirection: TextDirection.ltr, maxLines: 2, overflow: TextOverflow.ellipsis)), Text(c.exampleGenerated ? 'مثال مولّد • الترجمة العربية تلقائية' : 'مثال من الكتاب • الترجمة العربية تلقائية', style: const TextStyle(fontSize: 11, color: Color(0xff64748b)))],",
    1,
)

# If the user edits a generated sentence manually, treat it as a reviewed custom example.
s = s.replace(
    "        c.exampleEn = exampleEn.text.trim();\n        c.exampleAr = exampleAr.text.trim();",
    "        c.exampleEn = exampleEn.text.trim();\n        c.exampleAr = exampleAr.text.trim();\n        c.exampleGenerated = false;",
    1,
)

p.write_text(s, encoding='utf-8')
print('Jordan v3.2.2 sentence translation and fallback examples patch applied')
