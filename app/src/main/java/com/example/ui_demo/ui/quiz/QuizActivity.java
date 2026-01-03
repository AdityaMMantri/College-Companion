package com.example.ui_demo.ui.quiz;

import android.content.Intent;
import android.os.Bundle;
import android.os.SystemClock;
import android.util.Log;
import android.view.View;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import com.android.volley.*;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.Volley;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

public class QuizActivity extends AppCompatActivity {

    private static final String TAG = "QuizActivity";

    private TextView tvQuestionNumber, tvQuestion, tvStreak, tvLevel;
    private RadioGroup rgOptions;
    private RadioButton rbOptionA, rbOptionB, rbOptionC, rbOptionD;
    private EditText etAnswer;
    private Button btnSubmit, btnNext;
    private ProgressBar progressBar;
    private LinearLayout layoutOptions, layoutTextAnswer;

    private String username;
    private ArrayList<JSONObject> questions;
    private ArrayList<JSONObject> answers;
    private int currentQuestionIndex = 0;
    private long questionStartTime;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_quiz);

        username = getIntent().getStringExtra("userEmail");
        String question = getIntent().getStringExtra("question");

        Log.d(TAG, "Username: " + username);
        Log.d(TAG, "Question Query: " + question);

        initializeViews();
        fetchQuestions(question);
    }

    private void initializeViews() {
        tvQuestionNumber = findViewById(R.id.tvQuestionNumber);
        tvQuestion = findViewById(R.id.tvQuestion);
        tvStreak = findViewById(R.id.tvStreak);
        tvLevel = findViewById(R.id.tvLevel);
        rgOptions = findViewById(R.id.rgOptions);
        rbOptionA = findViewById(R.id.rbOptionA);
        rbOptionB = findViewById(R.id.rbOptionB);
        rbOptionC = findViewById(R.id.rbOptionC);
        rbOptionD = findViewById(R.id.rbOptionD);
        etAnswer = findViewById(R.id.etAnswer);
        btnSubmit = findViewById(R.id.btnSubmit);
        btnNext = findViewById(R.id.btnNext);
        progressBar = findViewById(R.id.progressBar);
        layoutOptions = findViewById(R.id.layoutOptions);
        layoutTextAnswer = findViewById(R.id.layoutTextAnswer);

        questions = new ArrayList<>();
        answers = new ArrayList<>();

        btnSubmit.setOnClickListener(v -> submitAnswer());
        btnNext.setOnClickListener(v -> loadNextQuestion());
    }

    private void fetchQuestions(String question) {
        progressBar.setVisibility(View.VISIBLE);
        tvQuestion.setText("Generating questions... Please wait...");

        String url = ApiConfig.getAgent3Url();
        Log.d(TAG, "API URL: " + url);

        JSONObject requestBody = new JSONObject();
        try {
            requestBody.put("action", "generate_quiz");
            requestBody.put("user", username);
            requestBody.put("question", question);

            Log.d(TAG, "Request Body: " + requestBody.toString());
        } catch (JSONException e) {
            Log.e(TAG, "Error creating request", e);
            e.printStackTrace();
        }

        JsonObjectRequest request = new JsonObjectRequest(
                Request.Method.POST, url, requestBody,
                response -> {
                    Log.d(TAG, "Raw Response: " + response.toString());
                    progressBar.setVisibility(View.GONE);
                    parseQuizResponse(response);
                },
                error -> {
                    progressBar.setVisibility(View.GONE);
                    String errorMsg = "Error fetching questions";

                    if (error.networkResponse != null) {
                        errorMsg += " (Code: " + error.networkResponse.statusCode + ")";
                        try {
                            String responseBody = new String(error.networkResponse.data, "utf-8");
                            Log.e(TAG, "Error Response: " + responseBody);
                        } catch (Exception e) {
                            Log.e(TAG, "Error reading response", e);
                        }
                    } else if (error instanceof NoConnectionError) {
                        errorMsg = "No internet connection";
                        Log.e(TAG, "NoConnectionError");
                    } else if (error instanceof TimeoutError) {
                        errorMsg = "Request timeout - Questions take time to generate. Try again with fewer questions.";
                        Log.e(TAG, "TimeoutError - This is common when generating questions");
                    } else if (error instanceof NetworkError) {
                        errorMsg = "Network error. Check server connection.";
                        Log.e(TAG, "NetworkError");
                    } else {
                        Log.e(TAG, "Unknown error", error);
                    }

                    Toast.makeText(this, errorMsg, Toast.LENGTH_LONG).show();
                    finish();
                }
        ) {
            @Override
            public Map<String, String> getHeaders() {
                Map<String, String> headers = new HashMap<>();
                headers.put("Content-Type", "application/json");
                headers.put("Accept", "application/json");
                return headers;
            }
        };

        // CRITICAL: Set VERY long timeout for question generation (can take 30-60 seconds)
        request.setRetryPolicy(new DefaultRetryPolicy(
                90000,  // 90 seconds timeout - question generation is SLOW
                0,      // No retries (to avoid duplicate questions)
                DefaultRetryPolicy.DEFAULT_BACKOFF_MULT
        ));

        RequestQueue queue = Volley.newRequestQueue(this);
        queue.add(request);

        Log.d(TAG, "Request sent - Waiting for response (this may take 30-90 seconds)...");
    }

    private void parseQuizResponse(JSONObject response) {
        try {
            Log.d(TAG, "Starting to parse response...");

            // The response structure from your server is: {"response": {...}}
            JSONObject responseData;
            if (response.has("response")) {
                responseData = response.getJSONObject("response");
                Log.d(TAG, "Found 'response' wrapper");
            } else {
                responseData = response;
                Log.d(TAG, "No 'response' wrapper, using direct response");
            }

            // Check success flag
            boolean success = responseData.optBoolean("success", false);
            Log.d(TAG, "Success flag: " + success);

            if (!success) {
                String errorMsg = responseData.optString("error", "Failed to generate questions");
                Log.e(TAG, "Server returned success=false: " + errorMsg);
                Toast.makeText(this, errorMsg, Toast.LENGTH_LONG).show();
                finish();
                return;
            }

            // Get questions array
            if (!responseData.has("questions")) {
                Log.e(TAG, "No 'questions' field in response!");
                Toast.makeText(this, "Invalid response format", Toast.LENGTH_SHORT).show();
                finish();
                return;
            }

            JSONArray questionsArray = responseData.getJSONArray("questions");
            Log.d(TAG, "Found " + questionsArray.length() + " questions");

            if (questionsArray.length() == 0) {
                Log.e(TAG, "Questions array is empty!");
                Toast.makeText(this, "No questions were generated", Toast.LENGTH_SHORT).show();
                finish();
                return;
            }

            // Parse each question
            for (int i = 0; i < questionsArray.length(); i++) {
                JSONObject q = questionsArray.getJSONObject(i);

                // Log each question to verify it's real
                String questionText = q.optString("question", "");
                String uniqueId = q.optString("unique_id", "");
                Log.d(TAG, "Question " + (i+1) + ": " + questionText.substring(0, Math.min(50, questionText.length())));
                Log.d(TAG, "Question ID: " + uniqueId);

                // Check if it's a fallback question
                if (uniqueId.equals("fallback")) {
                    Log.w(TAG, "⚠️ WARNING: This is a FALLBACK question!");
                }

                questions.add(q);
            }

            // Update UI with level and streak info
            int level = responseData.optInt("level", 1);
            String title = responseData.optString("title", "Novice");
            int streak = responseData.optInt("current_streak", 0);

            tvLevel.setText("Level " + level + " - " + title);
            tvStreak.setText("🔥 Streak: " + streak);

            Log.d(TAG, "Level: " + level + ", Title: " + title + ", Streak: " + streak);

            // Load first question
            loadQuestion(0);

        } catch (JSONException e) {
            Log.e(TAG, "JSON Parsing Error", e);
            e.printStackTrace();
            Toast.makeText(this, "Error parsing questions: " + e.getMessage(),
                    Toast.LENGTH_LONG).show();
            finish();
        }
    }

    private void loadQuestion(int index) {
        if (index >= questions.size()) {
            Log.d(TAG, "All questions answered, submitting session...");
            submitQuizSession();
            return;
        }

        currentQuestionIndex = index;
        questionStartTime = SystemClock.elapsedRealtime();

        try {
            JSONObject question = questions.get(index);

            // Log full question for debugging
            Log.d(TAG, "Loading question " + (index + 1) + ":");
            Log.d(TAG, question.toString(2));  // Pretty print JSON

            tvQuestionNumber.setText("Question " + (index + 1) + " of " + questions.size());

            String questionText = question.getString("question");
            String formatType = question.getString("format_type");

            tvQuestion.setText(questionText);
            Log.d(TAG, "Question text: " + questionText);
            Log.d(TAG, "Format type: " + formatType);

            // Reset views
            layoutOptions.setVisibility(View.GONE);
            layoutTextAnswer.setVisibility(View.GONE);
            rgOptions.clearCheck();
            etAnswer.setText("");
            btnSubmit.setEnabled(true);
            btnNext.setVisibility(View.GONE);
            rbOptionC.setVisibility(View.VISIBLE);
            rbOptionD.setVisibility(View.VISIBLE);

            // Setup based on question type
            if (formatType.equals("multiple_choice")) {
                setupMultipleChoice(question);
            } else if (formatType.equals("true_false")) {
                setupTrueFalse();
            } else {
                setupTextAnswer(formatType);
            }

        } catch (JSONException e) {
            Log.e(TAG, "Error loading question", e);
            e.printStackTrace();
            Toast.makeText(this, "Error loading question: " + e.getMessage(),
                    Toast.LENGTH_SHORT).show();
        }
    }

    private void setupMultipleChoice(JSONObject question) throws JSONException {
        layoutOptions.setVisibility(View.VISIBLE);

        JSONArray options = question.getJSONArray("options");
        Log.d(TAG, "Setting up " + options.length() + " options");

        rbOptionA.setText(options.getString(0));
        rbOptionB.setText(options.getString(1));
        rbOptionC.setText(options.getString(2));
        rbOptionD.setText(options.getString(3));

        Log.d(TAG, "Options set successfully");
    }

    private void setupTrueFalse() {
        layoutOptions.setVisibility(View.VISIBLE);

        rbOptionA.setText("True");
        rbOptionB.setText("False");
        rbOptionC.setVisibility(View.GONE);
        rbOptionD.setVisibility(View.GONE);

        Log.d(TAG, "True/False options set");
    }

    private void setupTextAnswer(String formatType) {
        layoutTextAnswer.setVisibility(View.VISIBLE);

        if (formatType.equals("fill_in_blank")) {
            etAnswer.setHint("Fill in the blank");
        } else {
            etAnswer.setHint("Enter your answer");
        }

        Log.d(TAG, "Text answer input ready");
    }

    private void submitAnswer() {
        String userAnswer = getUserAnswer();

        if (userAnswer.isEmpty()) {
            Toast.makeText(this, "Please select or enter an answer", Toast.LENGTH_SHORT).show();
            return;
        }

        long responseTime = (SystemClock.elapsedRealtime() - questionStartTime) / 1000;

        try {
            JSONObject answer = new JSONObject();
            answer.put("question_id", questions.get(currentQuestionIndex).getString("unique_id"));
            answer.put("answer", userAnswer);
            answer.put("response_time", responseTime);

            answers.add(answer);

            Log.d(TAG, "Answer submitted: " + userAnswer + " in " + responseTime + " seconds");

            btnSubmit.setEnabled(false);
            btnNext.setVisibility(View.VISIBLE);

        } catch (JSONException e) {
            Log.e(TAG, "Error submitting answer", e);
            e.printStackTrace();
        }
    }

    private String getUserAnswer() {
        if (layoutOptions.getVisibility() == View.VISIBLE) {
            int selectedId = rgOptions.getCheckedRadioButtonId();
            if (selectedId == -1) return "";

            if (selectedId == R.id.rbOptionA) return "A";
            if (selectedId == R.id.rbOptionB) return "B";
            if (selectedId == R.id.rbOptionC) return "C";
            if (selectedId == R.id.rbOptionD) return "D";
        } else {
            return etAnswer.getText().toString().trim();
        }
        return "";
    }

    private void loadNextQuestion() {
        loadQuestion(currentQuestionIndex + 1);
    }

    private void submitQuizSession() {
        progressBar.setVisibility(View.VISIBLE);
        tvQuestion.setText("Evaluating your performance...");

        String url = ApiConfig.getAgent3Url();
        Log.d(TAG, "Submitting quiz session to: " + url);

        JSONObject requestBody = new JSONObject();
        try {
            requestBody.put("action", "evaluate_session");
            requestBody.put("user", username);

            JSONArray answersArray = new JSONArray();
            for (JSONObject answer : answers) {
                answersArray.put(answer);
            }
            requestBody.put("answers", answersArray);

            Log.d(TAG, "Submitting " + answers.size() + " answers");
            Log.d(TAG, "Submit request: " + requestBody.toString(2));

        } catch (JSONException e) {
            Log.e(TAG, "Error creating submit request", e);
            e.printStackTrace();
        }

        JsonObjectRequest request = new JsonObjectRequest(
                Request.Method.POST, url, requestBody,
                response -> {
                    Log.d(TAG, "Evaluation response received");
                    Log.d(TAG, response.toString());
                    progressBar.setVisibility(View.GONE);
                    showResults(response);
                },
                error -> {
                    progressBar.setVisibility(View.GONE);
                    Log.e(TAG, "Error submitting quiz", error);
                    Toast.makeText(this, "Error submitting quiz: " + error.toString(),
                            Toast.LENGTH_LONG).show();
                }
        ) {
            @Override
            public Map<String, String> getHeaders() {
                Map<String, String> headers = new HashMap<>();
                headers.put("Content-Type", "application/json");
                headers.put("Accept", "application/json");
                return headers;
            }
        };

        request.setRetryPolicy(new DefaultRetryPolicy(
                30000,
                DefaultRetryPolicy.DEFAULT_MAX_RETRIES,
                DefaultRetryPolicy.DEFAULT_BACKOFF_MULT
        ));

        Volley.newRequestQueue(this).add(request);
    }

    private void showResults(JSONObject response) {
        Intent intent = new Intent(QuizActivity.this, ResultsActivity.class);
        intent.putExtra("results", response.toString());
        intent.putExtra("username", username);
        startActivity(intent);
        finish();
    }
}
