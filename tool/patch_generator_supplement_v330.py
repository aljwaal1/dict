from pathlib import Path

p = Path('tool/generate_global_ai_words_v330.py')
s = p.read_text(encoding='utf-8')
marker = '\n\ndef make_examples(word, meaning, grade):'
if marker not in s:
    raise SystemExit('generator marker not found')

# Shared international student vocabulary bank. The same useful word may be
# appropriate in more than one grade; uniqueness is enforced inside each grade.
supplement = [
('apron','مئزر'),('basket','سلة'),('blanket','بطانية'),('bottle','زجاجة'),('button','زر'),('candle','شمعة'),('carpet','سجادة'),('ceiling','سقف'),('circle','دائرة'),('corner','زاوية'),
('cupboard','خزانة'),('curtain','ستارة'),('cushion','وسادة'),('drawer','درج'),('envelope','مغلف'),('feather','ريشة'),('fence','سياج'),('finger','إصبع'),('glove','قفاز'),('helmet','خوذة'),
('island','جزيرة'),('jacket','سترة'),('kettle','غلاية'),('ladder','سلم'),('mirror','مرآة'),('napkin','منديل'),('pillow','وسادة نوم'),('pocket','جيب'),('rectangle','مستطيل'),('roof','سطح المنزل'),
('scarf','وشاح'),('shelf','رف'),('suitcase','حقيبة سفر'),('triangle','مثلث'),('umbrella','مظلة'),('wallet','محفظة'),('whistle','صافرة'),('window','نافذة'),('wool','صوف'),('zipper','سحاب'),
('airport','مطار'),('aquarium','حوض أسماك'),('beach','شاطئ'),('campsite','مخيم'),('cave','كهف'),('factory','مصنع'),('harbor','ميناء'),('hotel','فندق'),('lake','بحيرة'),('palace','قصر'),
('pharmacy','صيدلية'),('restaurant','مطعم'),('stadium','ملعب'),('theater','مسرح'),('university','جامعة'),('valley','وادي'),('waterfall','شلال'),('workshop','ورشة'),('zoo','حديقة حيوان'),('avenue','شارع واسع'),
('ability','قدرة'),('activity','نشاط'),('attention','انتباه'),('balance','توازن'),('benefit','فائدة'),('courage','شجاعة'),('curiosity','فضول'),('effort','جهد'),('emotion','عاطفة'),('friendship','صداقة'),
('habit','عادة'),('idea','فكرة'),('memory','ذاكرة'),('patience','صبر'),('purpose','غرض'),('success','نجاح'),('talent','موهبة'),('value','قيمة'),('wonder','دهشة'),('wisdom','حكمة'),
('accept','يقبل'),('agree','يوافق'),('believe','يعتقد'),('belong','ينتمي'),('care','يهتم'),('deliver','يوصل'),('enter','يدخل'),('gather','يجمع'),('notice','يلاحظ'),('offer','يعرض'),
('order','يرتب'),('receive','يستلم'),('search','يبحث'),('send','يرسل'),('solve','يحل'),('teach','يدرّس'),('understand','يفهم'),('use','يستخدم'),('wonder','يتساءل'),('write','يكتب'),
('bright','مشرق'),('comfortable','مريح'),('curious','فضولي'),('gentle','لطيف'),('helpful','متعاون'),('polite','مهذب'),('proud','فخور'),('safe','آمن'),('simple','بسيط'),('wise','حكيم'),
('achievement','إنجاز'),('awareness','وعي'),('capacity','قدرة استيعابية'),('commitment','التزام'),('development','تطوير'),('discovery','اكتشاف'),('discussion','مناقشة'),('improvement','تحسين'),('motivation','دافعية'),('participation','مشاركة'),
('preparation','تحضير'),('presentation','عرض تقديمي'),('procedure','إجراء'),('reflection','تأمل'),('requirement','متطلب'),('response','استجابة'),('technique','تقنية'),('understanding','فهم'),('connection','ارتباط'),('communication','تواصل')
]

insert = "\n\n# Extra bank guarantees at least 50 NEW entries after removing words already present.\nfor _grade in grades:\n    grades[_grade].extend(supplement)\n"
s = s.replace(marker, insert + marker, 1)
p.write_text(s, encoding='utf-8')
print('Expanded global vocabulary candidates for all 12 grades')
