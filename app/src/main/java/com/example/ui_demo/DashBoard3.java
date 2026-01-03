package com.example.ui_demo;

import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.android.volley.Request;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.Volley;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

public class DashBoard3 extends AppCompatActivity {

    private TextView tvUsername, tvLevel, tvTitle, tvTotalXP, tvCoins;
    private TextView tvCurrentStreak, tvBestStreak, tvBadgesEarned;
    private TextView tvAccuracy, tvTotalQuestions, tvTotalCorrect;
    private TextView tvDailyQuestions, tvTopicsMastered, tvLevelProgress;
    private ProgressBar progressBar, progressLevel;
    private LinearLayout layoutRecentBadges, layoutTopTopics;

    private String username;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_dashboard3);

        username = getIntent().getStringExtra("userEmail");

        initializeViews();
        fetchDashboardData();
    }

    private void initializeViews() {
        tvUsername = findViewById(R.id.tvUsername);
        tvLevel = findViewById(R.id.tvLevel);
        tvTitle = findViewById(R.id.tvTitle);
        tvTotalXP = findViewById(R.id.tvTotalXP);
        tvCoins = findViewById(R.id.tvCoins);
        tvCurrentStreak = findViewById(R.id.tvCurrentStreak);
        tvBestStreak = findViewById(R.id.tvBestStreak);
        tvBadgesEarned = findViewById(R.id.tvBadgesEarned);
        tvAccuracy = findViewById(R.id.tvAccuracy);
        tvTotalQuestions = findViewById(R.id.tvTotalQuestions);
        tvTotalCorrect = findViewById(R.id.tvTotalCorrect);
        tvDailyQuestions = findViewById(R.id.tvDailyQuestions);
        tvTopicsMastered = findViewById(R.id.tvTopicsMastered);
        tvLevelProgress = findViewById(R.id.tvLevelProgress);
        progressBar = findViewById(R.id.progressBar);
        progressLevel = findViewById(R.id.progressLevel);
        layoutRecentBadges = findViewById(R.id.layoutRecentBadges);
        layoutTopTopics = findViewById(R.id.layoutTopTopics);

        tvUsername.setText("@" + username);
    }

    private void fetchDashboardData() {
        progressBar.setVisibility(View.VISIBLE);

        String url = "http://10.160.82.252:3000" + "/agent3";

        JSONObject requestBody = new JSONObject();
        try {
            requestBody.put("action", "dashboard");
            requestBody.put("user", username);
        } catch (JSONException e) {
            e.printStackTrace();
        }

        JsonObjectRequest request = new JsonObjectRequest(
                Request.Method.POST, url, requestBody,
                response -> {
                    progressBar.setVisibility(View.GONE);
                    parseDashboardData(response);
                },
                error -> {
                    progressBar.setVisibility(View.GONE);
                    Toast.makeText(this, "Error loading dashboard: " + error.getMessage(),
                            Toast.LENGTH_LONG).show();
                }
        );

        Volley.newRequestQueue(this).add(request);
    }

    private void parseDashboardData(JSONObject response) {
        try {
            JSONObject data = response.getJSONObject("data");

            // Level & Title
            tvLevel.setText("Level " + data.getInt("level"));
            tvTitle.setText(data.getString("title"));

            // XP & Coins
            tvTotalXP.setText(String.valueOf(data.getInt("total_xp")));
            tvCoins.setText(String.valueOf(data.getInt("coins")));

            // Streaks
            tvCurrentStreak.setText(String.valueOf(data.getInt("current_streak")));
            tvBestStreak.setText(String.valueOf(data.getInt("best_streak")));

            // Badges
            int badgesEarned = data.getInt("badges_earned");
            int totalBadges = data.getInt("total_badges");
            tvBadgesEarned.setText(badgesEarned + " / " + totalBadges);

            // Stats
            tvAccuracy.setText(data.getDouble("accuracy") + "%");
            tvTotalQuestions.setText(String.valueOf(data.getInt("total_questions")));
            tvTotalCorrect.setText(String.valueOf(data.getInt("total_correct")));
            tvDailyQuestions.setText(String.valueOf(data.getInt("daily_questions")));
            tvTopicsMastered.setText(String.valueOf(data.getInt("topics_mastered")));

            // Level Progress
            double levelProgress = data.getDouble("level_progress");
            tvLevelProgress.setText(String.format("%.1f%% to next level", levelProgress));
            progressLevel.setProgress((int) levelProgress);

            // Recent Badges
            JSONArray recentBadges = data.getJSONArray("recent_badges");
            displayRecentBadges(recentBadges);

            // Top Topics
            JSONArray topTopics = data.getJSONArray("top_topics");
            displayTopTopics(topTopics);

        } catch (JSONException e) {
            e.printStackTrace();
            Toast.makeText(this, "Error parsing dashboard data", Toast.LENGTH_SHORT).show();
        }
    }

    private void displayRecentBadges(JSONArray badges) throws JSONException {
        layoutRecentBadges.removeAllViews();

        if (badges.length() == 0) {
            TextView noBadges = new TextView(this);
            noBadges.setText("No badges earned yet. Keep playing!");
            noBadges.setTextSize(14);
            noBadges.setTextColor(getResources().getColor(android.R.color.darker_gray));
            layoutRecentBadges.addView(noBadges);
            return;
        }

        for (int i = 0; i < badges.length(); i++) {
            JSONObject badge = badges.getJSONObject(i);

            View badgeView = getLayoutInflater().inflate(R.layout.item_badge_small, layoutRecentBadges, false);
            TextView tvBadge = badgeView.findViewById(R.id.tvBadge);

            String badgeText = badge.getString("icon") + " " + badge.getString("name");
            tvBadge.setText(badgeText);

            layoutRecentBadges.addView(badgeView);
        }
    }

    private void displayTopTopics(JSONArray topics) throws JSONException {
        layoutTopTopics.removeAllViews();

        if (topics.length() == 0) {
            TextView noTopics = new TextView(this);
            noTopics.setText("No topics mastered yet. Start a quiz!");
            noTopics.setTextSize(14);
            noTopics.setTextColor(getResources().getColor(android.R.color.darker_gray));
            layoutTopTopics.addView(noTopics);
            return;
        }

        for (int i = 0; i < topics.length(); i++) {
            JSONObject topic = topics.getJSONObject(i);

            View topicView = getLayoutInflater().inflate(R.layout.item_topic, layoutTopTopics, false);
            TextView tvTopicName = topicView.findViewById(R.id.tvTopicName);
            TextView tvTopicCount = topicView.findViewById(R.id.tvTopicCount);

            tvTopicName.setText((i + 1) + ". " + topic.getString("topic"));
            tvTopicCount.setText(topic.getInt("count") + " questions");

            layoutTopTopics.addView(topicView);
        }
    }
}