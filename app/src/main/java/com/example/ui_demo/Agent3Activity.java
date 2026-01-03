package com.example.ui_demo;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.RadioGroup;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class Agent3Activity extends AppCompatActivity {

    private String userEmail;
    private EditText etQuizTopic, etNumQuestions;
    private RadioGroup rgQuestionType, rgDifficulty;
    private Button btnStartQuiz, btnViewDashboard, btnViewBadges;
    private TextView tvWelcomeMessage;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.agent3_activity_main);

        // Get user email from intent (passed from login)
        userEmail = getIntent().getStringExtra("userEmail");

        if (userEmail == null || userEmail.isEmpty()) {
            Toast.makeText(this, "User not logged in", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        initializeViews();
        setupWelcomeMessage();
        setupClickListeners();
    }

    private void initializeViews() {
        tvWelcomeMessage = findViewById(R.id.tvWelcomeMessage);
        etQuizTopic = findViewById(R.id.etQuizTopic);
        etNumQuestions = findViewById(R.id.etNumQuestions);
        rgQuestionType = findViewById(R.id.rgQuestionType);
        rgDifficulty = findViewById(R.id.rgDifficulty);
        btnStartQuiz = findViewById(R.id.btnStartQuiz);
        btnViewDashboard = findViewById(R.id.btnViewDashboard);
        btnViewBadges = findViewById(R.id.btnViewBadges);
    }

    private void setupWelcomeMessage() {
        String displayName = userEmail.split("@")[0];
        displayName = displayName.substring(0, 1).toUpperCase() + displayName.substring(1);
        tvWelcomeMessage.setText("Welcome back, " + displayName + "!");
    }

    private void setupClickListeners() {
        btnStartQuiz.setOnClickListener(v -> startQuiz());
        btnViewDashboard.setOnClickListener(v -> viewDashboard());
        btnViewBadges.setOnClickListener(v -> viewBadges());
    }

    private void startQuiz() {
        String topic = etQuizTopic.getText().toString().trim();
        String numQuestions = etNumQuestions.getText().toString().trim();

        if (topic.isEmpty()) {
            Toast.makeText(this, "Please enter a quiz topic", Toast.LENGTH_SHORT).show();
            etQuizTopic.requestFocus();
            return;
        }

        if (numQuestions.isEmpty()) {
            numQuestions = "5";
        }

        try {
            int num = Integer.parseInt(numQuestions);
            if (num <= 0 || num > 50) {
                Toast.makeText(this, "Please enter a number between 1 and 50", Toast.LENGTH_SHORT).show();
                return;
            }
        } catch (NumberFormatException e) {
            Toast.makeText(this, "Please enter a valid number", Toast.LENGTH_SHORT).show();
            return;
        }

        String questionType = getSelectedQuestionType();
        String difficulty = getSelectedDifficulty();
        String query = numQuestions + " " + difficulty + " " + questionType + " questions about " + topic;

        Intent intent = new Intent(Agent3Activity.this, QuizActivity.class);
        intent.putExtra("userEmail", userEmail);
        intent.putExtra("question", query);
        startActivity(intent);
    }

    private void viewDashboard() {
        Intent intent = new Intent(Agent3Activity.this, DashBoard3.class);
        intent.putExtra("userEmail", userEmail);
        startActivity(intent);
    }

    private void viewBadges() {
        Intent intent = new Intent(Agent3Activity.this, BadgesActivity.class);
        intent.putExtra("userEmail", userEmail);
        startActivity(intent);
    }

    private String getSelectedQuestionType() {
        int selectedId = rgQuestionType.getCheckedRadioButtonId();
        if (selectedId == R.id.rbMCQ) return "multiple choice";
        if (selectedId == R.id.rbTrueFalse) return "true false";
        if (selectedId == R.id.rbFillBlank) return "fill in blank";
        if (selectedId == R.id.rbShortAnswer) return "short answer";
        if (selectedId == R.id.rbMixed) return "mixed";
        return "multiple choice";
    }

    private String getSelectedDifficulty() {
        int selectedId = rgDifficulty.getCheckedRadioButtonId();
        if (selectedId == R.id.rbEasy) return "easy";
        if (selectedId == R.id.rbMedium) return "medium";
        if (selectedId == R.id.rbHard) return "hard";
        if (selectedId == R.id.rbExpert) return "expert";
        return "medium";
    }
}