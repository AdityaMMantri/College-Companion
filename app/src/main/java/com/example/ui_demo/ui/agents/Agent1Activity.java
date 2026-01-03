package com.example.ui_demo.ui.agents;

import androidx.appcompat.app.AppCompatActivity;
import android.os.Bundle;
import android.text.Html;
import android.view.Gravity;
import android.view.View;
import android.widget.*;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

public class Agent1Activity extends AppCompatActivity {

    private LinearLayout chatContainer;
    private EditText messageInput;
    private Button sendButton;
    private String userEmail;
    private ScrollView mainScroll;

    // keep recent chat messages in memory (simple)
    private final List<String> chatBuffer = new ArrayList<>();
    private final int CHAT_LIMIT = 50;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_agent1_chat);

        chatContainer = findViewById(R.id.chatContainer);
        messageInput = findViewById(R.id.messageInput);
        sendButton = findViewById(R.id.sendButton);
        mainScroll = findViewById(R.id.mainScroll);

        userEmail = getIntent().getStringExtra("userEmail");
        if (userEmail == null) userEmail = "android_user";

        sendButton.setOnClickListener(v -> {
            String q = messageInput.getText().toString().trim();
            if (q.isEmpty()) {
                Toast.makeText(this, "Type a message", Toast.LENGTH_SHORT).show();
                return;
            }
            messageInput.setText("");
            addChatBubble(q, true);
            sendToAgent(q);
        });
    }

    private void sendToAgent(String question) {
        new Thread(() -> {
            try {
                JSONObject json = new JSONObject();
                json.put("user", userEmail);
                json.put("question", question);
                String res = ApiClient.post("/agent1", json.toString());
                JSONObject resObj = new JSONObject(res);
                String responseText = resObj.optString("response", "");

                runOnUiThread(() -> {
                    // If it's a timetable request, open TimetableActivity instead of a chat bubble
                    if (looksLikeTimetable(responseText) && shouldOpenTimetable(question)) {
                        // launch TimetableActivity, passing raw response and userEmail
                        android.content.Intent i = new android.content.Intent(Agent1Activity.this, TimetableActivity.class);
                        i.putExtra("rawTimetable", responseText);
                        i.putExtra("userEmail", userEmail);
                        startActivity(i);
                    } else {
                        addChatBubble(responseText, false);
                    }
                });

            } catch (Exception e) {
                runOnUiThread(() -> addChatBubble("Error: " + e.getMessage(), false));
            }
        }).start();
    }

    // Heuristic: open timetable when user explicitly asked to see it (e.g. "show timetable")
    private boolean shouldOpenTimetable(String userQuestion) {
        if (userQuestion == null) return false;
        String q = userQuestion.toLowerCase();
        return q.contains("show timetable") || q.contains("show my timetable") || q.contains("show schedule") || q.contains("show time");
    }

    // small heuristic to detect timetable-ish text
    private boolean looksLikeTimetable(String s) {
        if (s == null) return false;
        if (s.contains("|")) return true;
        if (Pattern.compile("^\\s*\\*\\s+", Pattern.MULTILINE).matcher(s).find()) return true;
        if (Pattern.compile("\\d{2}:\\d{2}[-–]\\d{2}:\\d{2}").matcher(s).find()) return true;
        return false;
    }

    // Add a chat bubble to the chatContainer
    private void addChatBubble(String text, boolean isUser) {
        // keep buffer
        if (chatBuffer.size() >= CHAT_LIMIT) chatBuffer.remove(0);
        chatBuffer.add((isUser ? "You: " : "AI: ") + text);

        // Rebuild the visible chat area from buffer (simple)
        chatContainer.removeAllViews();
        for (String msg : chatBuffer) {
            TextView tv = new TextView(this);
            boolean fromUser = msg.startsWith("You:");
            String display = msg.substring(msg.indexOf(':') + 1).trim();

            // simple HTML formatting (preserve line breaks)
            tv.setText(Html.fromHtml(display.replace("\n", "<br/>")));
            tv.setTextSize(15);
            tv.setPadding(24, 18, 24, 18);
            tv.setTextColor(fromUser ? 0xFFFFFFFF : 0xFF212121);

            // Create card-like appearance
            android.graphics.drawable.GradientDrawable drawable = new android.graphics.drawable.GradientDrawable();
            drawable.setCornerRadius(20f);

            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
            );
            lp.setMargins(16, 8, 16, 8);

            if (fromUser) {
                // User bubble - right aligned, purple gradient
                lp.gravity = Gravity.END;
                drawable.setColors(new int[]{0xFF6200EE, 0xFF7C4DFF}); // Purple gradient
                drawable.setGradientType(android.graphics.drawable.GradientDrawable.LINEAR_GRADIENT);
                drawable.setOrientation(android.graphics.drawable.GradientDrawable.Orientation.LEFT_RIGHT);
                tv.setMaxWidth((int)(getResources().getDisplayMetrics().widthPixels * 0.75));
                tv.setElevation(4f);
            } else {
                // AI bubble - left aligned, white with shadow
                lp.gravity = Gravity.START;
                drawable.setColor(0xFFFFFFFF);
                drawable.setStroke(2, 0xFFE0E0E0); // Light border
                tv.setMaxWidth((int)(getResources().getDisplayMetrics().widthPixels * 0.80));
                tv.setElevation(2f);
            }

            tv.setBackground(drawable);
            tv.setLayoutParams(lp);
            chatContainer.addView(tv);

            // Add some spacing between messages
            View spacer = new View(this);
            LinearLayout.LayoutParams spacerParams = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, 4);
            spacer.setLayoutParams(spacerParams);
            chatContainer.addView(spacer);
        }

        // scroll to bottom
        mainScroll.post(() -> mainScroll.fullScroll(View.FOCUS_DOWN));
    }
}
