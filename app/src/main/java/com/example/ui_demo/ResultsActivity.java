package com.example.ui_demo;

import android.annotation.SuppressLint;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import java.util.ArrayList;

public class ResultsActivity extends AppCompatActivity {

    private TextView tvResultTitle, tvScore, tvAccuracy, tvXPEarned, tvTotalXP;
    private TextView tvStreak, tvCoins, tvLevel, tvLevelProgress;
    private LinearLayout layoutBadges, layoutLevelUps;
    private RecyclerView rvAnswerDetails;
    private Button btnReturnHome, btnViewDashboard;

    private String username;
    private JSONObject resultsData;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_results);

        username = getIntent().getStringExtra("userEmail");
        String resultsJson = getIntent().getStringExtra("results");

        initializeViews();
        parseResults(resultsJson);
    }

    private void initializeViews() {
        tvResultTitle = findViewById(R.id.tvResultTitle);
        tvScore = findViewById(R.id.tvScore);
        tvAccuracy = findViewById(R.id.tvAccuracy);
        tvXPEarned = findViewById(R.id.tvXPEarned);
        tvTotalXP = findViewById(R.id.tvTotalXP);
        tvStreak = findViewById(R.id.tvStreak);
        tvCoins = findViewById(R.id.tvCoins);
        tvLevel = findViewById(R.id.tvLevel);
        tvLevelProgress = findViewById(R.id.tvLevelProgress);
        layoutBadges = findViewById(R.id.layoutBadges);
        layoutLevelUps = findViewById(R.id.layoutLevelUps);
        rvAnswerDetails = findViewById(R.id.rvAnswerDetails);
        btnReturnHome = findViewById(R.id.btnReturnHome);
        btnViewDashboard = findViewById(R.id.btnViewDashboard);

        btnReturnHome.setOnClickListener(v -> returnHome());
        btnViewDashboard.setOnClickListener(v -> viewDashboard());
    }

    private void parseResults(String resultsJson) {
        try {
            JSONObject response = new JSONObject(resultsJson);
            resultsData = response.getJSONObject("response");

            if (!resultsData.getBoolean("success")) {
                return;
            }

            displaySummary();
            displayBadges();
            displayLevelUps();
            displayAnswerDetails();

        } catch (JSONException e) {
            e.printStackTrace();
        }
    }

    private void displaySummary() throws JSONException {
        int sessionCorrect = resultsData.getInt("session_correct");
        int totalQuestions = resultsData.getInt("total_questions");
        double accuracy = resultsData.getDouble("accuracy");
        int sessionXP = resultsData.getInt("session_xp");
        int totalXP = resultsData.getInt("total_xp");
        int streak = resultsData.getInt("current_streak");
        int coins = resultsData.getInt("coins");
        int level = resultsData.getInt("level");
        String title = resultsData.getString("title");
        double levelProgress = resultsData.getDouble("level_progress");

        // Set result title based on accuracy
        String resultTitle;
        if (accuracy >= 90) {
            resultTitle = "🌟 Outstanding Performance!";
        } else if (accuracy >= 70) {
            resultTitle = "🎯 Great Job!";
        } else if (accuracy >= 50) {
            resultTitle = "👍 Good Effort!";
        } else {
            resultTitle = "💪 Keep Practicing!";
        }
        tvResultTitle.setText(resultTitle);

        tvScore.setText(sessionCorrect + " / " + totalQuestions);
        tvAccuracy.setText(String.format("%.1f%%", accuracy));
        tvXPEarned.setText("+" + sessionXP + " XP");
        tvTotalXP.setText("Total: " + totalXP + " XP");
        tvStreak.setText("🔥 " + streak);
        tvCoins.setText("💰 " + coins);
        tvLevel.setText("Level " + level + " - " + title);
        tvLevelProgress.setText(String.format("%.1f%% to next level", levelProgress));
    }

    private void displayBadges() throws JSONException {
        JSONArray newBadges = resultsData.getJSONArray("new_badges");

        if (newBadges.length() == 0) {
            layoutBadges.setVisibility(View.GONE);
            return;
        }

        layoutBadges.setVisibility(View.VISIBLE);

        for (int i = 0; i < newBadges.length(); i++) {
            JSONObject badge = newBadges.getJSONObject(i);

            View badgeView = getLayoutInflater().inflate(R.layout.item_badge_earned, layoutBadges, false);

            TextView tvBadgeName = badgeView.findViewById(R.id.tvBadgeName);
            TextView tvBadgeDesc = badgeView.findViewById(R.id.tvBadgeDesc);
            TextView tvBadgeReward = badgeView.findViewById(R.id.tvBadgeReward);

            tvBadgeName.setText(badge.getString("icon") + " " + badge.getString("name"));
            tvBadgeDesc.setText(badge.getString("description"));
            tvBadgeReward.setText("+" + badge.getInt("xp_reward") + " XP, +" +
                    badge.getInt("coins_reward") + " Coins");

            layoutBadges.addView(badgeView);
        }
    }

    private void displayLevelUps() throws JSONException {
        JSONArray levelUps = resultsData.getJSONArray("level_ups");

        if (levelUps.length() == 0) {
            layoutLevelUps.setVisibility(View.GONE);
            return;
        }

        layoutLevelUps.setVisibility(View.VISIBLE);

        for (int i = 0; i < levelUps.length(); i++) {
            JSONObject levelUp = levelUps.getJSONObject(i);

            View levelUpView = getLayoutInflater().inflate(R.layout.item_level_up, layoutLevelUps, false);

            TextView tvLevelUpText = levelUpView.findViewById(R.id.tvLevelUpText);

            String text = "🎉 Level Up! You're now Level " +
                    levelUp.getInt("new_level") + " - " + levelUp.getString("new_title") +
                    "\n+100 Bonus Coins!";

            tvLevelUpText.setText(text);
            layoutLevelUps.addView(levelUpView);
        }
    }

    private void displayAnswerDetails() throws JSONException {
        JSONArray answers = resultsData.getJSONArray("answers");
        ArrayList<JSONObject> answerList = new ArrayList<>();

        for (int i = 0; i < answers.length(); i++) {
            answerList.add(answers.getJSONObject(i));
        }

        AnswerDetailsAdapter adapter = new AnswerDetailsAdapter(answerList);
        rvAnswerDetails.setLayoutManager(new LinearLayoutManager(this));
        rvAnswerDetails.setAdapter(adapter);
    }

    private void returnHome() {
        Intent intent = new Intent(ResultsActivity.this, Agent3Activity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
        startActivity(intent);
        finish();
    }

    private void viewDashboard() {
        Intent intent = new Intent(ResultsActivity.this, DashBoard3.class);
        intent.putExtra("username", username);
        startActivity(intent);
        finish();
    }
}