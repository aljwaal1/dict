from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text(encoding='utf-8')

old_pages = "late final pages = [HomePage(store: widget.store), DictionaryPage(store: widget.store), GradesPage(store: widget.store), StatsPage(store: widget.store), SettingsPage(store: widget.store)];"
new_pages = "late final pages = [HomePage(store: widget.store), SearchPage(store: widget.store), DictionaryPage(store: widget.store), GradesPage(store: widget.store), StatsPage(store: widget.store), SettingsPage(store: widget.store)];"
if old_pages in s:
    s = s.replace(old_pages, new_pages, 1)

old_nav = """          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'الرئيسية'),
          NavigationDestination(icon: Icon(Icons.search), label: 'القاموس'),
          NavigationDestination(icon: Icon(Icons.school_outlined), selectedIcon: Icon(Icons.school), label: 'الصفوف'),
          NavigationDestination(icon: Icon(Icons.insights_outlined), selectedIcon: Icon(Icons.insights), label: 'التقدم'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: 'الإعدادات'),"""
new_nav = """          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'الرئيسية'),
          NavigationDestination(icon: Icon(Icons.search_rounded), selectedIcon: Icon(Icons.search), label: 'بحث'),
          NavigationDestination(icon: Icon(Icons.menu_book_outlined), selectedIcon: Icon(Icons.menu_book), label: 'القاموس'),
          NavigationDestination(icon: Icon(Icons.school_outlined), selectedIcon: Icon(Icons.school), label: 'الصفوف'),
          NavigationDestination(icon: Icon(Icons.insights_outlined), selectedIcon: Icon(Icons.insights), label: 'التقدم'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: 'الإعدادات'),"""
if old_nav in s:
    s = s.replace(old_nav, new_nav, 1)

anchor = "class DictionaryPage extends StatefulWidget {"
if 'class SearchPage extends StatefulWidget' not in s:
    search_page = r'''
class SearchPage extends StatefulWidget {
  final Store store;
  const SearchPage({super.key, required this.store});

  @override
  State<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends State<SearchPage> {
  final controller = TextEditingController();
  String query = '';
  String gradeFilter = 'all';

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  List<WordItem> get results {
    final q = query.trim().toLowerCase();
    if (q.isEmpty) return [];
    return widget.store.words.where((w) {
      final matchesGrade = gradeFilter == 'all' || w.grade == gradeFilter;
      if (!matchesGrade) return false;
      return w.en.toLowerCase().contains(q) ||
          w.ar.contains(query.trim()) ||
          w.exampleEn.toLowerCase().contains(q) ||
          w.exampleAr.contains(query.trim());
    }).toList(growable: false);
  }

  @override
  Widget build(BuildContext context) {
    final list = results;
    return Scaffold(
      appBar: AppBar(title: const Text('البحث')),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
          child: TextField(
            controller: controller,
            autofocus: false,
            textInputAction: TextInputAction.search,
            onChanged: (v) => setState(() => query = v),
            decoration: InputDecoration(
              prefixIcon: const Icon(Icons.search_rounded),
              hintText: 'ابحث بكلمة، معنى أو جملة',
              suffixIcon: query.isEmpty
                  ? null
                  : IconButton(
                      tooltip: 'مسح البحث',
                      icon: const Icon(Icons.close_rounded),
                      onPressed: () {
                        controller.clear();
                        setState(() => query = '');
                      },
                    ),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: DropdownButtonFormField<String>(
            initialValue: gradeFilter,
            decoration: const InputDecoration(labelText: 'تصفية حسب الصف'),
            items: [
              const DropdownMenuItem(value: 'all', child: Text('كل الصفوف')),
              ...grades.map((g) => DropdownMenuItem(value: g, child: Text(gradeName(g)))),
            ],
            onChanged: (v) => setState(() => gradeFilter = v ?? 'all'),
          ),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: query.trim().isEmpty
              ? const Center(child: Text('اكتب كلمة أو معنى أو جزءاً من جملة للبحث'))
              : list.isEmpty
                  ? const Center(child: Text('لا توجد نتائج مطابقة'))
                  : ListView.builder(
                      keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                      itemCount: list.length,
                      itemBuilder: (_, i) {
                        final w = list[i];
                        return Card(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                ListTile(
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 8),
                                  title: Text(w.en, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
                                  subtitle: Text('${w.ar} • ${gradeName(w.grade)}'),
                                  trailing: IconButton(
                                    tooltip: 'نطق الكلمة',
                                    icon: const Icon(Icons.volume_up_rounded),
                                    onPressed: () => widget.store.speak(w.en),
                                  ),
                                  onTap: () => showWord(context, widget.store, w, source: list, initialIndex: i),
                                ),
                                if (w.exampleEn.isNotEmpty) ...[
                                  const Divider(height: 14),
                                  Row(children: [
                                    Expanded(child: Text(w.exampleEn, textDirection: TextDirection.ltr, style: const TextStyle(fontWeight: FontWeight.w700))),
                                    IconButton(
                                      tooltip: 'نطق الجملة',
                                      icon: const Icon(Icons.volume_up_outlined),
                                      onPressed: () => widget.store.speak(w.exampleEn),
                                    ),
                                  ]),
                                  if (w.exampleAr.isNotEmpty)
                                    Padding(
                                      padding: const EdgeInsets.fromLTRB(8, 0, 8, 8),
                                      child: Text(w.exampleAr),
                                    ),
                                ],
                              ],
                            ),
                          ),
                        );
                      },
                    ),
        ),
      ]),
    );
  }
}

'''
    if anchor not in s:
        raise SystemExit('DictionaryPage anchor not found')
    s = s.replace(anchor, search_page + anchor, 1)

# Keep the existing dictionary as a browsing screen; search now has its own screen.
s = s.replace("appBar: AppBar(title: const Text('القاموس')),\n      body: Column(children: [\n        Padding(", "appBar: AppBar(title: const Text('القاموس')),\n      body: Column(children: [\n        Padding(", 1)

p.write_text(s, encoding='utf-8')
print('Standalone Jordan dictionary search screen patch applied')
