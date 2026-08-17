from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

if "package:read_pdf_text/read_pdf_text.dart" not in s:
    s = s.replace("import 'package:path_provider/path_provider.dart';", "import 'package:path_provider/path_provider.dart';\nimport 'package:read_pdf_text/read_pdf_text.dart';", 1)

s = s.replace("const appVersion = '3.0.0';", "const appVersion = '3.1.0';", 1)

start = s.find('class BookLabPage extends StatefulWidget')
end = s.find('class HomePage extends StatelessWidget')
if start == -1 or end == -1 or end <= start:
    raise SystemExit('BookLab/HomePage anchors not found')

booklab = r'''class BookCandidate {
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
      final pages = await ReadPdfText.getPDFtextPaginated(file.path!);
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

'''

s = s[:start] + booklab + s[end:]
p.write_text(s, encoding='utf-8')
print('Jordan Book Lab v3.1 patch applied')
