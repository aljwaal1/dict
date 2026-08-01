from pathlib import Path
import re

p = Path('lib/main.dart')
text = p.read_text(encoding='utf-8')

# Visible version.
text = re.sub(r"const appVersion = '[^']+';", "const appVersion = '2.1.1';", text, count=1)

# Improve Android TTS routing/clarity while keeping volume at the supported maximum.
text = text.replace(
    "      await tts.awaitSpeakCompletion(false);\n      await tts.setSpeechRate(.42);",
    "      await tts.awaitSpeakCompletion(false);\n      try { await tts.setAudioAttributesForNavigation(); } catch (_) {}\n      await tts.setSpeechRate(.38);",
)
text = text.replace("      await tts.setSpeechRate(.42);", "      await tts.setSpeechRate(.38);")

# Replace merge logic so imported words receive stable unique IDs, existing progress is preserved,
# stale progress is removed, indices are clamped, and every screen refreshes immediately.
merge_pattern = re.compile(
    r"  Future<int> _mergeImportedWords\(List<WordItem> imported\) async \{.*?\n  \}\n\n  Future<int> importJsonWords",
    re.S,
)
merge_replacement = r'''  Future<int> _mergeImportedWords(List<WordItem> imported) async {
    final valid = imported
        .where((w) => w.en.trim().isNotEmpty && w.ar.trim().isNotEmpty && grades.contains(w.grade))
        .toList(growable: false);

    final existingByKey = <String, WordItem>{
      for (final w in words) '${w.grade}|${w.en.trim().toLowerCase()}': w,
    };
    var nextId = words.isEmpty ? 1 : words.map((w) => w.id).reduce(max) + 1;
    var added = 0;

    for (final incoming in valid) {
      final key = '${incoming.grade}|${incoming.en.trim().toLowerCase()}';
      final current = existingByKey[key];
      if (current != null) {
        // Keep the original ID so mastered/difficult statistics remain attached to the word.
        existingByKey[key] = WordItem(
          id: current.id,
          grade: incoming.grade,
          en: incoming.en.trim(),
          ar: incoming.ar.trim(),
          exampleEn: incoming.exampleEn.trim(),
          exampleAr: incoming.exampleAr.trim(),
        );
      } else {
        existingByKey[key] = WordItem(
          id: nextId++,
          grade: incoming.grade,
          en: incoming.en.trim(),
          ar: incoming.ar.trim(),
          exampleEn: incoming.exampleEn.trim(),
          exampleAr: incoming.exampleAr.trim(),
        );
        added++;
      }
    }

    words = existingByKey.values.toList(growable: true)
      ..sort((a, b) {
        final gradeCompare = grades.indexOf(a.grade).compareTo(grades.indexOf(b.grade));
        return gradeCompare != 0 ? gradeCompare : a.en.toLowerCase().compareTo(b.en.toLowerCase());
      });

    // Remove statistics that point to words no longer present, without marking new imports as learned.
    final validIds = words.map((w) => '${w.id}').toSet();
    mastered.removeWhere((id) => !validIds.contains(id));
    difficult.removeWhere((id) => !validIds.contains(id));
    wrongCounts.removeWhere((id, _) => !validIds.contains(id));

    // Keep each grade's last-card pointer inside the new word count.
    for (final grade in grades) {
      final total = words.where((w) => w.grade == grade).length;
      if (total == 0) {
        lastIndexByGrade[grade] = 0;
      } else {
        lastIndexByGrade[grade] = (lastIndexByGrade[grade] ?? 0).clamp(0, total - 1);
      }
    }

    await persistWords();
    await saveProgress();
    notifyListeners();
    return added;
  }

  Future<int> importJsonWords'''

if not merge_pattern.search(text):
    raise SystemExit('Could not locate _mergeImportedWords')
text = merge_pattern.sub(lambda _: merge_replacement, text, count=1)

# Ensure add-word also refreshes all dependent pages immediately.
text = text.replace(
    "    await persistWords();\n    notifyListeners();\n  }\n\n  Map<String, dynamic> _allPrefsSnapshot",
    "    await persistWords();\n    notifyListeners();\n  }\n\n  Map<String, dynamic> _allPrefsSnapshot",
    1,
)

p.write_text(text, encoding='utf-8')
print('Applied v2.1.1 live statistics refresh and clearer Android TTS routing')
