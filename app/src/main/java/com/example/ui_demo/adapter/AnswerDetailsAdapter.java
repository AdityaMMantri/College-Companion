package com.example.ui_demo.adapter;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import org.json.JSONException;
import org.json.JSONObject;
import java.util.ArrayList;

public class AnswerDetailsAdapter extends RecyclerView.Adapter<AnswerDetailsAdapter.AnswerViewHolder> {

    private ArrayList<JSONObject> answers;

    public AnswerDetailsAdapter(ArrayList<JSONObject> answers) {
        this.answers = answers;
    }

    @NonNull
    @Override
    public AnswerViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_answer_detail, parent, false);
        return new AnswerViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull AnswerViewHolder holder, int position) {
        try {
            JSONObject answer = answers.get(position);
            holder.bind(answer, position + 1);
        } catch (JSONException e) {
            e.printStackTrace();
        }
    }

    @Override
    public int getItemCount() {
        return answers.size();
    }

    static class AnswerViewHolder extends RecyclerView.ViewHolder {

        private TextView tvQuestionNum, tvIsCorrect, tvXPEarned;
        private TextView tvExplanation, tvFunFact, tvCorrectAnswer;

        public AnswerViewHolder(@NonNull View itemView) {
            super(itemView);
            tvQuestionNum = itemView.findViewById(R.id.tvQuestionNum);
            tvIsCorrect = itemView.findViewById(R.id.tvIsCorrect);
            tvXPEarned = itemView.findViewById(R.id.tvXPEarned);
            tvExplanation = itemView.findViewById(R.id.tvExplanation);
            tvFunFact = itemView.findViewById(R.id.tvFunFact);
            tvCorrectAnswer = itemView.findViewById(R.id.tvCorrectAnswer);
        }

        public void bind(JSONObject answer, int questionNum) throws JSONException {
            boolean isCorrect = answer.getBoolean("is_correct");
            int xpEarned = answer.getInt("xp_earned");
            String explanation = answer.getString("explanation");
            String funFact = answer.optString("fun_fact", "");

            tvQuestionNum.setText("Question " + questionNum);

            if (isCorrect) {
                tvIsCorrect.setText("✓ Correct");
                tvIsCorrect.setTextColor(itemView.getContext().getResources().getColor(android.R.color.holo_green_dark));
                tvXPEarned.setText("+" + xpEarned + " XP");
                tvXPEarned.setVisibility(View.VISIBLE);
                tvCorrectAnswer.setVisibility(View.GONE);
            } else {
                tvIsCorrect.setText("✗ Incorrect");
                tvIsCorrect.setTextColor(itemView.getContext().getResources().getColor(android.R.color.holo_red_dark));
                tvXPEarned.setVisibility(View.GONE);

                String correctAnswer = answer.optString("correct_answer", "");
                if (!correctAnswer.isEmpty()) {
                    tvCorrectAnswer.setText("Correct Answer: " + correctAnswer);
                    tvCorrectAnswer.setVisibility(View.VISIBLE);
                } else {
                    tvCorrectAnswer.setVisibility(View.GONE);
                }
            }

            tvExplanation.setText("💡 " + explanation);

            if (!funFact.isEmpty()) {
                tvFunFact.setText("🎓 Fun Fact: " + funFact);
                tvFunFact.setVisibility(View.VISIBLE);
            } else {
                tvFunFact.setVisibility(View.GONE);
            }
        }
    }
}
