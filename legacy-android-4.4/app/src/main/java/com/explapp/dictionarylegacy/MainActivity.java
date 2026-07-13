package com.explapp.dictionarylegacy;

import android.app.Activity;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.content.Context;
import android.widget.*;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Locale;
import java.util.Random;

public class MainActivity extends Activity {
    private final int navy = Color.rgb(20, 43, 76);
    private final int blue = Color.rgb(38, 112, 196);
    private final int sky = Color.rgb(231, 242, 255);
    private final int ink = Color.rgb(31, 43, 58);
    private LinearLayout content;
    private TextView title, subtitle;
    private EditText search;
    private TextToSpeech tts;
    private String selectedGrade = "الكل";
    private int currentPage;
    private static final int PAGE_SIZE = 25;
    private final ArrayList<Word> words = new ArrayList<Word>();
    private final String[] gradeKeys = {"الكل", "KG", "1", "2", "3", "4", "5", "6", "7", "8"};
    private final String[] gradeLabels = {"الكل", "روضة", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس", "السابع", "الثامن"};

    private static class Word {
        String en, ar, grade, example;
        Word(String e, String a, String g, String x) { en=e; ar=a; grade=g; example=x; }
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        loadWords();
        tts = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
            @Override public void onInit(int status) {
                if (status == TextToSpeech.SUCCESS) tts.setLanguage(Locale.US);
            }
        });
        showDictionary();
    }

    private void base(String section, String hint) {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        root.setBackgroundColor(Color.rgb(248, 250, 253));

        LinearLayout head = new LinearLayout(this);
        head.setOrientation(LinearLayout.VERTICAL);
        head.setPadding(dp(20), dp(18), dp(20), dp(16));
        head.setBackgroundColor(navy);
        title = text("قاموسي المدرسي", 26, Color.WHITE, Typeface.BOLD);
        subtitle = text(section + "  •  " + hint, 14, Color.rgb(207, 225, 247), Typeface.NORMAL);
        head.addView(title);
        head.addView(subtitle, lp(-1, -2, 0, 5, 0, 0));
        root.addView(head);

        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(16), dp(14), dp(16), dp(10));
        ScrollView scroll = new ScrollView(this);
        scroll.addView(content);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));

        LinearLayout nav = new LinearLayout(this);
        nav.setGravity(Gravity.CENTER);
        nav.setPadding(dp(8), dp(8), dp(8), dp(8));
        nav.setBackgroundColor(Color.WHITE);
        nav.addView(navButton("القاموس", new View.OnClickListener(){ public void onClick(View v){ showDictionary(); }}), navLp());
        nav.addView(navButton("بطاقات", new View.OnClickListener(){ public void onClick(View v){ showCards(); }}), navLp());
        nav.addView(navButton("اختبار", new View.OnClickListener(){ public void onClick(View v){ showQuiz(); }}), navLp());
        root.addView(nav);
        setContentView(root);
    }

    private void showDictionary() {
        base("ابحث وتعلّم", "قاموس يعمل دون إنترنت");
        search = new EditText(this);
        search.setSingleLine(true);
        search.setHint("ابحث بالإنجليزية أو العربية");
        search.setTextSize(16);
        search.setTextColor(ink);
        search.setHintTextColor(Color.rgb(115, 130, 148));
        search.setBackground(round(Color.WHITE, 16));
        search.setPadding(dp(16), dp(10), dp(16), dp(10));
        content.addView(search, lp(-1, dp(54), 0, 0, 0, 10));
        search.addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence s, int a, int b, int c) {}
            public void onTextChanged(CharSequence s, int a, int b, int c) { currentPage=0; renderWords(s.toString()); }
            public void afterTextChanged(Editable e) {}
        });

        HorizontalScrollView gradesScroll = new HorizontalScrollView(this);
        LinearLayout gradeRow = new LinearLayout(this);
        gradeRow.setPadding(0, 0, 0, dp(8));
        for (int i=0; i<gradeKeys.length; i++) {
            final String grade = gradeKeys[i];
            Button b = smallButton(gradeLabels[i], grade.equals(selectedGrade));
            b.setOnClickListener(new View.OnClickListener() { public void onClick(View v) {
                selectedGrade = grade; currentPage=0; showDictionary();
            }});
            gradeRow.addView(b, lp(-2, dp(40), 0, 0, 0, 0));
        }
        gradesScroll.addView(gradeRow);
        content.addView(gradesScroll);
        renderWords("");
    }

    private void renderWords(String query) {
        while (content.getChildCount() > 2) content.removeViewAt(2);
        String q = query.trim().toLowerCase(Locale.US);
        ArrayList<Word> matches = new ArrayList<Word>();
        for (int i=0;i<words.size();i++) {
            Word w=words.get(i);
            if (!selectedGrade.equals("الكل") && !w.grade.equals(selectedGrade)) continue;
            if (q.length()>0 && w.en.toLowerCase(Locale.US).indexOf(q)<0 && w.ar.indexOf(query.trim())<0) continue;
            matches.add(w);
        }
        if (matches.size()==0) {
            TextView empty=text("لا توجد نتيجة. جرّب كلمة أخرى.", 17, ink, Typeface.NORMAL);
            empty.setGravity(Gravity.CENTER);
            content.addView(empty, lp(-1, dp(120), 0, 0, 0, 0));
            return;
        }
        int pages = (matches.size()+PAGE_SIZE-1)/PAGE_SIZE;
        if (currentPage>=pages) currentPage=pages-1;
        int start=currentPage*PAGE_SIZE, end=Math.min(matches.size(), start+PAGE_SIZE);
        TextView count=text("النتائج " + (start+1) + "–" + end + " من " + matches.size(), 13, Color.rgb(90,105,120), Typeface.BOLD);
        count.setGravity(Gravity.CENTER); content.addView(count, lp(-1,-2,0,0,4,0));
        for (int i=start;i<end;i++) content.addView(wordCard(matches.get(i)));
        if (pages>1) addPager(pages, query);
    }

    private void addPager(final int pages, final String query) {
        LinearLayout row=new LinearLayout(this); row.setGravity(Gravity.CENTER);
        Button previous=smallButton("السابق", false); previous.setEnabled(currentPage>0);
        previous.setOnClickListener(new View.OnClickListener(){ public void onClick(View v){ currentPage--; renderWords(query); }});
        TextView page=text((currentPage+1)+" / "+pages, 15, navy, Typeface.BOLD); page.setGravity(Gravity.CENTER);
        Button next=smallButton("التالي", false); next.setEnabled(currentPage<pages-1);
        next.setOnClickListener(new View.OnClickListener(){ public void onClick(View v){ currentPage++; renderWords(query); }});
        row.addView(previous, new LinearLayout.LayoutParams(0,dp(44),1));
        row.addView(page, new LinearLayout.LayoutParams(0,dp(44),.7f));
        row.addView(next, new LinearLayout.LayoutParams(0,dp(44),1));
        content.addView(row, lp(-1,-2,0,0,8,0));
    }

    private View wordCard(final Word w) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16), dp(13), dp(16), dp(13));
        card.setBackgroundColor(Color.WHITE);
        TextView en=text(w.en, 23, navy, Typeface.BOLD);
        TextView ar=text(w.ar + "   •   " + gradeName(w.grade), 17, blue, Typeface.BOLD);
        TextView ex=text(w.example, 14, Color.rgb(95,108,123), Typeface.NORMAL);
        card.addView(en);
        card.addView(ar, lp(-1,-2,0,0,4,0));
        card.addView(ex, lp(-1,-2,0,0,6,0));
        Button speak=smallButton("استمع للنطق", false);
        speak.setOnClickListener(new View.OnClickListener(){ public void onClick(View v){ say(w.en); }});
        card.addView(speak, lp(-2, dp(38), 0, 0, 9, 0));
        return cardWithMargin(card);
    }

    private void showCards() {
        base("بطاقات المراجعة", "اضغط للإجابة ثم استمع للنطق");
        final SharedPreferences prefs=getSharedPreferences("learning",MODE_PRIVATE);
        final int index=Math.max(0,prefs.getInt("card_index",0))%words.size();
        final Word first = words.get(index);
        final TextView question = text(first.en, 34, navy, Typeface.BOLD);
        question.setGravity(Gravity.CENTER);
        final TextView answer = text("اضغط لإظهار المعنى", 20, blue, Typeface.BOLD);
        answer.setGravity(Gravity.CENTER);
        LinearLayout card=new LinearLayout(this); card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18),dp(42),dp(18),dp(36)); card.setBackgroundColor(Color.WHITE);
        card.addView(question, lp(-1,-2));
        card.addView(answer, lp(-1,-2,0,0,20,0));
        Button reveal=wideButton("إظهار المعنى");
        reveal.setOnClickListener(new View.OnClickListener(){ public void onClick(View v) {
            answer.setText(first.ar + "\n" + first.example); say(first.en);
        }});
        card.addView(reveal, lp(-1,dp(52),0,0,28,0));
        Button next=wideButton("الكلمة التالية");
        next.setOnClickListener(new View.OnClickListener(){ public void onClick(View v){ prefs.edit().putInt("card_index",(index+1)%words.size()).apply(); showCards(); }});
        card.addView(next, lp(-1,dp(52),0,0,8,0));
        content.addView(cardWithMargin(card));
        TextView tip=text("كل مرة تفتح البطاقات تحصل على كلمة جديدة للمراجعة.", 15, Color.rgb(90,105,120), Typeface.NORMAL);
        tip.setGravity(Gravity.CENTER); content.addView(tip, lp(-1,-2,0,0,14,0));
    }

    private void showQuiz() {
        base("اختبار سريع", "اختر الترجمة الصحيحة");
        final Random random = new Random();
        final Word correct=words.get(random.nextInt(words.size()));
        final Word wrong1=words.get((words.indexOf(correct)+3)%words.size());
        final Word wrong2=words.get((words.indexOf(correct)+7)%words.size());
        final SharedPreferences prefs=getSharedPreferences("learning",MODE_PRIVATE);
        final int correctCount=prefs.getInt("correct",0), wrongCount=prefs.getInt("wrong",0);
        TextView score=text("الصحيح " + correctCount + "  •  الخطأ " + wrongCount + "  •  النقاط " + String.format(Locale.US,"%.1f",correctCount*.5f), 14, blue, Typeface.BOLD);
        score.setGravity(Gravity.CENTER); content.addView(score,lp(-1,-2,0,0,4,0));
        TextView q=text("ما معنى كلمة  " + correct.en + " ؟", 24, navy, Typeface.BOLD);
        q.setGravity(Gravity.CENTER); content.addView(q, lp(-1,dp(88),0,0,8,0));
        ArrayList<String> choices=new ArrayList<String>();
        choices.add(correct.ar); choices.add(wrong1.ar); choices.add(wrong2.ar);
        java.util.Collections.shuffle(choices);
        for (int i=0;i<choices.size();i++) {
            final String choice=choices.get(i);
            Button b=wideButton(choice);
            b.setOnClickListener(new View.OnClickListener(){ public void onClick(View v) {
                boolean ok=choice.equals(correct.ar);
                prefs.edit().putInt(ok?"correct":"wrong",(ok?correctCount:wrongCount)+1).apply();
                Toast.makeText(MainActivity.this, ok ? "إجابة ممتازة! + نصف نقطة" : "الإجابة الصحيحة: " + correct.ar, Toast.LENGTH_LONG).show();
                if (ok) say(correct.en);
                showQuiz();
            }});
            content.addView(b, lp(-1,dp(54),0,0,9,0));
        }
        TextView note=text("بعد كل إجابة يظهر سؤال جديد. يمكنك العودة للقاموس لمراجعة الكلمات.", 14, Color.rgb(90,105,120), Typeface.NORMAL);
        note.setGravity(Gravity.CENTER); content.addView(note, lp(-1,-2,0,18,0,0));
    }

    private Button navButton(String label, View.OnClickListener listener) {
        Button b = new Button(this); b.setText(label); b.setTextSize(14); b.setTextColor(navy);
        b.setAllCaps(false); b.setBackgroundColor(Color.TRANSPARENT); b.setOnClickListener(listener); return b;
    }
    private LinearLayout.LayoutParams navLp() { return new LinearLayout.LayoutParams(0, dp(48), 1); }
    private Button wideButton(String label) {
        Button b=new Button(this); b.setText(label); b.setTextSize(17); b.setTextColor(Color.WHITE); b.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        b.setAllCaps(false); b.setBackground(round(blue, 16)); return b;
    }
    private Button smallButton(String label, boolean selected) {
        Button b=new Button(this); b.setText(label); b.setTextSize(14); b.setAllCaps(false);
        b.setTextColor(selected ? Color.WHITE : navy); b.setBackground(round(selected ? blue : sky, 14));
        return b;
    }
    private View cardWithMargin(View inside) {
        FrameLayout f=new FrameLayout(this); f.setBackgroundColor(Color.WHITE); f.addView(inside);
        return f;
    }
    private TextView text(String value, int size, int color, int style) {
        TextView t=new TextView(this); t.setText(value); t.setTextSize(size); t.setTextColor(color); t.setTypeface(Typeface.DEFAULT, style); return t;
    }
    private LinearLayout.LayoutParams lp(int w,int h) { return new LinearLayout.LayoutParams(w,h); }
    private LinearLayout.LayoutParams lp(int w,int h,int weight,int l,int top,int r) {
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(w,h,weight); p.setMargins(dp(l),dp(top),dp(r),dp(10)); return p;
    }
    private int dp(int n) { return (int)(n*getResources().getDisplayMetrics().density+0.5f); }
    private GradientDrawable round(int color,int radius) { GradientDrawable d=new GradientDrawable(); d.setColor(color); d.setCornerRadius(dp(radius)); return d; }
    private void say(String word) { if (tts!=null) tts.speak(word, TextToSpeech.QUEUE_FLUSH, null); }
    @Override protected void onDestroy() { if(tts!=null){tts.stop();tts.shutdown();} super.onDestroy(); }

    private String gradeName(String key) { for(int i=0;i<gradeKeys.length;i++) if(gradeKeys[i].equals(key)) return gradeLabels[i]; return "الصف " + key; }

    private void loadWords() {
        try {
            InputStream in=getAssets().open("words.json"); ByteArrayOutputStream out=new ByteArrayOutputStream();
            byte[] buffer=new byte[8192]; int read; while((read=in.read(buffer))!=-1) out.write(buffer,0,read); in.close();
            JSONArray list=new JSONObject(out.toString("UTF-8")).getJSONArray("words");
            for(int i=0;i<list.length();i++) { JSONObject item=list.getJSONObject(i); String en=item.optString("word_en").trim(); String ar=item.optString("meaning_ar").trim(); String grade=item.optString("grade").trim(); if(en.length()>0&&ar.length()>0) add(en,ar,grade,"Example: " + en); }
        } catch(Exception ignored) { }
        if(words.size()==0) seedFallback();
    }

    private void seedFallback() {
        add("apple","تفاحة","KG","I eat a red apple.");
        add("cat","قطة","KG","The cat is small.");
        add("sun","شمس","KG","The sun is bright.");
        add("book","كتاب","1","This book is new.");
        add("school","مدرسة","1","My school is beautiful.");
        add("water","ماء","2","Drink clean water.");
    }
    private void add(String e,String a,String g,String x) { words.add(new Word(e,a,g,x)); }
}
