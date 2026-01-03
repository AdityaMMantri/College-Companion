package com.example.ui_demo.network;

import java.io.IOException;
import java.util.concurrent.TimeUnit;
import okhttp3.*;

public class ApiClient {
    private static final String BASE_URL = "http://10.160.82.252:3000"; // Replace YOUR_SERVER_IP

    // Configure timeouts (you can tune these values)
    private static final OkHttpClient client = new OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS) // Time to establish connection
            .writeTimeout(10, TimeUnit.SECONDS)   // Time to send request data
            .readTimeout(15, TimeUnit.SECONDS)    // Time to wait for server response
            .build();

    public static String post(String endpoint, String json) throws IOException {
        MediaType JSON = MediaType.get("application/json; charset=utf-8");
        RequestBody body = RequestBody.create(json, JSON);
        Request request = new Request.Builder()
                .url(BASE_URL + endpoint)
                .post(body)
                .build();

        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException("Unexpected code " + response);
            }
            return response.body().string();
        }
    }
}
