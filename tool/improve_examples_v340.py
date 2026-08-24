import json
from pathlib import Path

PATH = Path('assets/data/words.json')
BAD_PREFIXES = (
    'we used the word "',
    'we learned the word "',
)

# Hand-tuned high-frequency examples students are especially likely to see first.
SPECIAL = {
    'board': ('The teacher writes on the board.', 'يكتب المعلم على اللوح.'),
    'apple': ('I eat an apple at break time.', 'آكل تفاحة في وقت الاستراحة.'),
    'banana': ('The banana is yellow.', 'الموزة صفراء.'),
    'orange': ('I have an orange in my lunchbox.', 'لدي برتقالة في صندوق الغداء.'),
    'cat': ('The cat is sleeping on the chair.', 'القطة نائمة على الكرسي.'),
    'dog': ('The dog runs in the garden.', 'يركض الكلب في الحديقة.'),
    'bird': ('The bird is flying in the sky.', 'يطير الطائر في السماء.'),
    'fish': ('The fish swims in the water.', 'تسبح السمكة في الماء.'),
    'sun': ('The sun is bright today.', 'الشمس ساطعة اليوم.'),
    'moon': ('We can see the moon at night.', 'يمكننا رؤية القمر ليلًا.'),
    'water': ('Please drink some water.', 'من فضلك اشرب بعض الماء.'),
    'rainbow': ('A rainbow has many colors.', 'لقوس قزح ألوان كثيرة.'),
    'playground': ('We play in the playground after class.', 'نلعب في ساحة اللعب بعد الحصة.'),
    'lunchbox': ('My lunchbox is in my school bag.', 'صندوق غدائي في حقيبتي المدرسية.'),
    'pencilcase': ('My pencils are in the pencil case.', 'أقلامي في المقلمة.'),
    'notebook': ('I write my homework in my notebook.', 'أكتب واجبي في دفتري.'),
    'crayon': ('She colors the sun with a yellow crayon.', 'تلوّن الشمس بقلم تلوين أصفر.'),
    'eraser': ('Use an eraser to fix the mistake.', 'استخدم ممحاة لتصحيح الخطأ.'),
    'ruler': ('I use a ruler to draw a straight line.', 'أستخدم مسطرة لرسم خط مستقيم.'),
    'picture': ('Look at the picture and answer the question.', 'انظر إلى الصورة وأجب عن السؤال.'),
    'story': ('Our teacher reads us a short story.', 'يقرأ لنا معلمنا قصة قصيرة.'),
    'garden': ('There are flowers in the garden.', 'توجد أزهار في الحديقة.'),
    'flower': ('This flower smells nice.', 'رائحة هذه الزهرة جميلة.'),
    'tree': ('The bird is sitting in the tree.', 'الطائر جالس على الشجرة.'),
    'leaf': ('A green leaf fell from the tree.', 'سقطت ورقة خضراء من الشجرة.'),
    'rabbit': ('The rabbit has long ears.', 'للأرنب أذنان طويلتان.'),
    'turtle': ('The turtle moves slowly.', 'تتحرك السلحفاة ببطء.'),
    'lion': ('The lion is a strong animal.', 'الأسد حيوان قوي.'),
    'zebra': ('The zebra has black and white stripes.', 'للحمار الوحشي خطوط سوداء وبيضاء.'),
    'giraffe': ('The giraffe has a long neck.', 'للزرافة رقبة طويلة.'),
    'breakfast': ('I eat breakfast before school.', 'أتناول الفطور قبل المدرسة.'),
    'cheese': ('I put cheese in my sandwich.', 'أضع الجبن في شطيرتي.'),
    'juice': ('She drinks orange juice with breakfast.', 'تشرب عصير البرتقال مع الفطور.'),
    'soup': ('The soup is hot.', 'الحساء ساخن.'),
    'bedroom': ('My bed is in the bedroom.', 'سريري في غرفة النوم.'),
    'kitchen': ('My father is cooking in the kitchen.', 'والدي يطبخ في المطبخ.'),
    'bathroom': ('Wash your hands in the bathroom.', 'اغسل يديك في الحمام.'),
    'family': ('My family eats dinner together.', 'تتناول عائلتي العشاء معًا.'),
    'sister': ('My sister helps me with my homework.', 'تساعدني أختي في واجبي.'),
    'brother': ('My brother plays football after school.', 'يلعب أخي كرة القدم بعد المدرسة.'),
    'morning': ('I go to school in the morning.', 'أذهب إلى المدرسة في الصباح.'),
    'evening': ('We read together in the evening.', 'نقرأ معًا في المساء.'),
    'today': ('We have English class today.', 'لدينا حصة إنجليزي اليوم.'),
    'tomorrow': ('We will visit the library tomorrow.', 'سنزور المكتبة غدًا.'),
    'weather': ('The weather is sunny today.', 'الطقس مشمس اليوم.'),
    'cloud': ('A dark cloud is above the school.', 'توجد سحابة داكنة فوق المدرسة.'),
    'storm': ('The storm brought heavy rain.', 'جلبت العاصفة أمطارًا غزيرة.'),
    'wind': ('The wind is moving the leaves.', 'تحرك الرياح أوراق الشجر.'),
    'spring': ('Flowers grow in spring.', 'تنمو الأزهار في الربيع.'),
    'summer': ('We go swimming in summer.', 'نذهب للسباحة في الصيف.'),
    'winter': ('I wear a warm coat in winter.', 'أرتدي معطفًا دافئًا في الشتاء.'),
    'library': ('I borrow books from the library.', 'أستعير الكتب من المكتبة.'),
    'hospital': ('The doctor works at the hospital.', 'يعمل الطبيب في المستشفى.'),
    'market': ('We buy fruit at the market.', 'نشتري الفاكهة من السوق.'),
    'doctor': ('The doctor helps sick people.', 'يساعد الطبيب المرضى.'),
    'nurse': ('The nurse checks the patient.', 'تفحص الممرضة المريض.'),
    'homework': ('I finish my homework before dinner.', 'أنهي واجبي قبل العشاء.'),
    'question': ('Raise your hand if you have a question.', 'ارفع يدك إذا كان لديك سؤال.'),
    'answer': ('Write your answer on the line.', 'اكتب إجابتك على السطر.'),
    'technology': ('Technology helps us find information quickly.', 'تساعدنا التكنولوجيا في العثور على المعلومات بسرعة.'),
    'internet': ('We use the internet to research our project.', 'نستخدم الإنترنت للبحث في مشروعنا.'),
    'computer': ('I use a computer to write my report.', 'أستخدم الحاسوب لكتابة تقريري.'),
    'environment': ('We must protect the environment.', 'يجب أن نحمي البيئة.'),
    'pollution': ('Air pollution can harm our health.', 'يمكن أن يضر تلوث الهواء بصحتنا.'),
    'recycling': ('Recycling reduces the amount of waste.', 'تقلل إعادة التدوير كمية النفايات.'),
    'climate': ('Climate affects plants, animals, and people.', 'يؤثر المناخ في النباتات والحيوانات والناس.'),
    'energy': ('Solar panels turn sunlight into energy.', 'تحول الألواح الشمسية ضوء الشمس إلى طاقة.'),
    'science': ('Science helps us understand the natural world.', 'تساعدنا العلوم على فهم العالم الطبيعي.'),
    'research': ('Good research begins with a clear question.', 'يبدأ البحث الجيد بسؤال واضح.'),
    'evidence': ('Use evidence to support your conclusion.', 'استخدم الدليل لدعم استنتاجك.'),
    'analysis': ('The analysis shows a clear change in the results.', 'يُظهر التحليل تغيرًا واضحًا في النتائج.'),
    'hypothesis': ('The experiment tested our hypothesis.', 'اختبرت التجربة فرضيتنا.'),
    'algorithm': ('The algorithm sorts the data into useful groups.', 'ترتب الخوارزمية البيانات في مجموعات مفيدة.'),
    'database': ('The school stores the records in a secure database.', 'تخزن المدرسة السجلات في قاعدة بيانات آمنة.'),
    'privacy': ('Strong passwords help protect online privacy.', 'تساعد كلمات المرور القوية في حماية الخصوصية على الإنترنت.'),
    'security': ('The website uses extra security to protect users.', 'يستخدم الموقع إجراءات أمان إضافية لحماية المستخدمين.'),
    'artificial': ('The robot uses artificial intelligence to recognize objects.', 'يستخدم الروبوت الذكاء الاصطناعي للتعرف على الأشياء.'),
    'intelligence': ('Artificial intelligence can identify patterns in data.', 'يمكن للذكاء الاصطناعي تحديد الأنماط في البيانات.'),
    'sustainability': ('Sustainability means using resources responsibly.', 'تعني الاستدامة استخدام الموارد بمسؤولية.'),
    'biodiversity': ('Biodiversity helps ecosystems stay healthy.', 'يساعد التنوع الحيوي الأنظمة البيئية على البقاء سليمة.'),
    'globalization': ('Globalization connects economies and cultures around the world.', 'تربط العولمة الاقتصادات والثقافات حول العالم.'),
    'inflation': ('Inflation can increase the prices of everyday goods.', 'يمكن أن يؤدي التضخم إلى ارتفاع أسعار السلع اليومية.'),
    'investment': ('The company made an investment in clean energy.', 'قامت الشركة باستثمار في الطاقة النظيفة.'),
    'leadership': ('Good leadership helps a team reach its goals.', 'تساعد القيادة الجيدة الفريق على تحقيق أهدافه.'),
    'integrity': ('Integrity means doing the right thing even when no one is watching.', 'تعني النزاهة فعل الصواب حتى عندما لا يراقبك أحد.'),
    'accountability': ('Accountability requires people to take responsibility for their decisions.', 'تتطلب المساءلة أن يتحمل الناس مسؤولية قراراتهم.'),
}

VERBS = set('''laugh clap draw paint count spell open close carry share help listen speak learn remember visit travel build wash cook plant grow collect choose finish begin follow cross wait invite enjoy practice repeat compare measure discover explore protect create imagine explain describe decide prepare improve return arrive borrow lend promise celebrate recycle save waste respect organize design invent communicate develop reduce reuse repair observe record predict connect separate include support provide increase decrease change continue manage plan solve recommend suggest review focus memorize translate pronounce recognize identify select complete achieve avoid prevent respond consider prefer analyze evaluate calculate estimate investigate demonstrate represent summarize participate cooperate encourage influence require contain depend produce consume conserve interpret contrast conclude justify persuade inform mention indicate determine establish maintain adapt contribute interact collaborate prioritize reflect optimize generate process detect classify personalize monitor simulate visualize verify update access assess examine define illustrate cite reference present discuss argue question formulate synthesize propose implement modify validate document negotiate resolve critique infer articulate anticipate facilitate coordinate allocate regulate advocate mitigate differentiate integrate substantiate'''.split())

ADJECTIVES = set('''clean dirty strong kind funny quiet loud healthy hungry thirsty tired excited afraid careful quick slow early late important different similar possible special friendly brave honest useful responsible creative successful dangerous natural modern ancient local international popular confident patient independent active environmental sustainable renewable global regional urban rural reliable accurate effective efficient complex available essential significant artificial virtual critical flexible innovative logical academic economic social cultural political scientific ethical legal professional technical relevant appropriate specific general potential primary secondary objective subjective consistent precise abstract strategic controversial comprehensive fundamental alternative contemporary emerging sophisticated credible'''.split())


def is_bad(text):
    t = (text or '').strip().lower()
    return not t or any(t.startswith(p) for p in BAD_PREFIXES)


def adaptive_example(word, meaning, grade):
    w = word.strip().lower()
    if w in SPECIAL:
        return SPECIAL[w]
    g = int(grade) if str(grade).isdigit() else 6
    if w in VERBS:
        if g <= 3:
            return (f'The student can {w} during the activity.', f'يمكن أن {meaning} الطالب أثناء النشاط.')
        if g <= 6:
            return (f'Students need to {w} carefully during this task.', f'يجب أن {meaning} الطلاب بعناية أثناء هذه المهمة.')
        return (f'Students should {w} the situation carefully before making a decision.', f'ينبغي أن {meaning} الطلاب الموقف بعناية قبل اتخاذ قرار.')
    if w in ADJECTIVES:
        if g <= 3:
            return (f'The teacher says this example is {w}.', f'يقول المعلم إن هذا المثال {meaning}.')
        if g <= 6:
            return (f'The class described the example as {w}.', f'وصف الصف المثال بأنه {meaning}.')
        return (f'The evidence suggests that this factor is {w} to the discussion.', f'تشير الأدلة إلى أن هذا العامل {meaning} بالنسبة إلى النقاش.')
    if g <= 2:
        return (f'We learned about {w} in class today.', f'تعلمنا عن {meaning} في الصف اليوم.')
    if g <= 4:
        return (f'Our lesson includes an activity about {w}.', f'يتضمن درسنا نشاطًا عن {meaning}.')
    if g <= 6:
        return (f'Students discussed {w} and gave examples from daily life.', f'ناقش الطلاب {meaning} وقدموا أمثلة من الحياة اليومية.')
    if g <= 9:
        return (f'The class discussed how {w} affects people and society.', f'ناقش الصف كيف يؤثر {meaning} في الناس والمجتمع.')
    return (f'The report examines the role of {w} in a wider academic context.', f'يدرس التقرير دور {meaning} ضمن سياق أكاديمي أوسع.')


data = json.loads(PATH.read_text(encoding='utf-8'))
changed = 0
for item in data.get('words', []):
    en = str(item.get('example_en', '') or '')
    ar = str(item.get('example_ar', '') or '')
    if is_bad(en) or 'استخدمنا كلمة «' in ar or 'تعلمنا كلمة «' in ar:
        new_en, new_ar = adaptive_example(str(item.get('word_en', '')), str(item.get('meaning_ar', '')), str(item.get('grade', '6')))
        item['example_en'] = new_en
        item['example_ar'] = new_ar
        changed += 1

data['version'] = max(int(data.get('version', 0) or 0), 5)
data['examples_revision'] = 'v3.4 grade-adaptive contextual examples'
PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Improved {changed} generated/empty examples')
