# طريقة تحديث محتوى قاموسي المدرسي

## 1) ملف المحتوى
التطبيق يقرأ الكلمات من ملف JSON ثابت اسمه غالباً:

`words.json`

الصيغة المطلوبة:

```json
{
  "version": 1,
  "words": [
    {
      "id": 1,
      "grade": "KG",
      "word_en": "Apple",
      "meaning_ar": "تفاحة",
      "source": "Jordan Curriculum"
    }
  ]
}
```

## 2) أسماء الصفوف المعتمدة
- الروضة: `KG`
- الصف الأول: `1`
- الصف الثاني: `2`
- الصف الثالث: `3`
- الصف الرابع: `4`
- الصف الخامس: `5`
- الصف السادس: `6`
- الصف السابع: `7`
- الصف الثامن: `8`

## 3) أين أرفع الملف؟
أنشئ مستودع GitHub للمحتوى، مثلاً:

`qamoosi-school-content`

ثم ارفع داخله ملف:

`words.json`

بعدها خذ رابط Raw، ويكون تقريباً بهذا الشكل:

`https://raw.githubusercontent.com/USERNAME/qamoosi-school-content/main/words.json`

## 4) أين أضع الرابط داخل التطبيق؟
افتح الملف:

`lib/main.dart`

وغيّر السطر:

```dart
const String dictionaryJsonUrl = 'https://raw.githubusercontent.com/YOUR_USER/qamoosi-school-content/main/words.json';
```

إلى رابطك الحقيقي.

## 5) كيف يحدث المستخدم القاموس؟
داخل التطبيق:

الإعدادات والتواصل → تحديث القاموس من GitHub JSON

إذا نجح التحديث تظهر رسالة بعدد الكلمات.

## 6) كيف نحدث من Excel أو PDF؟
أرسل ملف Excel أو PDF هنا، وسأحوله لك إلى `words.json` بنفس الصيغة الصحيحة، ثم ترفعه على GitHub.
