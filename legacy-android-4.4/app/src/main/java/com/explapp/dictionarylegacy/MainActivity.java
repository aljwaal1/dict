package com.explapp.dictionarylegacy;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.InputMethodManager;
import android.content.Context;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.Locale;
import java.util.Random;
import java.util.Set;

public class MainActivity extends Activity {
    private static final int NAVY = Color.rgb(22, 44, 76);
    private static final int BLUE = Color.rgb(34, 105, 190);
    private static final int BLUE_DARK = Color.rgb(24, 80, 150);
    private static final int SKY = Color.rgb(232, 242, 253);
    private static final int MINT = Color.rgb(226, 246, 239);
    private static final int GREEN = Color.rgb(24, 132, 91);
    private static final int RED = Color.rgb(190, 62, 65);
    private static final int AMBER = Color.rgb(242, 166, 46);
    private static final int INK = Color.rgb(34, 47, 62);
    private static final int MUTED = Color.rgb(96, 112, 130);
    private static final int PAGE_SIZE = 20;

    private final ArrayList<Word> words = new ArrayList<Word>();
    private final String[] gradeKeys = {"الكل", "KG", "1", "2", "3", "4", "5", "6", "7", "8"};
    private final String[] gradeLabels = {"الكل", "روضة", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس", "السابع", "الثامن"};
    private final Random random = new Random();

    private LinearLayout content;
    private ScrollView scroll;
    private EditText search;
    private TextToSpeech tts;
    private boolean ttsReady;
    private String selectedGrade = "الكل";
    private String searchQuery = "";
    private int currentPage;
    private int currentSection;
    private ArrayList<Word> quizWords = new ArrayList<Word>();
    private int quizIndex;
    private int quizCorrect;
    private int quizWrong;
    private boolean quizLocked;

    private static class Word {
        int id;
        String en;
        String ar;
        String grade;

        Word(int id, String en, String ar, String grade) {
            this.id = id;
            this.en = en;
            this.ar = ar;
            this.grade = grade;
        }
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        loadWords();
        selectedGrade = getSharedPreferences("app", MODE_PRIVATE).getString("last_grade", "الكل");
        tts = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
            @Override public void onInit(int status) {
                if (status == TextToSpeech.SUCCESS) {
                    int result = tts.setLanguage(Locale.US);
                    ttsReady = result != TextToSpeech.LANG_MISSING_DATA && result != TextToSpeech.LANG_NOT_SUPPORTED;
                }
            }
        });
        showDictionary();
    }

    private void buildPage(String section, String hint, int activeSection) {
        currentSection = activeSection;
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        root.setBackgroundColor(Color.rgb(247, 249, 252));

        LinearLayout head = new LinearLayout(this);
        head.setOrientation(LinearLayout.VERTICAL);
        head.setPadding(dp(18), dp(15), dp(18), dp(14));
        head.setBackground(round(NAVY, 0));
        TextView brand = text("قاموسي المدرسي", 25, Color.WHITE, Typeface.BOLD);
        TextView subtitle = text(section + "  •  " + hint, 14, Color.rgb(205, 224, 246), Typeface.NORMAL);
        head.addView(brand);
        head.addView(subtitle, lp(-1, -2, 0, 0, 4, 0, 0));
        root.addView(head);

        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(14), dp(12), dp(14), dp(12));
        scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setClipToPadding(false);
        scroll.addView(content, new ScrollView.LayoutParams(-1, -2));
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));

        LinearLayout nav = new LinearLayout(this);
        nav.setGravity(Gravity.CENTER);
        nav.setPadding(dp(4), dp(5), dp(4), dp(5));
        nav.setBackgroundColor(Color.WHITE);
        nav.addView(navButton("قاموس", android.R.drawable.ic_menu_search, 0), navLp());
        nav.addView(navButton("بطاقات", android.R.drawable.ic_menu_agenda, 1), navLp());
        nav.addView(navButton("اختبار", android.R.drawable.ic_menu_edit, 2), navLp());
        nav.addView(navButton("تقدّمي", android.R.drawable.ic_menu_info_details, 3), navLp());
        root.addView(nav);
        setContentView(root);
        content.setAlpha(0f);
        content.setTranslationY(dp(8));
        content.animate().alpha(1f).translationY(0).setDuration(180).start();
    }

    private void showDictionary() {
        buildPage("القاموس", words.size() + " كلمة دون إنترنت", 0);
        search = new EditText(this);
        search.setSingleLine(true);
        search.setHint("ابحث بالإنجليزية أو العربية");
        search.setTextSize(16);
        search.setTextColor(INK);
        search.setHintTextColor(MUTED);
        search.setCompoundDrawablesWithIntrinsicBounds(0, 0, android.R.drawable.ic_menu_search, 0);
        search.setCompoundDrawablePadding(dp(9));
        search.setBackground(round(Color.WHITE, 14, Color.rgb(216, 225, 235), 1));
        search.setPadding(dp(14), dp(8), dp(14), dp(8));
        search.setText(searchQuery);
        search.setSelection(search.length());
        content.addView(search, lp(-1, dp(54), 0, 0, 0, 0, 10));
        search.addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence s, int start, int count, int after) { }
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                searchQuery = s.toString();
                currentPage = 0;
                renderWords();
            }
            public void afterTextChanged(Editable editable) { }
        });

        HorizontalScrollView gradesScroll = new HorizontalScrollView(this);
        gradesScroll.setHorizontalScrollBarEnabled(false);
        LinearLayout gradeRow = new LinearLayout(this);
        gradeRow.setPadding(0, 0, 0, dp(7));
        for (int i = 0; i < gradeKeys.length; i++) {
            final String grade = gradeKeys[i];
            Button button = chip(gradeLabels[i], grade.equals(selectedGrade));
            button.setOnClickListener(new View.OnClickListener() {
                public void onClick(View view) {
                    selectedGrade = grade;
                    getSharedPreferences("app", MODE_PRIVATE).edit().putString("last_grade", grade).apply();
                    currentPage = 0;
                    showDictionary();
                }
            });
            gradeRow.addView(button, lp(-2, dp(42), 0, 0, 0, 6, 0));
        }
        gradesScroll.addView(gradeRow);
        content.addView(gradesScroll, lp(-1, -2, 0, 0, 0, 0, 4));
        renderWords();
    }

    private void renderWords() {
        while (content.getChildCount() > 2) content.removeViewAt(2);
        ArrayList<Word> matches = filteredWords(selectedGrade, searchQuery);
        if (matches.isEmpty()) {
            LinearLayout empty = emptyState(android.R.drawable.ic_menu_search, "لم نعثر على كلمة", "جرّب كتابة جزء من الكلمة أو اختر صفاً آخر");
            content.addView(empty, lp(-1, -2, 0, 10, 16, 0, 0));
            return;
        }
        int pages = (matches.size() + PAGE_SIZE - 1) / PAGE_SIZE;
        currentPage = Math.max(0, Math.min(currentPage, pages - 1));
        int start = currentPage * PAGE_SIZE;
        int end = Math.min(matches.size(), start + PAGE_SIZE);
        TextView count = text("عرض " + (start + 1) + "–" + end + " من " + matches.size(), 13, MUTED, Typeface.BOLD);
        count.setGravity(Gravity.CENTER);
        content.addView(count, lp(-1, -2, 0, 0, 2, 0, 7));
        for (int i = start; i < end; i++) content.addView(wordCard(matches.get(i)), lp(-1, -2, 0, 0, 0, 0, 9));
        if (pages > 1) addPager(pages);
    }

    private ArrayList<Word> filteredWords(String grade, String query) {
        String normalizedQuery = normalize(query);
        ArrayList<Word> result = new ArrayList<Word>();
        for (Word word : words) {
            if (!"الكل".equals(grade) && !grade.equals(word.grade)) continue;
            if (normalizedQuery.length() > 0 && !normalize(word.en).contains(normalizedQuery) && !normalize(word.ar).contains(normalizedQuery)) continue;
            result.add(word);
        }
        return result;
    }

    private void addPager(final int pages) {
        LinearLayout row = new LinearLayout(this);
        row.setGravity(Gravity.CENTER);
        Button previous = outlineButton("السابق");
        previous.setEnabled(currentPage > 0);
        previous.setAlpha(previous.isEnabled() ? 1f : .45f);
        previous.setOnClickListener(new View.OnClickListener() {
            public void onClick(View view) { currentPage--; renderWords(); scroll.smoothScrollTo(0, 0); }
        });
        TextView page = text((currentPage + 1) + " / " + pages, 15, NAVY, Typeface.BOLD);
        page.setGravity(Gravity.CENTER);
        Button next = outlineButton("التالي");
        next.setEnabled(currentPage < pages - 1);
        next.setAlpha(next.isEnabled() ? 1f : .45f);
        next.setOnClickListener(new View.OnClickListener() {
            public void onClick(View view) { currentPage++; renderWords(); scroll.smoothScrollTo(0, 0); }
        });
        row.addView(previous, new LinearLayout.LayoutParams(0, dp(48), 1));
        row.addView(page, new LinearLayout.LayoutParams(0, dp(48), .65f));
        row.addView(next, new LinearLayout.LayoutParams(0, dp(48), 1));
        content.addView(row, lp(-1, -2, 0, 0, 4, 0, 4));
    }

    private View wordCard(final Word word) {
        LinearLayout card = card();
        LinearLayout titleRow = new LinearLayout(this);
        titleRow.setGravity(Gravity.CENTER_VERTICAL);
        titleRow.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);
        TextView en = text(word.en, 22, NAVY, Typeface.BOLD);
        en.setSingleLine(false);
        titleRow.addView(en, new LinearLayout.LayoutParams(0, -2, 1));
        Button speak = iconButton(android.R.drawable.ic_btn_speak_now, "نطق");
        speak.setOnClickListener(new View.OnClickListener() { public void onClick(View view) { say(word.en); } });
        titleRow.addView(speak, new LinearLayout.LayoutParams(dp(48), dp(44)));
        card.addView(titleRow);
        TextView ar = text(word.ar, 19, BLUE_DARK, Typeface.BOLD);
        card.addView(ar, lp(-1, -2, 0, 0, 4, 0, 0));
        TextView grade = text(gradeName(word.grade), 13, MUTED, Typeface.NORMAL);
        card.addView(grade, lp(-1, -2, 0, 0, 4, 0, 8));
        LinearLayout actions = new LinearLayout(this);
        actions.setGravity(Gravity.CENTER);
        final boolean difficult = difficultIds().contains(String.valueOf(word.id));
        Button difficultButton = smallAction(difficult ? "إزالة من الصعبة" : "أحتاج مراجعتها", difficult ? AMBER : SKY, difficult ? Color.WHITE : NAVY);
        difficultButton.setOnClickListener(new View.OnClickListener() {
            public void onClick(View view) { toggleDifficult(word); renderWords(); }
        });
        actions.addView(difficultButton, new LinearLayout.LayoutParams(0, dp(44), 1));
        card.addView(actions);
        return elevated(card);
    }

    private void showCards() {
        buildPage("بطاقات المراجعة", "تعلّم على مهل وثبّت الكلمات", 1);
        addGradeChooser(new GradeChoiceListener() {
            public void onGrade(String grade) { selectedGrade = grade; showCards(); }
        });
        final ArrayList<Word> deck = filteredWords(selectedGrade, "");
        if (deck.isEmpty()) {
            content.addView(emptyState(android.R.drawable.ic_menu_agenda, "لا توجد بطاقات", "اختر صفاً يحتوي على كلمات"));
            return;
        }
        SharedPreferences prefs = learningPrefs();
        int saved = prefs.getInt("card_" + selectedGrade, 0);
        final int index = Math.max(0, saved) % deck.size();
        final Word word = deck.get(index);
        TextView progress = text("البطاقة " + (index + 1) + " من " + deck.size(), 14, MUTED, Typeface.BOLD);
        progress.setGravity(Gravity.CENTER);
        content.addView(progress, lp(-1, -2, 0, 0, 5, 0, 8));

        final LinearLayout card = card();
        card.setGravity(Gravity.CENTER);
        card.setPadding(dp(20), dp(32), dp(20), dp(26));
        TextView wordText = text(word.en, 34, NAVY, Typeface.BOLD);
        wordText.setGravity(Gravity.CENTER);
        wordText.setTextDirection(View.TEXT_DIRECTION_LTR);
        card.addView(wordText, lp(-1, -2));
        final TextView answer = text("اضغط لإظهار المعنى", 18, BLUE, Typeface.BOLD);
        answer.setGravity(Gravity.CENTER);
        card.addView(answer, lp(-1, -2, 0, 0, 18, 0, 18));
        Button reveal = primaryButton("إظهار المعنى والاستماع");
        reveal.setOnClickListener(new View.OnClickListener() {
            public void onClick(View view) {
                answer.setText(word.ar);
                say(word.en);
                answer.setAlpha(0f);
                answer.animate().alpha(1f).setDuration(160).start();
            }
        });
        card.addView(reveal, lp(-1, dp(52), 0, 0, 0, 0, 9));
        LinearLayout actions = new LinearLayout(this);
        Button review = outlineButton("راجعها لاحقاً");
        review.setOnClickListener(new View.OnClickListener() {
            public void onClick(View view) { setDifficult(word, true); goToNextCard(deck, index); }
        });
        Button mastered = coloredButton("أتقنتها", GREEN);
        mastered.setOnClickListener(new View.OnClickListener() {
            public void onClick(View view) { markMastered(word); setDifficult(word, false); goToNextCard(deck, index); }
        });
        actions.addView(review, weightedButton(1, 0, 4));
        actions.addView(mastered, weightedButton(1, 4, 0));
        card.addView(actions, lp(-1, dp(50), 0, 0, 0, 0, 0));
        content.addView(elevated(card), lp(-1, -2, 0, 0, 4, 0, 10));
    }

    private void goToNextCard(ArrayList<Word> deck, int index) {
        learningPrefs().edit().putInt("card_" + selectedGrade, (index + 1) % deck.size()).apply();
        showCards();
    }

    private void showQuizSetup() {
        buildPage("اختبار ذكي", "10 أسئلة من الصف المختار", 2);
        TextView intro = text("اختر مستوى الاختبار", 21, NAVY, Typeface.BOLD);
        content.addView(intro, lp(-1, -2, 0, 0, 5, 0, 10));
        for (int i = 1; i < gradeKeys.length; i++) {
            final String grade = gradeKeys[i];
            int completed = masteredCount(grade);
            LinearLayout row = card();
            TextView label = text(gradeLabels[i], 18, NAVY, Typeface.BOLD);
            TextView detail = text(completed + " من 150 كلمة متقنة", 13, MUTED, Typeface.NORMAL);
            row.addView(label);
            row.addView(detail, lp(-1, -2, 0, 0, 3, 0, 8));
            Button start = primaryButton("ابدأ الاختبار");
            start.setOnClickListener(new View.OnClickListener() {
                public void onClick(View view) { startQuiz(grade); }
            });
            row.addView(start, lp(-1, dp(48)));
            content.addView(elevated(row), lp(-1, -2, 0, 0, 0, 0, 9));
        }
    }

    private void startQuiz(String grade) {
        selectedGrade = grade;
        quizWords = filteredWords(grade, "");
        Collections.shuffle(quizWords);
        if (quizWords.size() > 10) quizWords = new ArrayList<Word>(quizWords.subList(0, 10));
        quizIndex = 0;
        quizCorrect = 0;
        quizWrong = 0;
        quizLocked = false;
        renderQuizQuestion();
    }

    private void renderQuizQuestion() {
        buildPage("اختبار " + gradeName(selectedGrade), "السؤال " + Math.min(quizIndex + 1, quizWords.size()) + " من " + quizWords.size(), 2);
        if (quizIndex >= quizWords.size()) {
            showQuizResult();
            return;
        }
        quizLocked = false;
        final Word correct = quizWords.get(quizIndex);
        TextView score = text("صحيح " + quizCorrect + "   •   يحتاج مراجعة " + quizWrong, 14, BLUE, Typeface.BOLD);
        score.setGravity(Gravity.CENTER);
        content.addView(score, lp(-1, -2, 0, 0, 3, 0, 12));
        LinearLayout questionCard = card();
        questionCard.setGravity(Gravity.CENTER);
        TextView prompt = text("ما معنى", 15, MUTED, Typeface.NORMAL);
        prompt.setGravity(Gravity.CENTER);
        TextView question = text(correct.en, 31, NAVY, Typeface.BOLD);
        question.setGravity(Gravity.CENTER);
        question.setTextDirection(View.TEXT_DIRECTION_LTR);
        questionCard.addView(prompt);
        questionCard.addView(question, lp(-1, -2, 0, 0, 8, 0, 5));
        Button listen = outlineButton("استمع للكلمة");
        listen.setOnClickListener(new View.OnClickListener() { public void onClick(View view) { say(correct.en); } });
        questionCard.addView(listen, lp(-1, dp(46), 0, 0, 8, 0, 0));
        content.addView(elevated(questionCard), lp(-1, -2, 0, 0, 0, 0, 12));

        ArrayList<String> choices = quizChoices(correct);
        for (final String choice : choices) {
            final Button answer = outlineButton(choice);
            answer.setTextSize(17);
            answer.setOnClickListener(new View.OnClickListener() {
                public void onClick(View view) {
                    if (quizLocked) return;
                    quizLocked = true;
                    boolean ok = choice.equals(correct.ar);
                    if (ok) {
                        quizCorrect++;
                        markMastered(correct);
                        setDifficult(correct, false);
                        answer.setBackground(round(MINT, 14, GREEN, 2));
                        answer.setTextColor(GREEN);
                        say(correct.en);
                    } else {
                        quizWrong++;
                        setDifficult(correct, true);
                        answer.setBackground(round(Color.rgb(253, 235, 235), 14, RED, 2));
                        answer.setTextColor(RED);
                    }
                    learningPrefs().edit()
                            .putInt("correct", learningPrefs().getInt("correct", 0) + (ok ? 1 : 0))
                            .putInt("wrong", learningPrefs().getInt("wrong", 0) + (ok ? 0 : 1))
                            .apply();
                    showQuizFeedback(correct, ok);
                }
            });
            content.addView(answer, lp(-1, dp(54), 0, 0, 0, 0, 9));
        }
    }

    private ArrayList<String> quizChoices(Word correct) {
        HashSet<String> values = new HashSet<String>();
        values.add(correct.ar);
        ArrayList<Word> sameGrade = filteredWords(correct.grade, "");
        while (values.size() < 4 && values.size() < sameGrade.size()) values.add(sameGrade.get(random.nextInt(sameGrade.size())).ar);
        ArrayList<String> choices = new ArrayList<String>(values);
        Collections.shuffle(choices);
        return choices;
    }

    private void showQuizFeedback(Word correct, boolean ok) {
        TextView feedback = text(ok ? "إجابة صحيحة، أحسنت!" : "الإجابة الصحيحة: " + correct.ar, 16, ok ? GREEN : RED, Typeface.BOLD);
        feedback.setGravity(Gravity.CENTER);
        feedback.setBackground(round(ok ? MINT : Color.rgb(253, 235, 235), 12));
        content.addView(feedback, lp(-1, -2, 0, 10, 4, 10, 8));
        Button next = coloredButton(quizIndex + 1 == quizWords.size() ? "عرض النتيجة" : "السؤال التالي", BLUE);
        next.setOnClickListener(new View.OnClickListener() {
            public void onClick(View view) { quizIndex++; renderQuizQuestion(); }
        });
        content.addView(next, lp(-1, dp(52), 0, 0, 0, 0, 8));
        scroll.post(new Runnable() { public void run() { scroll.smoothScrollTo(0, content.getHeight()); } });
    }

    private void showQuizResult() {
        int percent = quizWords.isEmpty() ? 0 : Math.round(quizCorrect * 100f / quizWords.size());
        LinearLayout result = card();
        result.setGravity(Gravity.CENTER);
        ImageView trophy = new ImageView(this);
        trophy.setImageResource(android.R.drawable.star_big_on);
        trophy.setColorFilter(AMBER);
        result.addView(trophy, new LinearLayout.LayoutParams(dp(64), dp(64)));
        TextView title = text(percent >= 80 ? "نتيجة رائعة" : percent >= 50 ? "تقدّم جيد" : "واصل المراجعة", 25, NAVY, Typeface.BOLD);
        title.setGravity(Gravity.CENTER);
        result.addView(title, lp(-1, -2, 0, 0, 10, 0, 5));
        TextView details = text(percent + "%\n" + quizCorrect + " صحيحة  •  " + quizWrong + " للمراجعة", 17, MUTED, Typeface.BOLD);
        details.setGravity(Gravity.CENTER);
        result.addView(details, lp(-1, -2, 0, 0, 5, 0, 16));
        Button retry = primaryButton("إعادة الاختبار");
        retry.setOnClickListener(new View.OnClickListener() { public void onClick(View view) { startQuiz(selectedGrade); } });
        result.addView(retry, lp(-1, dp(52), 0, 0, 0, 0, 8));
        Button review = outlineButton("مراجعة الكلمات الصعبة");
        review.setOnClickListener(new View.OnClickListener() { public void onClick(View view) { showDifficultCards(); } });
        result.addView(review, lp(-1, dp(52)));
        content.addView(elevated(result), lp(-1, -2, 0, 0, 16, 0, 0));
    }

    private void showProgress() {
        buildPage("تقدّمي", "إحصاءات محفوظة لكل طالب", 3);
        addProfileChooser();
        SharedPreferences prefs = learningPrefs();
        int correct = prefs.getInt("correct", 0);
        int wrong = prefs.getInt("wrong", 0);
        int mastered = masteredIds().size();
        LinearLayout summary = new LinearLayout(this);
        summary.setGravity(Gravity.CENTER);
        summary.addView(statBox("متقنة", String.valueOf(mastered), GREEN), weightedButton(1, 0, 4));
        summary.addView(statBox("صحيحة", String.valueOf(correct), BLUE), weightedButton(1, 4, 4));
        summary.addView(statBox("للمراجعة", String.valueOf(difficultIds().size()), AMBER), weightedButton(1, 4, 0));
        content.addView(summary, lp(-1, dp(92), 0, 0, 4, 0, 12));

        TextView gradesTitle = text("التقدم حسب الصف", 19, NAVY, Typeface.BOLD);
        content.addView(gradesTitle, lp(-1, -2, 0, 0, 0, 0, 7));
        for (int i = 1; i < gradeKeys.length; i++) {
            String grade = gradeKeys[i];
            int done = masteredCount(grade);
            LinearLayout progress = card();
            LinearLayout row = new LinearLayout(this);
            TextView gradeName = text(gradeLabels[i], 16, NAVY, Typeface.BOLD);
            TextView count = text(done + " / 150", 14, MUTED, Typeface.BOLD);
            count.setGravity(Gravity.LEFT);
            row.addView(gradeName, new LinearLayout.LayoutParams(0, -2, 1));
            row.addView(count, new LinearLayout.LayoutParams(0, -2, 1));
            progress.addView(row);
            progress.addView(progressBar(done / 150f), lp(-1, dp(8), 0, 0, 9, 0, 0));
            content.addView(elevated(progress), lp(-1, -2, 0, 0, 0, 0, 7));
        }
        Button difficult = coloredButton("مراجعة الكلمات الصعبة", AMBER);
        difficult.setOnClickListener(new View.OnClickListener() { public void onClick(View view) { showDifficultCards(); } });
        content.addView(difficult, lp(-1, dp(52), 0, 0, 8, 0, 8));
        Button reset = outlineButton("إعادة ضبط تقدم هذا الطالب");
        reset.setTextColor(RED);
        reset.setOnClickListener(new View.OnClickListener() { public void onClick(View view) { confirmReset(); } });
        content.addView(reset, lp(-1, dp(50), 0, 0, 0, 0, 4));
    }

    private void showDifficultCards() {
        Set<String> difficult = difficultIds();
        final ArrayList<Word> review = new ArrayList<Word>();
        for (Word word : words) if (difficult.contains(String.valueOf(word.id))) review.add(word);
        if (review.isEmpty()) {
            Toast.makeText(this, "لا توجد كلمات صعبة حالياً", Toast.LENGTH_SHORT).show();
            showProgress();
            return;
        }
        selectedGrade = "الكل";
        buildPage("مراجعة الكلمات الصعبة", review.size() + " كلمة", 3);
        for (Word word : review) content.addView(wordCard(word), lp(-1, -2, 0, 0, 0, 0, 9));
    }

    private void addProfileChooser() {
        final SharedPreferences app = getSharedPreferences("app", MODE_PRIVATE);
        final int active = app.getInt("profile", 1);
        TextView heading = text("ملف الطالب", 14, MUTED, Typeface.BOLD);
        content.addView(heading, lp(-1, -2, 0, 0, 0, 0, 5));
        LinearLayout profiles = new LinearLayout(this);
        for (int i = 1; i <= 3; i++) {
            final int profile = i;
            Button button = chip("الطالب " + i, active == i);
            button.setOnClickListener(new View.OnClickListener() {
                public void onClick(View view) { app.edit().putInt("profile", profile).apply(); showProgress(); }
            });
            profiles.addView(button, weightedButton(1, i == 1 ? 0 : 3, i == 3 ? 0 : 3));
        }
        content.addView(profiles, lp(-1, dp(46), 0, 0, 0, 0, 11));
    }

    private void confirmReset() {
        new AlertDialog.Builder(this)
                .setTitle("إعادة ضبط التقدم؟")
                .setMessage("سيتم حذف نتائج الطالب الحالي وكلماته الصعبة فقط. لن تُحذف كلمات القاموس.")
                .setNegativeButton("إلغاء", null)
                .setPositiveButton("إعادة الضبط", new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int which) { learningPrefs().edit().clear().apply(); showProgress(); }
                }).show();
    }

    private View statBox(String label, String value, int color) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER);
        box.setBackground(round(Color.WHITE, 14, Color.rgb(225, 232, 240), 1));
        TextView number = text(value, 23, color, Typeface.BOLD);
        TextView caption = text(label, 12, MUTED, Typeface.BOLD);
        box.addView(number);
        box.addView(caption);
        return box;
    }

    private View progressBar(float value) {
        FrameLayout track = new FrameLayout(this);
        track.setBackground(round(Color.rgb(227, 233, 240), 8));
        View fill = new View(this);
        fill.setBackground(round(GREEN, 8));
        int width = Math.max(dp(3), (int) (getResources().getDisplayMetrics().widthPixels * .82f * Math.max(0f, Math.min(1f, value))));
        track.addView(fill, new FrameLayout.LayoutParams(width, -1));
        return track;
    }

    private void addGradeChooser(final GradeChoiceListener listener) {
        HorizontalScrollView horizontal = new HorizontalScrollView(this);
        horizontal.setHorizontalScrollBarEnabled(false);
        LinearLayout row = new LinearLayout(this);
        for (int i = 0; i < gradeKeys.length; i++) {
            final String grade = gradeKeys[i];
            Button button = chip(gradeLabels[i], grade.equals(selectedGrade));
            button.setOnClickListener(new View.OnClickListener() { public void onClick(View view) { listener.onGrade(grade); } });
            row.addView(button, lp(-2, dp(42), 0, 0, 0, 6, 0));
        }
        horizontal.addView(row);
        content.addView(horizontal, lp(-1, -2, 0, 0, 0, 0, 8));
    }

    private interface GradeChoiceListener { void onGrade(String grade); }

    private Button navButton(String label, int icon, final int section) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextSize(12);
        button.setTextColor(section == currentSection ? BLUE : MUTED);
        button.setTypeface(Typeface.DEFAULT, section == currentSection ? Typeface.BOLD : Typeface.NORMAL);
        button.setAllCaps(false);
        button.setGravity(Gravity.CENTER);
        button.setCompoundDrawablesWithIntrinsicBounds(0, icon, 0, 0);
        button.setCompoundDrawablePadding(dp(1));
        button.setBackgroundColor(Color.TRANSPARENT);
        button.setOnClickListener(new View.OnClickListener() {
            public void onClick(View view) {
                hideKeyboard();
                if (section == 0) showDictionary();
                else if (section == 1) showCards();
                else if (section == 2) showQuizSetup();
                else showProgress();
            }
        });
        return button;
    }

    private LinearLayout emptyState(int icon, String title, String description) {
        LinearLayout empty = new LinearLayout(this);
        empty.setOrientation(LinearLayout.VERTICAL);
        empty.setGravity(Gravity.CENTER);
        empty.setPadding(dp(16), dp(32), dp(16), dp(32));
        ImageView image = new ImageView(this);
        image.setImageResource(icon);
        image.setColorFilter(BLUE);
        empty.addView(image, new LinearLayout.LayoutParams(dp(52), dp(52)));
        TextView heading = text(title, 20, NAVY, Typeface.BOLD);
        heading.setGravity(Gravity.CENTER);
        empty.addView(heading, lp(-1, -2, 0, 0, 12, 0, 5));
        TextView body = text(description, 15, MUTED, Typeface.NORMAL);
        body.setGravity(Gravity.CENTER);
        empty.addView(body);
        return empty;
    }

    private LinearLayout card() {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(15), dp(13), dp(15), dp(13));
        card.setBackground(round(Color.WHITE, 15, Color.rgb(227, 233, 240), 1));
        return card;
    }

    private View elevated(View view) {
        if (Build.VERSION.SDK_INT >= 21) view.setElevation(dp(2));
        return view;
    }

    private Button primaryButton(String label) { return coloredButton(label, BLUE); }

    private Button coloredButton(String label, int color) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextSize(16);
        button.setTextColor(Color.WHITE);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setAllCaps(false);
        button.setGravity(Gravity.CENTER);
        button.setPadding(dp(10), 0, dp(10), 0);
        button.setBackground(round(color, 14));
        return button;
    }

    private Button outlineButton(String label) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextSize(15);
        button.setTextColor(NAVY);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setAllCaps(false);
        button.setGravity(Gravity.CENTER);
        button.setPadding(dp(8), 0, dp(8), 0);
        button.setBackground(round(Color.WHITE, 14, Color.rgb(190, 207, 226), 1));
        return button;
    }

    private Button chip(String label, boolean selected) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextSize(13);
        button.setAllCaps(false);
        button.setMinWidth(dp(64));
        button.setPadding(dp(12), 0, dp(12), 0);
        button.setTextColor(selected ? Color.WHITE : NAVY);
        button.setTypeface(Typeface.DEFAULT, selected ? Typeface.BOLD : Typeface.NORMAL);
        button.setBackground(round(selected ? BLUE : SKY, 15));
        return button;
    }

    private Button smallAction(String label, int background, int foreground) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextSize(13);
        button.setTextColor(foreground);
        button.setAllCaps(false);
        button.setBackground(round(background, 12));
        return button;
    }

    private Button iconButton(int icon, String description) {
        Button button = new Button(this);
        button.setContentDescription(description);
        button.setCompoundDrawablesWithIntrinsicBounds(icon, 0, 0, 0);
        button.setGravity(Gravity.CENTER);
        button.setBackground(round(SKY, 12));
        return button;
    }

    private TextView text(String value, int size, int color, int style) {
        TextView text = new TextView(this);
        text.setText(value);
        text.setTextSize(size);
        text.setTextColor(color);
        text.setTypeface(Typeface.DEFAULT, style);
        text.setLineSpacing(0, 1.08f);
        return text;
    }

    private LinearLayout.LayoutParams navLp() { return new LinearLayout.LayoutParams(0, dp(58), 1); }
    private LinearLayout.LayoutParams weightedButton(float weight, int left, int right) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, -1, weight);
        params.setMargins(dp(left), 0, dp(right), 0);
        return params;
    }
    private LinearLayout.LayoutParams lp(int width, int height) { return new LinearLayout.LayoutParams(width, height); }
    private LinearLayout.LayoutParams lp(int width, int height, float weight, int left, int top, int right, int bottom) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(width, height, weight);
        params.setMargins(dp(left), dp(top), dp(right), dp(bottom));
        return params;
    }

    private GradientDrawable round(int color, int radius) { return round(color, radius, Color.TRANSPARENT, 0); }
    private GradientDrawable round(int color, int radius, int strokeColor, int strokeWidth) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(dp(radius));
        if (strokeWidth > 0) drawable.setStroke(dp(strokeWidth), strokeColor);
        return drawable;
    }

    private int dp(int value) { return (int) (value * getResources().getDisplayMetrics().density + .5f); }

    private void say(String word) {
        if (!ttsReady) {
            Toast.makeText(this, "النطق غير متاح على هذا الجهاز", Toast.LENGTH_SHORT).show();
            return;
        }
        tts.speak(word, TextToSpeech.QUEUE_FLUSH, null);
    }

    private void hideKeyboard() {
        View focused = getCurrentFocus();
        if (focused != null) ((InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(focused.getWindowToken(), 0);
    }

    private SharedPreferences learningPrefs() {
        int profile = getSharedPreferences("app", MODE_PRIVATE).getInt("profile", 1);
        return getSharedPreferences("learning_" + profile, MODE_PRIVATE);
    }

    private Set<String> difficultIds() { return new HashSet<String>(learningPrefs().getStringSet("difficult", new HashSet<String>())); }
    private Set<String> masteredIds() { return new HashSet<String>(learningPrefs().getStringSet("mastered", new HashSet<String>())); }

    private void toggleDifficult(Word word) { setDifficult(word, !difficultIds().contains(String.valueOf(word.id))); }
    private void setDifficult(Word word, boolean difficult) {
        Set<String> ids = difficultIds();
        if (difficult) ids.add(String.valueOf(word.id)); else ids.remove(String.valueOf(word.id));
        learningPrefs().edit().putStringSet("difficult", ids).apply();
    }
    private void markMastered(Word word) {
        Set<String> ids = masteredIds();
        ids.add(String.valueOf(word.id));
        learningPrefs().edit().putStringSet("mastered", ids).apply();
    }
    private int masteredCount(String grade) {
        Set<String> ids = masteredIds();
        int count = 0;
        for (Word word : words) if (grade.equals(word.grade) && ids.contains(String.valueOf(word.id))) count++;
        return count;
    }

    private String gradeName(String key) {
        for (int i = 0; i < gradeKeys.length; i++) if (gradeKeys[i].equals(key)) return gradeLabels[i];
        return "الصف " + key;
    }

    private String normalize(String value) {
        if (value == null) return "";
        String normalized = Normalizer.normalize(value.trim().toLowerCase(Locale.US), Normalizer.Form.NFD);
        normalized = normalized.replaceAll("[\\u064B-\\u065F\\u0670\\u06D6-\\u06ED]", "");
        normalized = normalized.replace("ـ", "").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا");
        return normalized;
    }

    private void loadWords() {
        try {
            InputStream input = getAssets().open("words.json");
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            byte[] buffer = new byte[8192];
            int read;
            while ((read = input.read(buffer)) != -1) output.write(buffer, 0, read);
            input.close();
            JSONArray list = new JSONObject(output.toString("UTF-8")).getJSONArray("words");
            HashSet<String> seen = new HashSet<String>();
            for (int i = 0; i < list.length(); i++) {
                JSONObject item = list.getJSONObject(i);
                String en = item.optString("word_en").trim();
                String ar = item.optString("meaning_ar").trim();
                String grade = item.optString("grade").trim();
                String identity = en.toLowerCase(Locale.US) + "|" + grade;
                if (en.length() > 0 && ar.length() > 0 && validGrade(grade) && seen.add(identity)) {
                    words.add(new Word(item.optInt("id", i + 1), en, ar, grade));
                }
            }
        } catch (Exception ignored) { }
        if (words.isEmpty()) seedFallback();
    }

    private boolean validGrade(String grade) {
        for (int i = 1; i < gradeKeys.length; i++) if (gradeKeys[i].equals(grade)) return true;
        return false;
    }

    private void seedFallback() {
        words.add(new Word(1, "apple", "تفاحة", "KG"));
        words.add(new Word(2, "cat", "قطة", "KG"));
        words.add(new Word(3, "book", "كتاب", "1"));
        words.add(new Word(4, "school", "مدرسة", "1"));
    }

    @Override public void onBackPressed() {
        if (currentSection != 0) showDictionary(); else super.onBackPressed();
    }

    @Override protected void onDestroy() {
        if (tts != null) { tts.stop(); tts.shutdown(); }
        super.onDestroy();
    }
}
