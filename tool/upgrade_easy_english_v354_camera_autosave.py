from pathlib import Path

JS=Path('lib/main.dart')
PUB=Path('pubspec.yaml')
s=JS.read_text(encoding='utf-8')
p=PUB.read_text(encoding='utf-8')

if "const appVersion = '3.5.4'" in s and "pickAndAnalyzeImages" in s and "booklab_latest_draft" in s:
    raise SystemExit(0)

s=s.replace("const appVersion = '3.5.3';","const appVersion = '3.5.4';")
if "package:image_picker/image_picker.dart" not in s:
    s=s.replace("import 'package:http/http.dart' as http;\n",
                "import 'package:http/http.dart' as http;\nimport 'package:image_picker/image_picker.dart';\nimport 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';\n")

anchor="""  BookCandidate({
    required this.word,
    this.meaning = '',
    this.exampleEn = '',
    this.exampleAr = '',
    this.unit = '',
    this.lesson = '',
    this.page = '',
    this.frequency = 1,
    this.selected = true,
    this.exampleGenerated = false,
  });
}"""
replacement="""  BookCandidate({
    required this.word,
    this.meaning = '',
    this.exampleEn = '',
    this.exampleAr = '',
    this.unit = '',
    this.lesson = '',
    this.page = '',
    this.frequency = 1,
    this.selected = true,
    this.exampleGenerated = false,
  });

  Map<String, dynamic> toJson() => {
    'word': word,
    'meaning': meaning,
    'exampleEn': exampleEn,
    'exampleAr': exampleAr,
    'unit': unit,
    'lesson': lesson,
    'page': page,
    'frequency': frequency,
    'selected': selected,
    'exampleGenerated': exampleGenerated,
  };

  factory BookCandidate.fromJson(Map<String, dynamic> j) => BookCandidate(
    word: (j['word'] ?? '').toString(),
    meaning: (j['meaning'] ?? '').toString(),
    exampleEn: (j['exampleEn'] ?? '').toString(),
    exampleAr: (j['exampleAr'] ?? '').toString(),
    unit: (j['unit'] ?? '').toString(),
    lesson: (j['lesson'] ?? '').toString(),
    page: (j['page'] ?? '').toString(),
    frequency: int.tryParse((j['frequency'] ?? 1).toString()) ?? 1,
    selected: j['selected'] != false,
    exampleGenerated: j['exampleGenerated'] == true,
  );
}"""
if anchor not in s:
    raise SystemExit('BookCandidate anchor not found')
s=s.replace(anchor,replacement,1)

state_anchor="""  List<BookCandidate> candidates = [];
  int pagesRead = 0;

  static const _stopWords"""
state_extra="""  List<BookCandidate> candidates = [];
  int pagesRead = 0;
  final ImagePicker _imagePicker = ImagePicker();
  String _activeDraftSource = '';

  Future<void> _saveDraft({String phase = 'working'}) async {
    final payload = <String, dynamic>{
      'version': 1,
      'source': _activeDraftSource,
      'grade': grade,
      'semester': semester,
      'fileName': fileName,
      'pagesRead': pagesRead,
      'phase': phase,
      'savedAt': DateTime.now().millisecondsSinceEpoch,
      'candidates': candidates.map((e) => e.toJson()).toList(),
    };
    await widget.store.prefs.setString('booklab_latest_draft', jsonEncode(payload));
  }

  Future<Map<String, dynamic>?> _readDraft() async {
    final raw = widget.store.prefs.getString('booklab_latest_draft');
    if (raw == null || raw.isEmpty) return null;
    try {
      final x = jsonDecode(raw);
      return x is Map ? Map<String, dynamic>.from(x) : null;
    } catch (_) {
      return null;
    }
  }

  Future<void> _restoreLatestDraft() async {
    final x = await _readDraft();
    if (x == null) {
      if (mounted) snack(context, 'لا يوجد عمل محفوظ للاستعادة');
      return;
    }
    final list = (x['candidates'] as List? ?? const [])
        .whereType<Map>()
        .map((e) => BookCandidate.fromJson(Map<String, dynamic>.from(e)))
        .where((e) => e.word.isNotEmpty)
        .toList(growable: true);
    if (!mounted) return;
    setState(() {
      grade = (x['grade'] ?? grade).toString();
      semester = (x['semester'] ?? semester).toString();
      fileName = (x['fileName'] ?? 'عمل محفوظ').toString();
      pagesRead = int.tryParse((x['pagesRead'] ?? 0).toString()) ?? 0;
      _activeDraftSource = (x['source'] ?? 'restored').toString();
      candidates = list;
    });
    snack(context, 'تمت استعادة آخر عمل محفوظ • ' + list.length.toString() + ' كلمة');
  }

  Future<void> _clearDraft() async {
    await widget.store.prefs.remove('booklab_latest_draft');
    _activeDraftSource = '';
  }

  Map<String, String> _consumeText(
    String text,
    int pageNumber,
    Map<String, BookCandidate> map,
    String currentUnit,
    String currentLesson,
  ) {
    final unitMatch = RegExp(r'\\bUnit\\s+([0-9]+|[A-Za-z]+)', caseSensitive: false).firstMatch(text);
    final lessonMatch = RegExp(r'\\bLesson\\s+([0-9]+|[A-Za-z]+)', caseSensitive: false).firstMatch(text);
    if (unitMatch != null) {
      final v = (unitMatch.group(1) ?? '').trim();
      if (v.isNotEmpty && v.toLowerCase() != 'unit') currentUnit = 'Unit ' + v;
    }
    if (lessonMatch != null) {
      final v = (lessonMatch.group(1) ?? '').trim();
      if (v.isNotEmpty && v.toLowerCase() != 'lesson') currentLesson = 'Lesson ' + v;
    }
    final tokens = RegExp(r"[A-Za-z][A-Za-z'-]*").allMatches(text).toList();
    for (var ti = 0; ti < tokens.length; ti++) {
      final raw = tokens[ti].group(0)!;
      final prefixStart = tokens[ti].start > 2 ? tokens[ti].start - 2 : 0;
      final prefix = text.substring(prefixStart, tokens[ti].start);
      final startsSentence = ti == 0 || RegExp(r'[.!?]\\s*$').hasMatch(prefix);
      if (!_validWord(raw, midSentenceTitleCase: !startsSentence)) continue;
      final key = raw.toLowerCase();
      final existing = _existingWord(raw);
      final found = map[key];
      if (found != null) {
        found.frequency++;
        if (found.exampleEn.isEmpty) found.exampleEn = _sentenceFor(text, raw);
      } else {
        map[key] = BookCandidate(
          word: key,
          meaning: existing?.ar ?? '',
          exampleEn: _sentenceFor(text, raw),
          exampleAr: existing?.exampleAr ?? '',
          unit: currentUnit,
          lesson: currentLesson,
          page: pageNumber.toString(),
        );
      }
    }
    return {'unit': currentUnit, 'lesson': currentLesson};
  }

  Future<void> _finishCandidates(List<BookCandidate> list) async {
    if (mounted) setState(() => candidates = List<BookCandidate>.from(list));
    await _saveDraft(phase: 'enriching');
    if (list.isNotEmpty) {
      await _fillQualityExamples(list);
      if (mounted) setState(() => candidates = List<BookCandidate>.from(list));
      await _saveDraft(phase: 'translating');
      await _autoFillMeanings(list);
      if (mounted) setState(() => candidates = List<BookCandidate>.from(list));
      await _saveDraft(phase: 'ready');
    }
  }

  static const _stopWords"""
if state_anchor not in s:
    raise SystemExit('state anchor not found')
s=s.replace(state_anchor,state_extra,1)

start=s.find("  Future<void> pickAndAnalyzePdf() async {")
end=s.find("\n  final Map<String, String> _onlineTranslationCache", start)
if start < 0 or end < 0:
    raise SystemExit('PDF method block not found')

new_methods=r'''  Future<void> pickAndAnalyzePdf() async {
    final picked = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['pdf']);
    if (picked == null || picked.files.isEmpty) return;
    final file = picked.files.first;
    if (file.path == null) {
      if (mounted) snack(context, 'تعذر الوصول إلى مسار ملف PDF على هذا الجهاز');
      return;
    }
    final size = await File(file.path!).length();
    final sourceKey = 'pdf:' + file.name + ':' + size.toString() + ':' + grade + ':' + semester;
    final draft = await _readDraft();
    final canResume = draft != null && (draft['source'] ?? '').toString() == sourceKey;
    final map = <String, BookCandidate>{};
    var completedPages = 0;
    String currentUnit = '';
    String currentLesson = '';
    if (canResume) {
      for (final raw in (draft['candidates'] as List? ?? const [])) {
        if (raw is Map) {
          final c = BookCandidate.fromJson(Map<String, dynamic>.from(raw));
          if (c.word.isNotEmpty) map[c.word.toLowerCase()] = c;
        }
      }
      completedPages = int.tryParse((draft['pagesRead'] ?? 0).toString()) ?? 0;
      for (final c in map.values.toList().reversed) {
        if (currentUnit.isEmpty && c.unit.isNotEmpty) currentUnit = c.unit;
        if (currentLesson.isEmpty && c.lesson.isNotEmpty) currentLesson = c.lesson;
        if (currentUnit.isNotEmpty && currentLesson.isNotEmpty) break;
      }
    }
    setState(() {
      busy = true;
      fileName = file.name;
      candidates = map.values.toList(growable: true);
      pagesRead = completedPages;
      _activeDraftSource = sourceKey;
    });
    try {
      await ensurePdfRuntime();
      final document = await PdfDocument.openFile(file.path!);
      try {
        for (var pi = completedPages; pi < document.pages.length; pi++) {
          final pageText = await document.pages[pi].loadText();
          final text = pageText?.fullText ?? '';
          final scope = _consumeText(text, pi + 1, map, currentUnit, currentLesson);
          currentUnit = scope['unit'] ?? currentUnit;
          currentLesson = scope['lesson'] ?? currentLesson;
          completedPages = pi + 1;
          if (mounted) {
            setState(() {
              pagesRead = completedPages;
              candidates = map.values.toList(growable: true);
            });
          }
          await _saveDraft(phase: 'reading-pdf');
        }
      } finally {
        await document.dispose();
      }
      final list = map.values.toList(growable: true);
      await _finishCandidates(list);
      if (mounted && list.isEmpty) snack(context, 'تمت قراءة الملف لكن لم يتم العثور على كلمات صالحة بعد التصفية');
    } catch (e) {
      await _saveDraft(phase: 'interrupted');
      if (mounted) snack(context, 'توقف تحليل PDF، لكن تم حفظ ما تم إنجازه: ' + e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> pickAndAnalyzeImages({required bool camera}) async {
    List<XFile> images = [];
    if (camera) {
      final one = await _imagePicker.pickImage(source: ImageSource.camera, imageQuality: 95);
      if (one != null) images = [one];
    } else {
      images = await _imagePicker.pickMultiImage(imageQuality: 95);
    }
    if (images.isEmpty) return;

    final sourceKey = 'images:' + DateTime.now().millisecondsSinceEpoch.toString() + ':' + grade + ':' + semester;
    final map = <String, BookCandidate>{};
    String currentUnit = '';
    String currentLesson = '';
    setState(() {
      busy = true;
      fileName = camera ? 'صورة من الكاميرا' : images.length.toString() + ' صور';
      candidates = [];
      pagesRead = 0;
      _activeDraftSource = sourceKey;
    });

    final recognizer = TextRecognizer(script: TextRecognitionScript.latin);
    try {
      for (var i = 0; i < images.length; i++) {
        final input = InputImage.fromFilePath(images[i].path);
        final recognized = await recognizer.processImage(input);
        final scope = _consumeText(recognized.text, i + 1, map, currentUnit, currentLesson);
        currentUnit = scope['unit'] ?? currentUnit;
        currentLesson = scope['lesson'] ?? currentLesson;
        if (mounted) {
          setState(() {
            pagesRead = i + 1;
            candidates = map.values.toList(growable: true);
          });
        }
        await _saveDraft(phase: camera ? 'ocr-camera' : 'ocr-gallery');
      }
      final list = map.values.toList(growable: true);
      await _finishCandidates(list);
      if (mounted && list.isEmpty) snack(context, 'تمت قراءة الصورة لكن لم يتم العثور على كلمات إنجليزية مناسبة');
    } catch (e) {
      await _saveDraft(phase: 'interrupted');
      if (mounted) snack(context, 'توقف التعرف على الصورة، لكن تم حفظ ما تم إنجازه: ' + e.toString());
    } finally {
      recognizer.close();
      if (mounted) setState(() => busy = false);
    }
  }
'''
s=s[:start]+new_methods+s[end:]

s=s.replace("      if (mounted) setState(() {});\n    }\n    for (final c in missing) {",
            "      if (mounted) setState(() {});\n      await _saveDraft(phase: 'examples');\n    }\n    for (final c in missing) {",1)

s=s.replace("      if (mounted) setState(() {});\n    }\n  }\n\n  Future<void> _autoFillMeanings",
            "      if (mounted) setState(() {});\n      await _saveDraft(phase: 'online-translation');\n    }\n  }\n\n  Future<void> _autoFillMeanings",1)

s=s.replace("          if (mounted && (i % 20 == 0 || i == list.length - 1)) {\n            setState(() {});\n          }",
            "          if (i % 20 == 0 || i == list.length - 1) {\n            if (mounted) setState(() {});\n            await _saveDraft(phase: 'on-device-translation');\n          }",1)

s=s.replace("    final added = await widget.store._mergeImportedWords(items);\n    if (mounted) snack(context, added == 0 ? 'تم تحديث الكلمات الموجودة دون تكرار' : 'تم حفظ $added كلمة جديدة في القاموس');",
            "    final added = await widget.store._mergeImportedWords(items);\n    await _clearDraft();\n    if (mounted) snack(context, added == 0 ? 'تم تحديث الكلمات الموجودة دون تكرار' : 'تم حفظ ' + added.toString() + ' كلمة جديدة في القاموس');",1)

old_ui="""            const SizedBox(height: 10),
            SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: busy ? null : pickAndAnalyzePdf, icon: const Icon(Icons.picture_as_pdf_rounded), label: Text(busy ? 'جاري قراءة الكتاب...' : 'اختر كتاب PDF وابدأ الاستخراج'))),
            if (fileName.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 8), child: Text('$fileName • $pagesRead صفحة', style: const TextStyle(color: Color(0xff64748b)))),
"""
new_ui="""            const SizedBox(height: 10),
            Row(children: [
              Expanded(child: FilledButton.icon(onPressed: busy ? null : pickAndAnalyzePdf, icon: const Icon(Icons.picture_as_pdf_rounded), label: const Text('PDF'))),
              const SizedBox(width: 8),
              Expanded(child: FilledButton.icon(onPressed: busy ? null : () => pickAndAnalyzeImages(camera: true), icon: const Icon(Icons.camera_alt_rounded), label: const Text('الكاميرا'))),
              const SizedBox(width: 8),
              Expanded(child: FilledButton.icon(onPressed: busy ? null : () => pickAndAnalyzeImages(camera: false), icon: const Icon(Icons.photo_library_rounded), label: const Text('صور'))),
            ]),
            const SizedBox(height: 8),
            SizedBox(width: double.infinity, child: OutlinedButton.icon(onPressed: busy ? null : _restoreLatestDraft, icon: const Icon(Icons.restore_rounded), label: const Text('استعادة آخر عمل محفوظ'))),
            const Padding(
              padding: EdgeInsets.only(top: 7),
              child: Text('يحفظ التطبيق تلقائيًا بعد كل صفحة أو صورة وبعد كل دفعة ترجمة.', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, color: Color(0xff64748b))),
            ),
            if (fileName.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 8), child: Text(fileName + ' • ' + pagesRead.toString() + ' صفحة/صورة', style: const TextStyle(color: Color(0xff64748b)))),
"""
if old_ui not in s:
    raise SystemExit('BookLab UI anchor not found')
s=s.replace(old_ui,new_ui,1)

s=s.replace("const Text('حوّل أي كتاب إلى قاموس بالذكاء الاصطناعي'", "const Text('حوّل كتابًا أو صورة إلى قاموس بالذكاء الاصطناعي'",1)
s=s.replace("const Text('يحلل PDF، يكتشف بنية الكتاب، ينظف المفردات، ويستخدم التعلم الآلي للترجمة واقتراح أمثلة قبل أن تراجعها وتحفظها.'",
            "const Text('استخدم PDF أو صوّر صفحة مباشرة أو اختر صورًا من الهاتف. يستخرج النص محليًا، ينظف المفردات، ويترجمها مع حفظ العمل أولًا بأول.'",1)
s=s.replace("subtitle: 'استخرج المفردات والمعاني والجمل من أي كتاب PDF'", "subtitle: 'PDF أو كاميرا أو صور • استخراج الكلمات مع حفظ تلقائي'",1)
s=s.replace("subtitle: 'ارفع PDF وحوله لقاموس'", "subtitle: 'PDF أو كاميرا أو صور'",1)

JS.write_text(s,encoding='utf-8')

p=p.replace("version: 3.5.3+38","version: 3.5.4+39")
if "image_picker:" not in p:
    p=p.replace("  http: ^1.2.2\n", "  http: ^1.2.2\n  image_picker: ^1.1.2\n  google_mlkit_text_recognition: ^0.17.0\n")
PUB.write_text(p,encoding='utf-8')
