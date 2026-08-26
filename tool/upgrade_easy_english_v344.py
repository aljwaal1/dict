from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

s = s.replace("const appVersion = '3.4.3';", "const appVersion = '3.4.4';")

# Unify the flash-card section name everywhere the training hub or page title uses an older label.
s = s.replace("title: 'البطاقات', subtitle: 'تعلم كلمة كلمة'", "title: 'بطاقات سريعة', subtitle: 'تعلم الكلمة مع النطق والمعنى والمثال'")
s = s.replace("AppBar(title: const Text('البطاقات التعليمية')", "AppBar(title: const Text('بطاقات سريعة')")
s = s.replace("أو بطاقات تعليمية ليبني المدرب الذكي", "أو بطاقات سريعة ليبني المدرب الذكي")

# PDF extraction rule requested by the user: keep all normal English vocabulary and remove only
# prepositions, conjunctions, obvious proper names/places, and extraction noise.
start = s.index('  static const _stopWords = <String>{', s.index('class _BookLabPageState'))
end = s.index('  bool _instructionLike(String text)', start)
new_filter = r'''  static const _stopWords = <String>{
    // English prepositions / prepositional function words.
    'about','above','across','after','against','along','among','around','at','before','behind','below','beneath','beside','besides','between','beyond',
    'by','despite','down','during','except','for','from','in','inside','into','like','near','of','off','on','onto','opposite','outside','over','past','since',
    'through','throughout','to','toward','towards','under','underneath','until','up','upon','via','with','within','without',
    // Conjunctions / connectors.
    'and','or','but','nor','for','yet','so','although','though','because','since','unless','until','while','whereas','whether','if','than','once',
    // Obvious PDF structural noise, not vocabulary from the lesson itself.
    'unit','lesson','page','pages'
  };

  static const _knownProperNames = <String>{
    // Common person names that frequently occur in school books.
    'adam','ahmed','ali','amal','amina','anna','ben','david','emma','fatima','george','hassan','helen','ibrahim','jack','james','jane','john','joseph',
    'khaled','layla','linda','lisa','maria','mary','michael','mohamed','mohammad','mohammed','mona','nancy','nora','omar','peter','rasha','sally','sara','sarah',
    'sam','sami','samer','sara','susan','tom','yousef','yusuf','zaid','zeinab','zainab',
    // Countries, major cities and common geographic names.
    'amman','aqaba','athens','australia','austria','baghdad','bahrain','beijing','berlin','brazil','britain','cairo','canada','china','damascus','denmark',
    'dubai','egypt','england','europe','finland','france','germany','greece','india','iraq','ireland','istanbul','italy','japan','jerusalem','jordan','kuwait',
    'london','madrid','morocco','moscow','newyork','norway','oman','paris','poland','qatar','riyadh','rome','russia','saudi','scotland','spain','stockholm',
    'sweden','switzerland','syria','tokyo','turkey','uae','ukraine','yemen'
  };

  bool _validWord(String raw, {required bool midSentenceTitleCase}) {
    final w = raw.trim();
    if (!RegExp(r"^[A-Za-z][A-Za-z'-]*$").hasMatch(w)) return false;
    final lower = w.toLowerCase();
    if (lower.length < 2 || lower.length > 32) return false;
    if (_stopWords.contains(lower)) return false;
    if (_knownProperNames.contains(lower.replaceAll(RegExp(r"[-']"), ''))) return false;
    if (RegExp(r'^([a-z])\\1+$').hasMatch(lower)) return false;

    // A title-cased token in the middle of a sentence is overwhelmingly likely to be a
    // person/place/proper name. Sentence-initial words are kept because ordinary words are
    // capitalised there as well.
    if (midSentenceTitleCase && RegExp(r'^[A-Z][a-z]+(?:[-\'][A-Z]?[a-z]+)?$').hasMatch(w)) return false;
    return true;
  }

'''
s = s[:start] + new_filter + s[end:]

# Keep every allowed word, including words that occur only once. LinkedHashMap preserves
# first appearance in the PDF, so the review list follows book order instead of frequency.
old_list = """      final list = map.values.where((e) => e.meaning.trim().isNotEmpty || e.exampleEn.trim().isNotEmpty || e.frequency >= 3).where((e) => !_stopWords.contains(e.word.toLowerCase())).toList();
      list.sort((a, b) {
        final f = b.frequency.compareTo(a.frequency);
        if (f != 0) return f;
        return a.word.compareTo(b.word);
      });"""
new_list = """      final list = map.values.toList(growable: true);"""
if old_list not in s:
    raise SystemExit('PDF candidate list block not found')
s = s.replace(old_list, new_list)
s = s.replace("لم يتم العثور على كلمات تعليمية مناسبة", "لم يتم العثور على كلمات صالحة بعد استبعاد حروف الجر والعطف والأسماء والأماكن")

# Replace the crowded flash-card screen with a scroll-safe compact layout.
flash_start = s.index('class FlashCardsPage extends StatefulWidget')
flash_end = s.index('class QuizSetupPage extends StatefulWidget', flash_start)
new_flash = r'''class FlashCardsPage extends StatefulWidget {
  final Store store;
  const FlashCardsPage({super.key, required this.store});

  @override
  State<FlashCardsPage> createState() => _FlashCardsPageState();
}

class _FlashCardsPageState extends State<FlashCardsPage> {
  String grade = '1';
  int index = 0;
  bool showMeaning = true;
  bool showExample = true;

  @override
  void initState() {
    super.initState();
    index = widget.store.lastIndex(grade);
    WidgetsBinding.instance.addPostFrameCallback((_) => _markCurrent());
  }

  void _markCurrent() {
    final list = widget.store.byGrade(grade);
    if (list.isNotEmpty && index < list.length) widget.store.markStudied(list[index]);
  }

  void move(int delta, int length) {
    if (length == 0) return;
    setState(() {
      index = (index + delta) % length;
      if (index < 0) index += length;
      // Keep meaning/example visible by default; this avoids an empty-looking card.
      showMeaning = true;
      showExample = true;
    });
    widget.store.saveLastIndex(grade, index);
    _markCurrent();
  }

  Future<void> pronounce(BuildContext context, String value) async {
    final list = widget.store.byGrade(grade);
    if (list.isNotEmpty && index < list.length) await widget.store.markStudied(list[index]);
    final ok = await widget.store.speak(value);
    if (!ok && context.mounted) snack(context, 'تعذر تشغيل النطق. فعّل محرك تحويل النص إلى كلام الإنجليزي من إعدادات الهاتف');
  }

  Widget _bottomButton({required Widget child}) => SizedBox(height: 44, child: child);

  @override
  Widget build(BuildContext context) {
    final list = widget.store.byGrade(grade);
    if (list.isNotEmpty && index >= list.length) index = 0;
    final word = list.isEmpty ? null : list[index];
    final hasExample = word != null && (word.exampleEn.isNotEmpty || word.exampleAr.isNotEmpty);

    return Scaffold(
      appBar: AppBar(title: const Text('بطاقات سريعة'), toolbarHeight: 52),
      body: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(10, 4, 10, 8),
          child: Column(children: [
            DropdownButtonFormField<String>(
              initialValue: grade,
              isExpanded: true,
              items: grades.map((g) => DropdownMenuItem(value: g, child: Text(gradeName(g)))).toList(),
              onChanged: (value) {
                setState(() {
                  grade = value ?? '1';
                  index = widget.store.lastIndex(grade);
                  showMeaning = true;
                  showExample = true;
                });
                _markCurrent();
              },
              decoration: const InputDecoration(contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 10)),
            ),
            const SizedBox(height: 5),
            if (word != null)
              Text('${index + 1} من ${list.length}', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 14)),
            const SizedBox(height: 5),
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
                        margin: EdgeInsets.zero,
                        child: ListView(
                          padding: const EdgeInsets.fromLTRB(14, 14, 14, 18),
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Flexible(child: Text(word.en, textDirection: TextDirection.ltr, textAlign: TextAlign.center, style: const TextStyle(fontSize: 36, fontWeight: FontWeight.w900))),
                                IconButton(onPressed: () => pronounce(context, word.en), tooltip: 'لفظ الكلمة', icon: const Icon(Icons.volume_up_rounded, size: 27)),
                              ],
                            ),
                            Text(gradeName(word.grade), textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, color: Color(0xff64748b), fontWeight: FontWeight.w700)),
                            const SizedBox(height: 10),
                            Row(children: [
                              Expanded(child: OutlinedButton.icon(
                                onPressed: () => setState(() => showMeaning = !showMeaning),
                                icon: const Icon(Icons.translate_rounded, size: 18),
                                label: Text(showMeaning ? 'إخفاء المعنى' : 'إظهار المعنى'),
                              )),
                              if (hasExample) ...[
                                const SizedBox(width: 7),
                                Expanded(child: OutlinedButton.icon(
                                  onPressed: () => setState(() => showExample = !showExample),
                                  icon: const Icon(Icons.format_quote_rounded, size: 18),
                                  label: Text(showExample ? 'إخفاء المثال' : 'إظهار المثال'),
                                )),
                              ],
                            ]),
                            if (showMeaning) ...[
                              const SizedBox(height: 9),
                              Container(
                                width: double.infinity,
                                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                                decoration: BoxDecoration(color: const Color(0xffdbeafe), borderRadius: BorderRadius.circular(16)),
                                child: Text(word.ar, textAlign: TextAlign.center, style: const TextStyle(fontSize: 25, fontWeight: FontWeight.w900, height: 1.3)),
                              ),
                            ],
                            if (hasExample && showExample) ...[
                              const SizedBox(height: 9),
                              Container(
                                width: double.infinity,
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(color: const Color(0xfff3e8ff), borderRadius: BorderRadius.circular(16)),
                                child: Column(children: [
                                  if (word.exampleEn.isNotEmpty) ...[
                                    Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                      Expanded(child: Text(word.exampleEn, textDirection: TextDirection.ltr, textAlign: TextAlign.left, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, height: 1.45))),
                                      IconButton(onPressed: () => pronounce(context, word.exampleEn), tooltip: 'لفظ الجملة', icon: const Icon(Icons.volume_up_rounded, size: 21)),
                                    ]),
                                  ],
                                  if (word.exampleAr.isNotEmpty) ...[
                                    if (word.exampleEn.isNotEmpty) const Divider(height: 18),
                                    Text(word.exampleAr, textAlign: TextAlign.right, style: const TextStyle(fontSize: 15, height: 1.5, fontWeight: FontWeight.w600)),
                                  ],
                                ]),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
            ),
            const SizedBox(height: 6),
            Row(children: [
              Expanded(child: _bottomButton(child: OutlinedButton.icon(onPressed: word == null ? null : () => move(-1, list.length), icon: const Icon(Icons.arrow_forward_rounded, size: 21, textDirection: TextDirection.ltr), label: const Text('السابق')))),
              const SizedBox(width: 7),
              Expanded(child: _bottomButton(child: FilledButton.icon(onPressed: word == null ? null : () => move(1, list.length), icon: const Icon(Icons.arrow_back_rounded, size: 21, textDirection: TextDirection.ltr), label: const Text('التالي')))),
            ]),
            const SizedBox(height: 5),
            Row(children: [
              Expanded(child: _bottomButton(child: OutlinedButton.icon(
                style: OutlinedButton.styleFrom(foregroundColor: const Color(0xffb45309), side: const BorderSide(color: Color(0xfff59e0b))),
                onPressed: word == null ? null : () async { await widget.store.setReviewState(word, masteredNow: false); move(1, list.length); },
                icon: const Icon(Icons.refresh_rounded, size: 18), label: const Text('تحتاج مراجعة')))),
              const SizedBox(width: 7),
              Expanded(child: _bottomButton(child: FilledButton.icon(
                style: FilledButton.styleFrom(backgroundColor: const Color(0xff059669), foregroundColor: Colors.white),
                onPressed: word == null ? null : () async { await widget.store.setReviewState(word, masteredNow: true); move(1, list.length); },
                icon: const Icon(Icons.check_rounded, size: 18), label: const Text('أتقنتها')))),
            ]),
          ]),
        ),
      ),
    );
  }
}

'''
s = s[:flash_start] + new_flash + s[flash_end:]

p.write_text(s, encoding='utf-8')

pub = Path('pubspec.yaml')
ps = pub.read_text(encoding='utf-8')
ps = re.sub(r'^version:\s*3\.4\.3\+32$', 'version: 3.4.4+33', ps, flags=re.M)
pub.write_text(ps, encoding='utf-8')

print('Easy English AI v3.4.4 upgrade applied')
