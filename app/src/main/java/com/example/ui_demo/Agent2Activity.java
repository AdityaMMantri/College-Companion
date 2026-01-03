package com.example.ui_demo;

import androidx.appcompat.app.AppCompatActivity;
import android.os.Bundle;
import android.text.SpannableStringBuilder;
import android.text.Spanned;
import android.text.style.StyleSpan;
import android.text.style.ForegroundColorSpan;
import android.text.style.TypefaceSpan;
import android.graphics.Typeface;
import android.view.Gravity;
import android.widget.*;
import org.json.JSONObject;
import android.graphics.Color;
import android.view.ViewGroup;
import android.view.View;
import android.widget.LinearLayout.LayoutParams;
import android.view.animation.TranslateAnimation;
import android.view.animation.AlphaAnimation;
import androidx.cardview.widget.CardView;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.ArrayList;
import java.util.List;

public class Agent2Activity extends AppCompatActivity {
    private EditText messageInput;
    private ImageButton sendButton;
    private LinearLayout chatContainer;
    private ScrollView chatScrollView;
    private String userEmail;
    private LinearLayout typingIndicatorContainer;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_agent2);

        messageInput = findViewById(R.id.messageInput);
        sendButton = findViewById(R.id.sendButton);
        chatContainer = findViewById(R.id.chatContainer);
        chatScrollView = findViewById(R.id.chatScrollView);
        typingIndicatorContainer = findViewById(R.id.typingIndicatorContainer);

        userEmail = getIntent().getStringExtra("userEmail");

        addWelcomeMessage();

        sendButton.setOnClickListener(v -> sendMessage());

        messageInput.setOnEditorActionListener((v, actionId, event) -> {
            sendMessage();
            return true;
        });

        messageInput.addTextChangedListener(new android.text.TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                boolean hasText = s.length() > 0;
                sendButton.setEnabled(hasText);
                sendButton.setAlpha(hasText ? 1.0f : 0.4f);
                sendButton.setColorFilter(hasText ?
                        Color.WHITE : Color.parseColor("#BBBBBB"));
            }

            @Override
            public void afterTextChanged(android.text.Editable s) {}
        });
    }

    private void sendMessage() {
        String userMessage = messageInput.getText().toString().trim();
        if (userMessage.isEmpty()) {
            shakeView(messageInput);
            return;
        }

        addUserMessage(userMessage);
        messageInput.setText("");
        showTypingIndicator(true);
        sendToAgent(userMessage);
    }

    private void addWelcomeMessage() {
        LinearLayout welcomeContainer = new LinearLayout(this);
        welcomeContainer.setOrientation(LinearLayout.VERTICAL);
        welcomeContainer.setGravity(Gravity.CENTER);
        welcomeContainer.setPadding(40, 60, 40, 60);

        TextView emoji = new TextView(this);
        emoji.setText("🤖");
        emoji.setTextSize(48);
        emoji.setGravity(Gravity.CENTER);
        welcomeContainer.addView(emoji);

        TextView welcomeView = new TextView(this);
        welcomeView.setText("Hello! I'm your AI coding assistant");
        welcomeView.setTextSize(16);
        welcomeView.setTextColor(Color.parseColor("#2C3E50"));
        welcomeView.setGravity(Gravity.CENTER);
        welcomeView.setPadding(0, 16, 0, 8);
        welcomeView.setTypeface(null, Typeface.BOLD);
        welcomeContainer.addView(welcomeView);

        TextView subtitle = new TextView(this);
        subtitle.setText("Ask me anything about programming!");
        subtitle.setTextSize(14);
        subtitle.setTextColor(Color.parseColor("#7F8C8D"));
        subtitle.setGravity(Gravity.CENTER);
        welcomeContainer.addView(subtitle);

        chatContainer.addView(welcomeContainer);
    }

    private void sendToAgent(String question) {
        new Thread(() -> {
            try {
                JSONObject json = new JSONObject();
                json.put("user", userEmail);
                json.put("question", question);

                String response = ApiClient.post("/agent2", json.toString());
                JSONObject resObj = new JSONObject(response);
                String agentResponse = resObj.optString("response", "No response from AI");

                runOnUiThread(() -> {
                    showTypingIndicator(false);
                    addAIMessage(agentResponse);
                });

            } catch (Exception e) {
                runOnUiThread(() -> {
                    showTypingIndicator(false);
                    Toast.makeText(this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
                });
            }
        }).start();
    }

    private void addUserMessage(String message) {
        LinearLayout messageWrapper = new LinearLayout(this);
        messageWrapper.setOrientation(LinearLayout.VERTICAL);
        LayoutParams wrapperParams = new LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        );
        wrapperParams.setMargins(60, 8, 20, 8);
        messageWrapper.setLayoutParams(wrapperParams);

        CardView cardView = new CardView(this);
        LayoutParams cardParams = new LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        );
        cardParams.gravity = Gravity.END;

        TextView textView = new TextView(this);
        textView.setText(message);
        textView.setTextSize(15);
        textView.setTextColor(Color.WHITE);
        textView.setPadding(40, 28, 40, 28);
        textView.setLineSpacing(6, 1.2f);

        cardView.setCardBackgroundColor(Color.parseColor("#007AFF"));
        cardView.setCardElevation(6);
        cardView.setRadius(28);
        cardView.setLayoutParams(cardParams);
        cardView.addView(textView);

        TextView timeStamp = new TextView(this);
        java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("HH:mm", java.util.Locale.getDefault());
        timeStamp.setText(sdf.format(new java.util.Date()));
        timeStamp.setTextSize(11);
        timeStamp.setTextColor(Color.parseColor("#95A5A6"));
        timeStamp.setPadding(0, 6, 12, 0);
        timeStamp.setGravity(Gravity.END);

        messageWrapper.addView(cardView);
        messageWrapper.addView(timeStamp);
        chatContainer.addView(messageWrapper);

        animateMessageEntry(messageWrapper, true);
        scrollToBottom();
    }

    private void addAIMessage(String message) {
        LinearLayout aiContainer = new LinearLayout(this);
        aiContainer.setOrientation(LinearLayout.VERTICAL);
        LayoutParams containerParams = new LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        );
        containerParams.setMargins(20, 8, 60, 8);
        aiContainer.setLayoutParams(containerParams);

        // Parse message into segments (text and code)
        List<MessageSegment> segments = parseMessage(message);

        for (MessageSegment segment : segments) {
            if (segment.isCode) {
                addCodeSegment(segment.content, segment.language, aiContainer);
            } else {
                addTextSegment(segment.content, aiContainer);
            }
        }

        // Timestamp
        TextView timeStamp = new TextView(this);
        java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("HH:mm", java.util.Locale.getDefault());
        timeStamp.setText(sdf.format(new java.util.Date()));
        timeStamp.setTextSize(11);
        timeStamp.setTextColor(Color.parseColor("#95A5A6"));
        timeStamp.setPadding(12, 6, 0, 0);
        aiContainer.addView(timeStamp);

        chatContainer.addView(aiContainer);
        animateMessageEntry(aiContainer, false);
        scrollToBottom();
    }

    private List<MessageSegment> parseMessage(String message) {
        List<MessageSegment> segments = new ArrayList<>();
        Pattern codePattern = Pattern.compile("```(\\w+)?\\n([\\s\\S]*?)```");
        Matcher matcher = codePattern.matcher(message);

        int lastEnd = 0;
        while (matcher.find()) {
            // Add text before code block
            if (matcher.start() > lastEnd) {
                String text = message.substring(lastEnd, matcher.start()).trim();
                if (!text.isEmpty()) {
                    segments.add(new MessageSegment(text, false, null));
                }
            }

            // Add code block
            String language = matcher.group(1);
            String code = matcher.group(2);
            segments.add(new MessageSegment(code, true, language));

            lastEnd = matcher.end();
        }

        // Add remaining text
        if (lastEnd < message.length()) {
            String text = message.substring(lastEnd).trim();
            if (!text.isEmpty()) {
                segments.add(new MessageSegment(text, false, null));
            }
        }

        // If no code blocks found, add entire message as text
        if (segments.isEmpty()) {
            segments.add(new MessageSegment(message, false, null));
        }

        return segments;
    }

    private void addTextSegment(String text, LinearLayout container) {
        CardView cardView = new CardView(this);
        LayoutParams cardParams = new LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        );
        cardParams.setMargins(0, 6, 0, 6);
        cardView.setLayoutParams(cardParams);
        cardView.setCardBackgroundColor(Color.parseColor("#F5F7FA"));
        cardView.setCardElevation(3);
        cardView.setRadius(28);

        TextView textView = new TextView(this);
        textView.setTextSize(15);
        textView.setTextColor(Color.parseColor("#2C3E50"));
        textView.setPadding(40, 28, 40, 28);
        textView.setLineSpacing(8, 1.25f);

        SpannableStringBuilder formatted = formatRichText(text);
        textView.setText(formatted);

        cardView.addView(textView);
        container.addView(cardView);
    }

    private void addCodeSegment(String code, String language, LinearLayout container) {
        LinearLayout codeContainer = new LinearLayout(this);
        codeContainer.setOrientation(LinearLayout.VERTICAL);
        LayoutParams codeContainerParams = new LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        );
        codeContainerParams.setMargins(0, 12, 0, 12);
        codeContainer.setLayoutParams(codeContainerParams);

        // Language label
        if (language != null && !language.isEmpty()) {
            LinearLayout labelContainer = new LinearLayout(this);
            labelContainer.setBackgroundColor(Color.parseColor("#2C3E50"));
            labelContainer.setPadding(32, 12, 32, 12);

            TextView langLabel = new TextView(this);
            langLabel.setText(language.toUpperCase());
            langLabel.setTextSize(12);
            langLabel.setTextColor(Color.parseColor("#3498DB"));
            langLabel.setTypeface(Typeface.MONOSPACE, Typeface.BOLD);

            labelContainer.addView(langLabel);
            codeContainer.addView(labelContainer);
        }

        // Code block
        CardView codeCard = new CardView(this);
        codeCard.setCardBackgroundColor(Color.parseColor("#282C34"));
        codeCard.setCardElevation(4);
        codeCard.setRadius(language != null && !language.isEmpty() ? 0 : 16);

        HorizontalScrollView scrollView = new HorizontalScrollView(this);

        TextView codeView = new TextView(this);
        codeView.setText(code.trim());
        codeView.setTextSize(14);
        codeView.setTextColor(Color.parseColor("#ABB2BF"));
        codeView.setTypeface(Typeface.MONOSPACE);
        codeView.setPadding(32, 28, 32, 28);
        codeView.setTextIsSelectable(true);
        codeView.setLineSpacing(4, 1.15f);

        scrollView.addView(codeView);
        codeCard.addView(scrollView);
        codeContainer.addView(codeCard);
        container.addView(codeContainer);
    }

    private SpannableStringBuilder formatRichText(String text) {
        SpannableStringBuilder builder = new SpannableStringBuilder();

        // Remove extra newlines but keep paragraph breaks
        text = text.replaceAll("\n{3,}", "\n\n");

        String[] lines = text.split("\n");

        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            if (line.isEmpty()) continue;

            int start = builder.length();

            // Handle bullet points
            if (line.matches("^\\*\\s+.*")) {
                line = "• " + line.substring(1).trim();
                builder.append(line);
                builder.setSpan(new ForegroundColorSpan(Color.parseColor("#3498DB")),
                        start, start + 1, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
            }
            // Handle numbered lists
            else if (line.matches("^\\d+\\.\\s+.*")) {
                builder.append(line);
                Matcher numMatcher = Pattern.compile("^(\\d+\\.)").matcher(line);
                if (numMatcher.find()) {
                    builder.setSpan(new StyleSpan(Typeface.BOLD),
                            start, start + numMatcher.end(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                    builder.setSpan(new ForegroundColorSpan(Color.parseColor("#3498DB")),
                            start, start + numMatcher.end(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                }
            }
            else {
                builder.append(line);
            }

            // Format bold text (**text**)
            String currentText = builder.toString();
            Pattern boldPattern = Pattern.compile("\\*\\*(.+?)\\*\\*");
            Matcher boldMatcher = boldPattern.matcher(currentText.substring(start));

            while (boldMatcher.find()) {
                int boldStart = start + boldMatcher.start();
                int boldEnd = start + boldMatcher.end();
                String boldText = boldMatcher.group(1);

                builder.replace(boldStart, boldEnd, boldText);
                builder.setSpan(new StyleSpan(Typeface.BOLD),
                        boldStart, boldStart + boldText.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                builder.setSpan(new ForegroundColorSpan(Color.parseColor("#E74C3C")),
                        boldStart, boldStart + boldText.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);

                currentText = builder.toString();
                boldMatcher = boldPattern.matcher(currentText.substring(start));
            }

            if (i < lines.length - 1 && !lines[i + 1].trim().isEmpty()) {
                builder.append("\n");
            }
        }

        return builder;
    }

    private void animateMessageEntry(View view, boolean isUser) {
        TranslateAnimation translate = new TranslateAnimation(
                isUser ? 200 : -200, 0, 0, 0
        );
        translate.setDuration(250);

        AlphaAnimation alpha = new AlphaAnimation(0, 1);
        alpha.setDuration(250);

        view.startAnimation(translate);
        view.startAnimation(alpha);
    }

    private void shakeView(View view) {
        TranslateAnimation shake = new TranslateAnimation(0, 15, 0, 0);
        shake.setDuration(50);
        shake.setRepeatCount(3);
        shake.setRepeatMode(android.view.animation.Animation.REVERSE);
        view.startAnimation(shake);
    }

    private void showTypingIndicator(boolean show) {
        if (typingIndicatorContainer != null) {
            typingIndicatorContainer.setVisibility(show ? View.VISIBLE : View.GONE);
            if (show) scrollToBottom();
        }
    }

    private void scrollToBottom() {
        chatScrollView.post(() -> chatScrollView.fullScroll(View.FOCUS_DOWN));
    }

    private static class MessageSegment {
        String content;
        boolean isCode;
        String language;

        MessageSegment(String content, boolean isCode, String language) {
            this.content = content;
            this.isCode = isCode;
            this.language = language;
        }
    }
}