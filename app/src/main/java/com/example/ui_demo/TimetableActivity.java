package com.example.ui_demo;

import androidx.appcompat.app.AppCompatActivity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.*;
import com.google.android.material.floatingactionbutton.FloatingActionButton;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class TimetableActivity extends AppCompatActivity {

    private LinearLayout timetableContainer;
    private String rawTimetable;
    private String userEmail;
    private ScrollView mainScroll;
    private FloatingActionButton fabRefresh;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_timetable);

        timetableContainer = findViewById(R.id.timetableContainer);
        mainScroll = findViewById(R.id.ttScroll);
        fabRefresh = findViewById(R.id.fabRefresh);

        rawTimetable = getIntent().getStringExtra("rawTimetable");
        userEmail = getIntent().getStringExtra("userEmail");
        if (userEmail == null) userEmail = "android_user";

        // Refresh button
        fabRefresh.setOnClickListener(v -> refreshTimetable());

        // initial render
        displayParsedTimetable(rawTimetable);
    }

    /**
     * Enhanced parsing with multiple fallback strategies
     */
    private void displayParsedTimetable(String rawText) {
        timetableContainer.removeAllViews();

        if (rawText == null || rawText.trim().isEmpty()) {
            addEmptyState();
            return;
        }

        List<TimetableBlock> blocks = new ArrayList<>();

        // Strategy 1: Try PIPE format (most reliable)
        blocks = parsePipeFormat(rawText);

        // Strategy 2: Try BULLET format
        if (blocks.isEmpty()) {
            blocks = parseBulletFormat(rawText);
        }

        // Strategy 3: Try simple line-by-line parsing
        if (blocks.isEmpty()) {
            blocks = parseSimpleFormat(rawText);
        }

        if (blocks.isEmpty()) {
            // Show raw text in a nice format
            addInfoCard("Could not parse timetable format", rawText);
            return;
        }

        // Render blocks (cards)
        for (TimetableBlock b : blocks) {
            addTimetableCard(b);
        }

        mainScroll.post(() -> mainScroll.smoothScrollTo(0, 0));
    }

    /**
     * Parse PIPE format: Time | Duration | Type | Task | id=xxx
     * CRITICAL: Preserve exact values, don't modify anything
     */
    private List<TimetableBlock> parsePipeFormat(String text) {
        List<TimetableBlock> blocks = new ArrayList<>();

        // More precise regex that captures EXACT content between pipes
        Pattern pipe = Pattern.compile(
                "([^|]+)\\|([^|]+)\\|([^|]+)\\|([^|]+)\\|\\s*id\\s*=\\s*([A-Za-z0-9_\\-]+)",
                Pattern.MULTILINE);

        Matcher m = pipe.matcher(text);
        while (m.find()) {
            String time = m.group(1).trim();
            String duration = m.group(2).trim();
            String type = m.group(3).trim();
            String taskRaw = m.group(4).trim();
            String id = m.group(5).trim();

            // Remove ONLY emojis from task, keep everything else
            String task = taskRaw.replaceAll("[📚🎓☕🏃🍽️👤📌🗑️✅❌⏰🔥💪🎯]+", "").trim();

            // DON'T modify time, duration, type, or id - use them AS-IS
            blocks.add(new TimetableBlock(task, time, duration, type, id));
        }

        return blocks;
    }

    /**
     * Parse BULLET format: * HH:MM-HH:MM: Task (type)
     * CRITICAL: Preserve exact values
     */
    private List<TimetableBlock> parseBulletFormat(String text) {
        List<TimetableBlock> blocks = new ArrayList<>();

        Pattern bullet = Pattern.compile(
                "[*•-]\\s*([^\\n]+)",
                Pattern.MULTILINE);

        Matcher m = bullet.matcher(text);
        int idc = 1;
        while (m.find()) {
            String line = m.group(1).trim();

            // Try to extract time pattern: HH:MM - HH:MM or HH:MM-HH:MM
            Pattern timePattern = Pattern.compile(
                    "(\\d{1,2}:\\d{2})\\s*[-–]\\s*(\\d{1,2}:\\d{2})\\s*:?\\s*(.+)",
                    Pattern.CASE_INSENSITIVE);

            Matcher timeMatcher = timePattern.matcher(line);
            if (timeMatcher.find()) {
                String start = timeMatcher.group(1).trim();
                String end = timeMatcher.group(2).trim();
                String rest = timeMatcher.group(3).trim();

                // Keep the EXACT time as given
                String time = start + "–" + end;
                String duration = getDurationMinutes(start, end);

                // Extract task and type if present
                String task = rest;
                String type = "task";

                // Check for type in parentheses
                Pattern typePattern = Pattern.compile("(.+?)\\s*\\(([^)]+)\\)");
                Matcher typeMatcher = typePattern.matcher(rest);
                if (typeMatcher.find()) {
                    task = typeMatcher.group(1).trim();
                    type = typeMatcher.group(2).trim();
                }

                blocks.add(new TimetableBlock(task, time, duration, type, "auto_" + (idc++)));
            }
        }

        return blocks;
    }

    /**
     * Parse simple format: lines with time and task
     */
    private List<TimetableBlock> parseSimpleFormat(String text) {
        List<TimetableBlock> blocks = new ArrayList<>();

        // Match lines like: "09:00-10:30 Study Math"
        Pattern simple = Pattern.compile(
                "(\\d{1,2}:\\d{2})\\s*[-–]\\s*(\\d{1,2}:\\d{2})\\s+(.+)",
                Pattern.MULTILINE);

        Matcher m = simple.matcher(text);
        int idc = 1;
        while (m.find()) {
            String start = m.group(1).trim();
            String end = m.group(2).trim();
            String task = m.group(3).trim();

            String time = start + "–" + end;
            String duration = getDurationMinutes(start, end);
            String type = guessType(task);

            blocks.add(new TimetableBlock(task, time, duration, type, "auto_" + (idc++)));
        }

        return blocks;
    }

    /**
     * Guess block type from task name
     */
    private String guessType(String task) {
        String lower = task.toLowerCase();
        if (lower.contains("study") || lower.contains("read")) return "study";
        if (lower.contains("class") || lower.contains("lecture") || lower.contains("lab")) return "class";
        if (lower.contains("break") || lower.contains("rest")) return "break";
        if (lower.contains("lunch") || lower.contains("dinner") || lower.contains("breakfast")) return "meal";
        if (lower.contains("exercise") || lower.contains("gym") || lower.contains("workout")) return "exercise";
        return "task";
    }

    /**
     * Add timetable card - PRESERVE EXACT CONTENT
     */
    private void addTimetableCard(TimetableBlock b) {
        View card = LayoutInflater.from(this).inflate(R.layout.card_timetable, timetableContainer, false);

        TextView txtTask = card.findViewById(R.id.txt_task);
        TextView txtTime = card.findViewById(R.id.txt_time);
        TextView txtDuration = card.findViewById(R.id.txt_duration);
        TextView txtType = card.findViewById(R.id.txt_type);
        TextView txtId = card.findViewById(R.id.txt_id);
        TextView txtTypeIcon = card.findViewById(R.id.txt_type_icon);
        TextView btnRemove = card.findViewById(R.id.btn_remove);
        View colorIndicator = card.findViewById(R.id.colorIndicator);

        // Set content EXACTLY as received - NO MODIFICATIONS
        txtTask.setText(b.task);
        txtTime.setText(b.time);  // ← KEEP EXACT TIME FROM SERVER
        txtDuration.setText(b.duration != null ? b.duration : "");

        // Store ID internally but don't show it
        txtId.setText(b.id);
        txtId.setVisibility(View.GONE);

        // Set icon and color based on type
        Map<String, String> iconMap = new HashMap<>();
        iconMap.put("study", "📚");
        iconMap.put("class", "🎓");
        iconMap.put("break", "☕");
        iconMap.put("meal", "🍽️");
        iconMap.put("exercise", "🏃");
        iconMap.put("personal", "👤");
        iconMap.put("task", "📌");

        Map<String, Integer> colorMap = new HashMap<>();
        colorMap.put("study", Color.parseColor("#6200EE"));
        colorMap.put("class", Color.parseColor("#1976D2"));
        colorMap.put("break", Color.parseColor("#00897B"));
        colorMap.put("meal", Color.parseColor("#F57C00"));
        colorMap.put("exercise", Color.parseColor("#C62828"));
        colorMap.put("personal", Color.parseColor("#7B1FA2"));
        colorMap.put("task", Color.parseColor("#455A64"));

        String typeLower = b.type.toLowerCase();
        String icon = iconMap.getOrDefault(typeLower, "📌");
        int color = colorMap.getOrDefault(typeLower, Color.parseColor("#6200EE"));

        txtTypeIcon.setText(icon);
        txtType.setText(b.type.toUpperCase());

        // Set colored indicator bar
        colorIndicator.setBackgroundColor(color);

        // Handle remove button
        if (b.id != null && b.id.startsWith("auto_")) {
            btnRemove.setEnabled(false);
            btnRemove.setText("🔒 No ID");
            btnRemove.setTextColor(Color.parseColor("#BDBDBD"));
            btnRemove.setOnClickListener(v ->
                    Toast.makeText(this, "Ask agent to show timetable for server IDs", Toast.LENGTH_SHORT).show());
        } else {
            btnRemove.setEnabled(true);
            btnRemove.setText("🗑️ Remove");
            btnRemove.setTextColor(Color.parseColor("#EF5350"));
            btnRemove.setOnClickListener(v -> {
                // Show confirmation
                new android.app.AlertDialog.Builder(this)
                        .setTitle("Remove Block")
                        .setMessage("Remove " + b.task + "?")
                        .setPositiveButton("Remove", (dialog, which) -> performRemoveAndRefresh(b.id))
                        .setNegativeButton("Cancel", null)
                        .show();
            });
        }

        timetableContainer.addView(card);
    }

    /**
     * Refresh timetable from server
     */
    private void refreshTimetable() {
        Toast.makeText(this, "Refreshing timetable...", Toast.LENGTH_SHORT).show();
        timetableContainer.removeAllViews();
        addLoadingState();

        new Thread(() -> {
            try {
                JSONObject json = new JSONObject();
                json.put("user", userEmail);
                json.put("question", "show timetable");
                String res = ApiClient.post("/agent1", json.toString());
                JSONObject resObj = new JSONObject(res);
                String tableRaw = resObj.optString("response", "");

                runOnUiThread(() -> {
                    Toast.makeText(this, "Refreshed!", Toast.LENGTH_SHORT).show();
                    displayParsedTimetable(tableRaw);
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    Toast.makeText(this, "Refresh failed: " + e.getMessage(), Toast.LENGTH_LONG).show();
                    displayParsedTimetable(rawTimetable);
                });
            }
        }).start();
    }

    /**
     * Remove block and refresh
     */
    private void performRemoveAndRefresh(String id) {
        Toast.makeText(this, "Removing...", Toast.LENGTH_SHORT).show();

        new Thread(() -> {
            try {
                JSONObject json = new JSONObject();
                json.put("user", userEmail);
                json.put("question", "remove id=" + id);
                ApiClient.post("/agent1", json.toString());

                // Refresh
                JSONObject showJson = new JSONObject();
                showJson.put("user", userEmail);
                showJson.put("question", "show timetable");
                String showRes = ApiClient.post("/agent1", showJson.toString());
                JSONObject showObj = new JSONObject(showRes);
                String tableRaw = showObj.optString("response", "");

                runOnUiThread(() -> {
                    Toast.makeText(this, "Removed successfully!", Toast.LENGTH_SHORT).show();
                    displayParsedTimetable(tableRaw);
                });
            } catch (Exception e) {
                runOnUiThread(() ->
                        Toast.makeText(this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show());
            }
        }).start();
    }

    /**
     * Show empty state
     */
    private void addEmptyState() {
        TextView tv = new TextView(this);
        tv.setText("📭\n\nNo timetable yet\n\nChat with the agent to create your schedule");
        tv.setTextSize(16);
        tv.setTextColor(0xFF757575);
        tv.setGravity(android.view.Gravity.CENTER);
        tv.setPadding(40, 100, 40, 100);
        timetableContainer.addView(tv);
    }

    /**
     * Show loading state
     */
    private void addLoadingState() {
        ProgressBar pb = new ProgressBar(this);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(100, 100);
        lp.gravity = android.view.Gravity.CENTER;
        lp.setMargins(0, 100, 0, 100);
        pb.setLayoutParams(lp);
        timetableContainer.addView(pb);
    }

    /**
     * Show info card for unparseable content
     */
    private void addInfoCard(String title, String content) {
        androidx.cardview.widget.CardView card = new androidx.cardview.widget.CardView(this);
        card.setCardElevation(4f);
        card.setRadius(16f);
        card.setCardBackgroundColor(0xFFFFF3E0);
        LinearLayout.LayoutParams cardParams = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        cardParams.setMargins(0, 0, 0, 16);
        card.setLayoutParams(cardParams);

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(24, 24, 24, 24);

        TextView titleTv = new TextView(this);
        titleTv.setText("⚠️ " + title);
        titleTv.setTextSize(16);
        titleTv.setTypeface(null, android.graphics.Typeface.BOLD);
        titleTv.setTextColor(0xFFE65100);
        layout.addView(titleTv);

        TextView contentTv = new TextView(this);
        contentTv.setText(content);
        contentTv.setTextSize(13);
        contentTv.setTextColor(0xFF616161);
        contentTv.setPadding(0, 12, 0, 0);
        layout.addView(contentTv);

        card.addView(layout);
        timetableContainer.addView(card);
    }

    /**
     * Calculate duration between two times
     */
    private String getDurationMinutes(String start, String end) {
        try {
            String[] s = start.split(":");
            String[] e = end.split(":");
            int sh = Integer.parseInt(s[0]);
            int sm = Integer.parseInt(s[1]);
            int eh = Integer.parseInt(e[0]);
            int em = Integer.parseInt(e[1]);
            int mins = (eh * 60 + em) - (sh * 60 + sm);
            if (mins < 0) mins += 24 * 60; // Handle overnight
            return mins + "min";
        } catch (Exception ex) {
            return "";
        }
    }

    private static class TimetableBlock {
        String task, time, duration, type, id;
        TimetableBlock(String task, String time, String duration, String type, String id) {
            this.task = task;
            this.time = time;
            this.duration = duration;
            this.type = type;
            this.id = id;
        }
    }
}