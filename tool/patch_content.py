from pathlib import Path

path = Path('lib/main.dart')
text = path.read_text(encoding='utf-8')

if 'Future<void> addWord(' not in text:
    marker = "  Map<String, dynamic> _allPrefsSnapshot() {"
    method = r'''  Future<void> addWord({
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

'''
    text = text.replace(marker, method + marker)

if 'class AddWordPage extends StatefulWidget' not in text:
    marker = 'class SettingsPage extends StatelessWidget'
    pages = r'''class AddWordPage extends StatefulWidget {
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

'''
    text = text.replace(marker, pages + marker)

settings_marker = "          Card(child: SwitchListTile(secondary: const Icon(Icons.volume_up_outlined), title: const Text('الأصوات والنطق'), subtitle: const Text('صوت الضغط ونطق الكلمات الإنجليزية'), value: store.sound, onChanged: store.setSound)),"
settings_add = settings_marker + r'''
          const SectionTitle('إدارة المحتوى'),
          SettingsTile(icon: Icons.add_circle_outline_rounded, title: 'إضافة كلمة', subtitle: 'إضافة كلمة ومعنى وجملة مثال', onTap: () => push(context, AddWordPage(store: store))),
          SettingsTile(icon: Icons.people_alt_outlined, title: 'إدارة الملفات الشخصية', subtitle: 'إضافة طالب أو التبديل بين الملفات', onTap: () => push(context, ProfilesPage(store: store))),
          SettingsTile(icon: Icons.format_quote_rounded, title: 'الجمل التعليمية', subtitle: 'عرض الجمل الإنجليزية وترجمتها مع النطق', onTap: () => push(context, SentencesPage(store: store))),'''
if "title: 'إضافة كلمة'" not in text:
    text = text.replace(settings_marker, settings_add)

path.write_text(text, encoding='utf-8')
print('Applied content-management pages')
