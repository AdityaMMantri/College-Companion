package com.example.ui_demo.ui.dashboard;

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
import java.util.Iterator;

public class BadgesActivity extends AppCompatActivity {

    private TextView tvBadgesTitle, tvCompletionPercentage;
    private ProgressBar progressBar, progressCompletion;
    private LinearLayout layoutBadgeCategories;

    private String username;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_badges);

        username = getIntent().getStringExtra("userEmail");

        initializeViews();
        fetchBadgesData();
    }

    private void initializeViews() {
        tvBadgesTitle = findViewById(R.id.tvBadgesTitle);
        tvCompletionPercentage = findViewById(R.id.tvCompletionPercentage);
        progressBar = findViewById(R.id.progressBar);
        progressCompletion = findViewById(R.id.progressCompletion);
        layoutBadgeCategories = findViewById(R.id.layoutBadgeCategories);
    }

    private void fetchBadgesData() {
        progressBar.setVisibility(View.VISIBLE);

        String url = "http://10.160.82.252:3000" + "/agent3";

        JSONObject requestBody = new JSONObject();
        try {
            requestBody.put("action", "badges");
            requestBody.put("user", username);
        } catch (JSONException e) {
            e.printStackTrace();
        }

        JsonObjectRequest request = new JsonObjectRequest(
                Request.Method.POST, url, requestBody,
                response -> {
                    progressBar.setVisibility(View.GONE);
                    parseBadgesData(response);
                },
                error -> {
                    progressBar.setVisibility(View.GONE);
                    Toast.makeText(this, "Error loading badges: " + error.getMessage(),
                            Toast.LENGTH_LONG).show();
                }
        );

        Volley.newRequestQueue(this).add(request);
    }

    private void parseBadgesData(JSONObject response) {
        try {
            JSONObject data = response.getJSONObject("data");

            int earnedCount = data.getInt("earned_count");
            int totalCount = data.getInt("total_count");
            double completionPercentage = data.getDouble("completion_percentage");

            tvBadgesTitle.setText("Badges: " + earnedCount + " / " + totalCount);
            tvCompletionPercentage.setText(String.format("%.1f%% Complete", completionPercentage));
            progressCompletion.setProgress((int) completionPercentage);

            JSONObject categories = data.getJSONObject("categories");
            displayBadgeCategories(categories);

        } catch (JSONException e) {
            e.printStackTrace();
            Toast.makeText(this, "Error parsing badges data", Toast.LENGTH_SHORT).show();
        }
    }

    private void displayBadgeCategories(JSONObject categories) throws JSONException {
        layoutBadgeCategories.removeAllViews();

        Iterator<String> categoryKeys = categories.keys();

        while (categoryKeys.hasNext()) {
            String categoryName = categoryKeys.next();
            JSONArray badges = categories.getJSONArray(categoryName);

            // Add category header
            View categoryHeader = getLayoutInflater().inflate(
                    R.layout.item_badge_category_header, layoutBadgeCategories, false);
            TextView tvCategoryName = categoryHeader.findViewById(R.id.tvCategoryName);
            tvCategoryName.setText(getCategoryIcon(categoryName) + " " +
                    categoryName.toUpperCase());
            layoutBadgeCategories.addView(categoryHeader);

            // Add badges in this category
            for (int i = 0; i < badges.length(); i++) {
                JSONObject badge = badges.getJSONObject(i);
                displayBadge(badge);
            }
        }
    }

    private void displayBadge(JSONObject badge) throws JSONException {
        View badgeView = getLayoutInflater().inflate(
                R.layout.item_badge_detail, layoutBadgeCategories, false);

        TextView tvBadgeName = badgeView.findViewById(R.id.tvBadgeName);
        TextView tvBadgeDesc = badgeView.findViewById(R.id.tvBadgeDesc);
        TextView tvBadgeRewards = badgeView.findViewById(R.id.tvBadgeRewards);
        TextView tvBadgeRarity = badgeView.findViewById(R.id.tvBadgeRarity);
        View badgeOverlay = badgeView.findViewById(R.id.badgeOverlay);

        boolean earned = badge.getBoolean("earned");
        String name = badge.getString("name");
        String description = badge.getString("description");
        String rarity = badge.getString("rarity");
        int xpReward = badge.getInt("xp_reward");
        int coinsReward = badge.getInt("coins_reward");

        tvBadgeName.setText(name);
        tvBadgeDesc.setText(description);
        tvBadgeRewards.setText("Rewards: " + xpReward + " XP, " + coinsReward + " Coins");
        tvBadgeRarity.setText(getRarityIcon(rarity) + " " + rarity.toUpperCase());

        // Apply rarity color
        int rarityColor = getRarityColor(rarity);
        badgeView.setBackgroundColor(rarityColor);

        // If not earned, show as locked
        if (!earned) {
            badgeOverlay.setVisibility(View.VISIBLE);
            tvBadgeName.setAlpha(0.5f);
            tvBadgeDesc.setAlpha(0.5f);
            tvBadgeRewards.setAlpha(0.5f);
            tvBadgeRarity.setAlpha(0.5f);
        } else {
            badgeOverlay.setVisibility(View.GONE);
            tvBadgeName.setAlpha(1.0f);
            tvBadgeDesc.setAlpha(1.0f);
            tvBadgeRewards.setAlpha(1.0f);
            tvBadgeRarity.setAlpha(1.0f);
        }

        layoutBadgeCategories.addView(badgeView);
    }

    private String getCategoryIcon(String category) {
        switch (category.toLowerCase()) {
            case "achievement": return "🎯";
            case "streak": return "🔥";
            case "speed": return "⚡";
            case "mastery": return "🎓";
            case "progression": return "⭐";
            case "special": return "✨";
            case "legendary": return "👑";
            default: return "🏆";
        }
    }

    private String getRarityIcon(String rarity) {
        switch (rarity.toLowerCase()) {
            case "common": return "⚪";
            case "rare": return "🔵";
            case "epic": return "🟣";
            case "legendary": return "🟡";
            default: return "⚪";
        }
    }

    private int getRarityColor(String rarity) {
        switch (rarity.toLowerCase()) {
            case "common": return 0xFFECF0F1; // Light gray
            case "rare": return 0xFF3498DB; // Blue
            case "epic": return 0xFF9B59B6; // Purple
            case "legendary": return 0xFFF39C12; // Gold
            default: return 0xFFFFFFFF;
        }
    }
}
