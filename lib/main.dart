
import 'dart:convert';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

const String developerEmail = 'yaya15112016@gmail.com';
const String dictionaryJsonUrl = 'https://raw.githubusercontent.com/YOUR_USER/qamoosi-school-content/main/words.json';

void main() => runApp(const QamoosiApp());

class QamoosiApp extends StatelessWidget {
  const QamoosiApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'قاموسي المدرسي',
      locale: const Locale('ar'),
      supportedLocales: const [Locale('ar'), Locale('en')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff42a5f5), brightness: Brightness.light),
        scaffoldBackgroundColor: const Color(0xfff7fbff),
        fontFamily: 'Roboto',
        cardTheme: CardThemeData(elevation: 0, color: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24))),
      ),
      home: const AppShell(),
    );
  }
}

class WordItem {
  final int id; final String grade; final String en; final String ar; final String source;
  WordItem({required this.id, required this.grade, required this.en, required this.ar, this.source=''});
  factory WordItem.fromJson(Map<String,dynamic> j)=> WordItem(id: j['id'] ?? 0, grade: '${j['grade']}', en: '${j['word_en']}', ar: '${j['meaning_ar']}', source: '${j['source'] ?? ''}');
  Map<String,dynamic> toJson()=> {'id':id,'grade':grade,'word_en':en,'meaning_ar':ar,'source':source};
  int difficulty(){
    final n = en.replaceAll(' ', '').length;
    if(n <= 5) return 1; if(n <= 9) return 2; return 3;
  }
  String difficultyText()=> ['','سهل','متوسط','صعب'][difficulty()];
}

class Profile {
  final int id; String name;
  Profile(this.id, this.name);
  Map<String,dynamic> toJson()=> {'id':id,'name':name};
  factory Profile.fromJson(Map<String,dynamic> j)=> Profile(j['id'], j['name']);
}

class Store extends ChangeNotifier {
  List<WordItem> words=[]; List<Profile> profiles=[]; int activeProfile=1; bool sound=true;
  Set<String> mastered={}; Set<String> difficult={}; Map<String,int> wrongCounts={}; double points=0;
  SharedPreferences? prefs; final FlutterTts tts=FlutterTts();

  Future<void> init() async {
    prefs = await SharedPreferences.getInstance();
    sound = prefs!.getBool('sound') ?? true;
    activeProfile = prefs!.getInt('activeProfile') ?? 1;
    final p = prefs!.getString('profiles');
    profiles = p == null ? [Profile(1,'الطالب 1')] : (jsonDecode(p) as List).map((e)=>Profile.fromJson(e)).toList();
    await _loadWords();
    await loadProgress();
    await tts.setLanguage('en-US'); await tts.setSpeechRate(0.42);
  }
  Future<void> _loadWords() async {
    final saved = prefs!.getString('words_json');
    final txt = saved ?? await rootBundle.loadString('assets/data/words.json');
    final data=jsonDecode(txt); words=(data['words'] as List).map((e)=>WordItem.fromJson(e)).toList();
  }
  String get key => 'p$activeProfile';
  Future<void> saveProfiles() async { await prefs!.setString('profiles', jsonEncode(profiles.map((e)=>e.toJson()).toList())); notifyListeners(); }
  Future<void> loadProgress() async {
    mastered = (prefs!.getStringList('$key.mastered') ?? []).toSet();
    difficult = (prefs!.getStringList('$key.difficult') ?? []).toSet();
    wrongCounts = Map<String,int>.from(jsonDecode(prefs!.getString('$key.wrongCounts') ?? '{}'));
    points = prefs!.getDouble('$key.points') ?? 0;
    notifyListeners();
  }
  Future<void> saveProgress() async {
    await prefs!.setStringList('$key.mastered', mastered.toList());
    await prefs!.setStringList('$key.difficult', difficult.toList());
    await prefs!.setString('$key.wrongCounts', jsonEncode(wrongCounts));
    await prefs!.setDouble('$key.points', points);
    notifyListeners();
  }
  Future<void> setActive(int id) async { activeProfile=id; await prefs!.setInt('activeProfile', id); await loadProgress(); }
  Future<void> setSound(bool v) async { sound = v; await prefs!.setBool('sound', v); notifyListeners(); }
  void click(){ if(sound) SystemSound.play(SystemSoundType.click); }
  Future<void> speak(String text) async { click(); await tts.stop(); await tts.speak(text); }
  List<WordItem> byGrade(String g)=> words.where((w)=>w.grade==g).toList();
  int masteredGrade(String g)=> byGrade(g).where((w)=>mastered.contains('${w.id}')).length;
  Future<void> answer(WordItem w, bool ok) async { if(ok){points += .5; mastered.add('${w.id}');} else {difficult.add('${w.id}'); wrongCounts['${w.id}']=(wrongCounts['${w.id}']??0)+1;} await saveProgress(); }
  Future<void> addWord(String en, String ar, String grade) async { final next=(words.map((e)=>e.id).fold(0, max))+1; words.add(WordItem(id:next, grade:grade, en:en.trim(), ar:ar.trim(), source:'manual')); await _persistWords(); notifyListeners(); }
  Future<void> _persistWords() async { await prefs!.setString('words_json', jsonEncode({'version':1,'words':words.map((e)=>e.toJson()).toList()})); }
  Future<String> updateFromUrl() async { final r=await http.get(Uri.parse(dictionaryJsonUrl)); if(r.statusCode!=200) throw Exception('تعذر تحميل الملف'); final data=jsonDecode(r.body); if(data['words'] is! List) throw Exception('ملف JSON غير صحيح'); words=(data['words'] as List).map((e)=>WordItem.fromJson(e)).toList(); await _persistWords(); notifyListeners(); return 'تم تحديث القاموس: ${words.length} كلمة'; }

}

class AppShell extends StatefulWidget { const AppShell({super.key}); @override State<AppShell> createState()=>_AppShellState(); }
class _AppShellState extends State<AppShell>{ final store=Store(); bool ready=false; @override void initState(){super.initState(); store.init().then((_){setState(()=>ready=true);});}
@override Widget build(BuildContext context){ if(!ready) return const Scaffold(body:Center(child:CircularProgressIndicator())); return AnimatedBuilder(animation:store,builder:(_,__)=>Home(store:store)); }}

Widget adBox(String text)=> Container(height:42, margin: const EdgeInsets.symmetric(horizontal:14, vertical:6), decoration:BoxDecoration(color: const Color(0xfffff8e1), borderRadius:BorderRadius.circular(16), border:Border.all(color: const Color(0xffffecb3))), child:Center(child:Text(text, style: const TextStyle(color: Colors.orange, fontWeight: FontWeight.bold))));
class PageFrame extends StatelessWidget{ final String title; final Widget child; const PageFrame({super.key, required this.title, required this.child}); @override Widget build(BuildContext c)=>Scaffold(appBar:AppBar(title:Text(title),centerTitle:true),body:Column(children:[adBox('مساحة إعلان علوية - لاحقاً'),Expanded(child:child),adBox('مساحة إعلان سفلية - لاحقاً')]));}

class Home extends StatelessWidget{ final Store store; const Home({super.key, required this.store}); @override Widget build(BuildContext c){ final p=store.profiles.firstWhere((e)=>e.id==store.activeProfile, orElse:()=>store.profiles.first); return PageFrame(title:'قاموسي المدرسي', child:ListView(padding:const EdgeInsets.all(16), children:[
  Card(child:Padding(padding:const EdgeInsets.all(18),child:Row(children:[const CircleAvatar(radius:28,child:Icon(Icons.school)),const SizedBox(width:12),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('أهلاً ${p.name}',style:Theme.of(c).textTheme.titleLarge),Text('النقاط: ${store.points.toStringAsFixed(1)} | الكلمات: ${store.words.length}')]))]))),
  GridView.count(crossAxisCount:2, shrinkWrap:true, physics:const NeverScrollableScrollPhysics(), mainAxisSpacing:12, crossAxisSpacing:12, childAspectRatio:1.15, children:[
    tile(c,'الصفوف',Icons.grid_view,()=>push(c,GradesPage(store))), tile(c,'القاموس',Icons.search,()=>push(c,DictionaryPage(store))), tile(c,'البطاقات',Icons.style,()=>push(c,FlashPage(store))), tile(c,'الاختبار',Icons.quiz,()=>push(c,QuizSetupPage(store))), tile(c,'الكلمات الصعبة',Icons.warning_amber,()=>push(c,DifficultPage(store))), tile(c,'الإحصائيات',Icons.bar_chart,()=>push(c,StatsPage(store))), tile(c,'الملف الشخصي',Icons.person,()=>push(c,ProfilesPage(store))), tile(c,'الإعدادات والتواصل',Icons.settings,()=>push(c,SettingsPage(store))),
  ])]));}
  Widget tile(BuildContext c,String t,IconData i,VoidCallback onTap)=>Card(child:InkWell(borderRadius:BorderRadius.circular(24),onTap:(){store.click();onTap();},child:Column(mainAxisAlignment:MainAxisAlignment.center,children:[Icon(i,size:38,color:Theme.of(c).colorScheme.primary),const SizedBox(height:10),Text(t,style:const TextStyle(fontWeight:FontWeight.bold))])));
}
void push(BuildContext c, Widget p)=>Navigator.push(c,MaterialPageRoute(builder:(_)=>p));
const gradesList=['KG','1','2','3','4','5','6','7','8'];
String gradeName(String g)=> g=='KG'?'الروضة':'الصف $g';

class GradesPage extends StatelessWidget{ final Store store; const GradesPage(this.store,{super.key}); @override Widget build(BuildContext c)=>PageFrame(title:'الصفوف', child:ListView.builder(padding:const EdgeInsets.all(16), itemCount:gradesList.length, itemBuilder:(_,i){ final g=gradesList[i]; final done=store.masteredGrade(g); return Card(child:ListTile(title:Text(gradeName(g),style:const TextStyle(fontWeight:FontWeight.bold)), subtitle:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('$done / ${store.byGrade(g).length} كلمة متقنة'),LinearProgressIndicator(value:store.byGrade(g).isEmpty?0:done/store.byGrade(g).length),Text(done>=100?'🏆 وسام الصف': done>=75?'⭐⭐⭐': done>=50?'⭐⭐': done>=25?'⭐':'ابدأ التعلم')]), trailing:const Icon(Icons.arrow_forward_ios), onTap:()=>push(c,GradeWordsPage(store,g)))); }));}
class GradeWordsPage extends StatelessWidget{ final Store store; final String grade; const GradeWordsPage(this.store,this.grade,{super.key}); @override Widget build(BuildContext c){ final list=store.byGrade(grade); return PageFrame(title:gradeName(grade), child:ListView.builder(padding:const EdgeInsets.all(16), itemCount:list.length, itemBuilder:(_,i){ final w=list[i]; return Card(child:ListTile(title:Text(w.en, textDirection:TextDirection.ltr, style:const TextStyle(fontWeight:FontWeight.bold,fontSize:20)), subtitle:Text('الصعوبة: ${w.difficultyText()}'), trailing:IconButton(icon:const Icon(Icons.volume_up), onPressed:()=>store.speak(w.en)), onTap:()=>push(c,WordCardPage(store,w)))); }));}}
class WordCardPage extends StatefulWidget{ final Store store; final WordItem word; const WordCardPage(this.store,this.word,{super.key}); @override State<WordCardPage> createState()=>_WordCardPageState();}
class _WordCardPageState extends State<WordCardPage>{ bool show=false; @override Widget build(BuildContext c)=>PageFrame(title:'بطاقة كلمة', child:Center(child:Card(margin:const EdgeInsets.all(20),child:Padding(padding:const EdgeInsets.all(24),child:Column(mainAxisSize:MainAxisSize.min,children:[InkWell(onTap:()=>widget.store.speak(widget.word.en),child:Text(widget.word.en,textDirection:TextDirection.ltr,style:const TextStyle(fontSize:36,fontWeight:FontWeight.bold))),const SizedBox(height:18),ElevatedButton.icon(onPressed:(){widget.store.click();setState(()=>show=!show);},icon:const Icon(Icons.translate),label:Text(show?'إخفاء المعنى':'إظهار المعنى')),if(show) Padding(padding:const EdgeInsets.all(18),child:Text(widget.word.ar,style:const TextStyle(fontSize:26,fontWeight:FontWeight.bold))),Text('الصف: ${gradeName(widget.word.grade)} | ${widget.word.difficultyText()}')])))));}

class DictionaryPage extends StatefulWidget{ final Store store; const DictionaryPage(this.store,{super.key}); @override State<DictionaryPage> createState()=>_DictionaryPageState();}
class _DictionaryPageState extends State<DictionaryPage>{ String q=''; @override Widget build(BuildContext c){ final list=widget.store.words.where((w)=>w.en.toLowerCase().contains(q.toLowerCase())||w.ar.contains(q)).take(80).toList(); return PageFrame(title:'القاموس', child:Column(children:[Padding(padding:const EdgeInsets.all(12),child:TextField(decoration:const InputDecoration(prefixIcon:Icon(Icons.search),hintText:'ابحث عن كلمة...',border:OutlineInputBorder()),onChanged:(v)=>setState(()=>q=v))),Expanded(child:ListView.builder(itemCount:list.length,itemBuilder:(_,i){final w=list[i]; return WordSearchTile(store:widget.store, word:w);})),FloatingActionButton.extended(onPressed:()=>push(c,AddWordPage(widget.store)), icon:const Icon(Icons.add), label:const Text('إضافة كلمة'))]));}}
class WordSearchTile extends StatefulWidget{ final Store store; final WordItem word; const WordSearchTile({super.key, required this.store, required this.word}); @override State<WordSearchTile> createState()=>_WordSearchTileState();}
class _WordSearchTileState extends State<WordSearchTile>{ bool show=false; @override Widget build(BuildContext c)=>Card(margin:const EdgeInsets.symmetric(horizontal:12,vertical:6),child:Padding(padding:const EdgeInsets.all(12),child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[InkWell(onTap:()=>widget.store.speak(widget.word.en),child:Text(widget.word.en,textDirection:TextDirection.ltr,style:const TextStyle(fontSize:22,fontWeight:FontWeight.bold))),const SizedBox(height:8),ElevatedButton(onPressed:(){widget.store.click();setState(()=>show=!show);},child:Text(show?'إخفاء المعنى':'إظهار المعنى')),if(show) Text(widget.word.ar,style:const TextStyle(fontSize:20,fontWeight:FontWeight.bold),textAlign:TextAlign.center)])));}
class AddWordPage extends StatefulWidget{ final Store store; const AddWordPage(this.store,{super.key}); @override State<AddWordPage> createState()=>_AddWordPageState();}
class _AddWordPageState extends State<AddWordPage>{ final en=TextEditingController(), ar=TextEditingController(); String grade='KG'; @override Widget build(BuildContext c)=>PageFrame(title:'إضافة كلمة', child:ListView(padding:const EdgeInsets.all(18),children:[DropdownButtonFormField(initialValue:grade,items:gradesList.map((g)=>DropdownMenuItem(value:g,child:Text(gradeName(g)))).toList(),onChanged:(v)=>setState(()=>grade=v!)),TextField(controller:en, decoration:const InputDecoration(labelText:'English word')),TextField(controller:ar, decoration:const InputDecoration(labelText:'المعنى العربي')),const SizedBox(height:20),ElevatedButton(onPressed:()async{if(en.text.trim().isEmpty||ar.text.trim().isEmpty)return; await widget.store.addWord(en.text, ar.text, grade); if(c.mounted)Navigator.pop(c);},child:const Text('حفظ'))]));}

class FlashPage extends StatelessWidget{ final Store store; const FlashPage(this.store,{super.key}); @override Widget build(BuildContext c)=>PageFrame(title:'البطاقات التعليمية', child:ListView(padding:const EdgeInsets.all(16),children:gradesList.map((g)=>Card(child:ListTile(title:Text(gradeName(g)),subtitle:Text('${store.byGrade(g).length} كلمة'),trailing:const Icon(Icons.style),onTap:()=>push(c,FlashRunPage(store,g))))).toList()));}
class FlashRunPage extends StatefulWidget{ final Store store; final String grade; const FlashRunPage(this.store,this.grade,{super.key}); @override State<FlashRunPage> createState()=>_FlashRunPageState();}
class _FlashRunPageState extends State<FlashRunPage>{ int index=0; bool show=false; @override Widget build(BuildContext c){ final list=widget.store.byGrade(widget.grade); final w=list[index%list.length]; return PageFrame(title:'بطاقات ${gradeName(widget.grade)}', child:Center(child:Card(margin:const EdgeInsets.all(20),child:Padding(padding:const EdgeInsets.all(24),child:Column(mainAxisSize:MainAxisSize.min,children:[Text('${index+1} / ${list.length}'),const SizedBox(height:12),InkWell(onTap:()=>widget.store.speak(w.en),child:Text(w.en,textDirection:TextDirection.ltr,style:const TextStyle(fontSize:36,fontWeight:FontWeight.bold))),const SizedBox(height:18),ElevatedButton(onPressed:()=>setState(()=>show=!show),child:Text(show?'إخفاء المعنى':'إظهار المعنى')),if(show)Padding(padding:const EdgeInsets.all(12),child:Text(w.ar,style:const TextStyle(fontSize:25,fontWeight:FontWeight.bold))),ElevatedButton.icon(onPressed:()=>setState((){index=(index+1)%list.length; show=false;}),icon:const Icon(Icons.navigate_next),label:const Text('التالي'))])))));}}

class QuizSetupPage extends StatelessWidget{ final Store store; const QuizSetupPage(this.store,{super.key}); @override Widget build(BuildContext c)=>PageFrame(title:'الاختبار', child:ListView(padding:const EdgeInsets.all(16),children:[const Text('اختر الصف ونوع الاختبار',style:TextStyle(fontSize:20,fontWeight:FontWeight.bold)),...gradesList.map((g)=>Card(child:Column(children:[ListTile(title:Text(gradeName(g)),subtitle:const Text('English → Arabic'),trailing:const Icon(Icons.play_arrow),onTap:()=>push(c,QuizPage(store,g,true))),ListTile(title:Text(gradeName(g)),subtitle:const Text('Arabic → English'),trailing:const Icon(Icons.play_arrow),onTap:()=>push(c,QuizPage(store,g,false)))])))]));}
class QuizPage extends StatefulWidget{ final Store store; final String grade; final bool enToAr; const QuizPage(this.store,this.grade,this.enToAr,{super.key}); @override State<QuizPage> createState()=>_QuizPageState();}
class _QuizPageState extends State<QuizPage>{ late List<WordItem> qs; int idx=0, ok=0, bad=0; final rand=Random(); @override void initState(){super.initState(); qs=[...widget.store.byGrade(widget.grade)]..shuffle(); qs=qs.take(20).toList();}
@override Widget build(BuildContext c){ if(idx>=qs.length) return ResultPage(store:widget.store,total:qs.length,ok:ok,bad:bad); final w=qs[idx]; final all=widget.store.words; final opts=<String>{widget.enToAr?w.ar:w.en}; while(opts.length<4){ final x=all[rand.nextInt(all.length)]; opts.add(widget.enToAr?x.ar:x.en); } final list=opts.toList()..shuffle(); return PageFrame(title:'اختبار ${gradeName(widget.grade)}', child:ListView(padding:const EdgeInsets.all(18),children:[Text('السؤال ${idx+1} / ${qs.length}',style:const TextStyle(fontWeight:FontWeight.bold)),const SizedBox(height:20),Card(child:Padding(padding:const EdgeInsets.all(24),child:Column(children:[Text(widget.enToAr?w.en:w.ar,textDirection:widget.enToAr?TextDirection.ltr:TextDirection.rtl,style:const TextStyle(fontSize:30,fontWeight:FontWeight.bold)),if(widget.enToAr) IconButton(icon:const Icon(Icons.volume_up),onPressed:()=>widget.store.speak(w.en))]))),...list.map((o)=>Card(child:ListTile(title:Text(o,textDirection:widget.enToAr?TextDirection.rtl:TextDirection.ltr),onTap:()async{ final correct=o==(widget.enToAr?w.ar:w.en); await widget.store.answer(w, correct); setState((){ if(correct) ok++; else bad++; idx++; });}))) ]));}}
class ResultPage extends StatelessWidget{ final Store store; final int total,ok,bad; const ResultPage({super.key,required this.store,required this.total,required this.ok,required this.bad}); @override Widget build(BuildContext c)=>PageFrame(title:'نتيجة الاختبار', child:Center(child:Card(margin:const EdgeInsets.all(20),child:Padding(padding:const EdgeInsets.all(24),child:Column(mainAxisSize:MainAxisSize.min,children:[const Icon(Icons.emoji_events,size:60,color:Colors.amber),Text('عدد الأسئلة: $total'),Text('الصحيح: $ok'),Text('الخطأ: $bad'),Text('النقاط المكتسبة: ${(ok*.5).toStringAsFixed(1)}'),Text('نسبة النجاح: ${total==0?0:((ok/total)*100).round()}%'),ElevatedButton(onPressed:()=>Navigator.pop(c),child:const Text('العودة'))])))));}

class DifficultPage extends StatelessWidget{ final Store store; const DifficultPage(this.store,{super.key}); @override Widget build(BuildContext c){ final list=store.words.where((w)=>store.difficult.contains('${w.id}')).toList(); return PageFrame(title:'الكلمات الصعبة', child:list.isEmpty?const Center(child:Text('لا توجد كلمات صعبة بعد')):ListView(children:list.map((w)=>WordSearchTile(store:store,word:w)).toList()));}}
class StatsPage extends StatelessWidget{ final Store store; const StatsPage(this.store,{super.key}); @override Widget build(BuildContext c)=>PageFrame(title:'الإحصائيات', child:ListView(padding:const EdgeInsets.all(16),children:[Card(child:ListTile(title:const Text('النقاط'),trailing:Text(store.points.toStringAsFixed(1)))),Card(child:ListTile(title:const Text('الكلمات الصعبة'),trailing:Text('${store.difficult.length}'))),...gradesList.map((g){final total=store.byGrade(g).length; final done=store.masteredGrade(g); return Card(child:ListTile(title:Text(gradeName(g)),subtitle:LinearProgressIndicator(value:total==0?0:done/total),trailing:Text('$done/$total')));})]));}
class ProfilesPage extends StatelessWidget{ final Store store; const ProfilesPage(this.store,{super.key}); @override Widget build(BuildContext c)=>PageFrame(title:'الملفات الشخصية', child:ListView(padding:const EdgeInsets.all(16),children:[...store.profiles.map((p)=>Card(child:ListTile(leading:Icon(p.id==store.activeProfile?Icons.check_circle:Icons.person),title:Text(p.name),onTap:()=>store.setActive(p.id)))),if(store.profiles.length<3)ElevatedButton.icon(onPressed:()async{final id=store.profiles.length+1; store.profiles.add(Profile(id,'الطالب $id')); await store.saveProfiles();},icon:const Icon(Icons.add),label:const Text('إضافة ملف'))]));}
class SettingsPage extends StatelessWidget{ final Store store; const SettingsPage(this.store,{super.key}); @override Widget build(BuildContext c)=>PageFrame(title:'الإعدادات والتواصل', child:ListView(padding:const EdgeInsets.all(16),children:[SwitchListTile(title:const Text('أصوات الضغط والتفاعل'),value:store.sound,onChanged:(v)async{await store.setSound(v);}),Card(child:ListTile(leading:const Icon(Icons.update),title:const Text('تحديث القاموس من GitHub JSON'),subtitle:const Text('الاستيراد المحلي من Excel/PDF يكون بتحويله إلى JSON ثم رفعه على GitHub'),onTap:()async{try{final m=await store.updateFromUrl(); if(c.mounted)msg(c,m);}catch(e){if(c.mounted)msg(c,'فشل التحديث. غيّر رابط JSON داخل main.dart لاحقاً.');}})),Card(child:ListTile(leading:const Icon(Icons.email),title:const Text('إرسال بريد للمطور'),onTap:()=>launchUrl(Uri.parse('mailto:$developerEmail?subject=قاموسي المدرسي')))),Card(child:ListTile(leading:const Icon(Icons.report),title:const Text('اقتراح كلمة / الإبلاغ عن خطأ'),onTap:()=>launchUrl(Uri.parse('mailto:$developerEmail?subject=اقتراح أو تصحيح في قاموسي المدرسي')))),const Padding(padding:EdgeInsets.all(12),child:Text('الإصدار 1.0.0 - بدون إشعارات - أماكن الإعلانات جاهزة وغير مفعلة'))]));}
void msg(BuildContext c,String m)=>ScaffoldMessenger.of(c).showSnackBar(SnackBar(content:Text(m)));
