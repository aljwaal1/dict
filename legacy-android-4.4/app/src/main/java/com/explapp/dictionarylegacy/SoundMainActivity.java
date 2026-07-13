package com.explapp.dictionarylegacy;

import android.media.AudioManager;
import android.media.ToneGenerator;
import android.os.Bundle;
import android.os.Handler;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

/** Rich, lightweight feedback for the Android 4.4 dictionary only. */
public class SoundMainActivity extends MainActivity {
    private final Handler observer = new Handler();
    private ToneGenerator tones;
    private float downX;
    private float downY;
    private long lastSoundAt;
    private String lastSnapshot = "";

    @Override public void onCreate(Bundle savedInstanceState) {
        tones = new ToneGenerator(AudioManager.STREAM_MUSIC, 46);
        super.onCreate(savedInstanceState);
        observer.post(statusWatcher);
    }

    @Override public boolean dispatchTouchEvent(MotionEvent event) {
        if (event.getAction() == MotionEvent.ACTION_DOWN) {
            downX = event.getRawX();
            downY = event.getRawY();
        } else if (event.getAction() == MotionEvent.ACTION_UP
                && Math.abs(event.getRawX() - downX) < 18f
                && Math.abs(event.getRawY() - downY) < 18f) {
            View target = findView(getWindow().getDecorView(), event.getRawX(), event.getRawY());
            if (target != null && target.isClickable()) playFor(target);
        }
        return super.dispatchTouchEvent(event);
    }

    private void playFor(View view) {
        String text = view instanceof TextView ? ((TextView) view).getText().toString() : "";
        if (containsAny(text, "حفظ", "إضافة", "استيراد", "تأكيد")) {
            play(ToneGenerator.TONE_PROP_ACK, 115);
        } else if (containsAny(text, "خطأ", "حذف", "إلغاء", "مسح")) {
            play(ToneGenerator.TONE_PROP_NACK, 110);
        } else if (containsAny(text, "رجوع", "العودة")) {
            play(ToneGenerator.TONE_PROP_BEEP2, 80);
        } else if (containsAny(text, "نطق", "استماع", "اسمع")) {
            play(ToneGenerator.TONE_DTMF_6, 72);
        } else if (containsAny(text, "التالي", "اختبار", "ابدأ")) {
            play(ToneGenerator.TONE_DTMF_5, 72);
        } else {
            play(ToneGenerator.TONE_PROP_BEEP, 55);
        }
    }

    private final Runnable statusWatcher = new Runnable() {
        @Override public void run() {
            if (tones == null) return;
            String snapshot = collectText(getWindow().getDecorView());
            if (lastSnapshot.length() == 0) {
                lastSnapshot = snapshot;
            } else if (!snapshot.equals(lastSnapshot)) {
                if (containsAny(snapshot, "أحسنت", "إجابة صحيحة", "رائع")) {
                    play(ToneGenerator.TONE_CDMA_ALERT_CALL_GUARD, 330);
                } else if (containsAny(snapshot, "حاول مرة أخرى", "إجابة خاطئة")) {
                    play(ToneGenerator.TONE_PROP_NACK, 150);
                } else if (containsAny(snapshot, "اكتمل الاختبار", "النتيجة النهائية")) {
                    play(ToneGenerator.TONE_CDMA_CONFIRM, 220);
                }
                lastSnapshot = snapshot;
            }
            observer.postDelayed(this, 280L);
        }
    };

    private String collectText(View view) {
        StringBuilder builder = new StringBuilder();
        appendText(view, builder);
        return builder.toString();
    }

    private void appendText(View view, StringBuilder builder) {
        if (view == null || view.getVisibility() != View.VISIBLE) return;
        if (view instanceof TextView) builder.append('|').append(((TextView) view).getText());
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) appendText(group.getChildAt(i), builder);
        }
    }

    private View findView(View view, float x, float y) {
        if (view == null || view.getVisibility() != View.VISIBLE) return null;
        int[] location = new int[2];
        view.getLocationOnScreen(location);
        if (x < location[0] || x > location[0] + view.getWidth()
                || y < location[1] || y > location[1] + view.getHeight()) return null;
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = group.getChildCount() - 1; i >= 0; i--) {
                View child = findView(group.getChildAt(i), x, y);
                if (child != null) return child;
            }
        }
        return view;
    }

    private void play(int tone, int durationMs) {
        if (tones == null || System.currentTimeMillis() - lastSoundAt < 70L) return;
        lastSoundAt = System.currentTimeMillis();
        tones.startTone(tone, durationMs);
    }

    private boolean containsAny(String text, String... words) {
        for (String word : words) if (text.contains(word)) return true;
        return false;
    }

    @Override public void onBackPressed() {
        play(ToneGenerator.TONE_PROP_BEEP2, 80);
        super.onBackPressed();
    }

    @Override protected void onDestroy() {
        observer.removeCallbacksAndMessages(null);
        if (tones != null) {
            tones.release();
            tones = null;
        }
        super.onDestroy();
    }
}
