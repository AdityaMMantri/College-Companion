package com.example.ui_demo.network;

/**
 * Centralized API configuration class
 * Change SERVER_IP to your Flask server's IP address
 */
public class ApiConfig {

    private static final String SERVER_IP = "10.160.82.252";

    // Server Port
    private static final String SERVER_PORT = "3000";

    // Base URL
    private static final String BASE_URL = "http://" + SERVER_IP + ":" + SERVER_PORT;

    // Endpoints
    public static final String AGENT_3_ENDPOINT =   BASE_URL + "/agent3";

    // Timeout settings (milliseconds)
    public static final int TIMEOUT_MS = 30000; // 30 seconds

    /**
     * Get the full URL for Agent 3 endpoint
     */
    public static String getAgent3Url() {
        return AGENT_3_ENDPOINT;
    }

    /**
     * Check if using emulator configuration
     */
    public static boolean isEmulator() {
        return SERVER_IP.equals("10.0.2.2");
    }

    /**
     * Get server info for debugging
     */
    public static String getServerInfo() {
        return "Server: " + BASE_URL + "\n" +
                "Type: " + (isEmulator() ? "Emulator" : "Physical Device");
    }
}
