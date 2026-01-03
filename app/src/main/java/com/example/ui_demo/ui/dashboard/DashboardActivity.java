package com.example.ui_demo.ui.dashboard;

import androidx.appcompat.app.AppCompatActivity;
import android.os.Bundle;
import android.widget.Button;
import android.content.Intent;

public class DashboardActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_dashboard);

        String userEmail = getIntent().getStringExtra("userEmail");

        Button agent1Btn = findViewById(R.id.agent1Btn);
        Button agent2Btn = findViewById(R.id.agent2Btn);
        Button agent3Btn = findViewById(R.id.agent3Btn);

        agent1Btn.setOnClickListener(v -> {
            Intent i = new Intent(this, Agent1Activity.class);
            i.putExtra("userEmail", userEmail);
            startActivity(i);
        });

        agent2Btn.setOnClickListener(v -> {
            Intent i = new Intent(this, Agent2Activity.class);
            i.putExtra("userEmail", userEmail);
            startActivity(i);
        });
        agent3Btn.setOnClickListener(v -> {
            Intent i = new Intent(this, Agent3Activity.class);
            i.putExtra("userEmail", userEmail);
            startActivity(i);
        });
    }
}
