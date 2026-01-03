package com.example.ui_demo.ui.auth;

import androidx.appcompat.app.AppCompatActivity;
import android.os.Bundle;
import android.widget.*;
import android.content.Intent;
import com.google.firebase.auth.FirebaseAuth;

public class LoginActivity extends AppCompatActivity {
    private EditText emailInput, passwordInput;
    private Button loginButton;
    private TextView registerLink;
    private FirebaseAuth auth;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        auth = FirebaseAuth.getInstance();

        emailInput = findViewById(R.id.emailInput);
        passwordInput = findViewById(R.id.passwordInput);
        loginButton = findViewById(R.id.loginButton);
        registerLink = findViewById(R.id.registerLink);

        loginButton.setOnClickListener(v -> loginUser());
        registerLink.setOnClickListener(v -> {
            startActivity(new Intent(LoginActivity.this, RegisterActivity.class));
        });
    }

    private void loginUser() {
        String email = emailInput.getText().toString().trim();
        String pass = passwordInput.getText().toString().trim();

        if (email.isEmpty() || pass.isEmpty()) {
            Toast.makeText(this, "Please fill all fields", Toast.LENGTH_SHORT).show();
            return;
        }

        auth.signInWithEmailAndPassword(email, pass)
                .addOnSuccessListener(res -> {
                    Intent intent = new Intent(LoginActivity.this, DashboardActivity.class);
                    intent.putExtra("userEmail", email);
                    startActivity(intent);
                    finish();
                })
                .addOnFailureListener(e -> {
                    Toast.makeText(this, e.getMessage(), Toast.LENGTH_SHORT).show();
                });
    }
}
