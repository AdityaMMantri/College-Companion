
# Colleage Companion Project

This project is a **Flask-based backend application** that integrates with Firebase and multiple AI agents.
It handles intelligent scheduling, study assistance, and gamified learning logic, designed to connect seamlessly with an Android app frontend.

This document provides the complete setup process to run the project locally from scratch.

---

## Prerequisites

### 1. Install Python 3.10 or 3.11

If Python is not installed, download one of the following versions:

* **Python 3.10 (Windows 64-bit)** → [https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe](https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe)
* **Python 3.11 (Windows 64-bit)** → [https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe)

> During installation, **check “Add Python to PATH”** before proceeding.

Verify installation:

```bash
python --version
```

Expected output:

```
Python 3.10.x
```

or

```
Python 3.11.x
```

---

## Installation Steps

### Step 1: Install All Required Libraries

A `requirements.txt` file has already been created in the project folder.
Simply open **Command Prompt** or **Terminal** inside your project directory and run:

```bash
pip install -r requirements.txt
```

This will automatically install all dependencies required for the Flask application.

---

### Step 2: If the Above Command Fails

If the above installation fails, use the following three commands instead (run them one after another):

```bash
pip install flask flask-cors firebase-admin langchain langchain-core langchain-google-genai langgraph
```

```bash
pip install pydantic dateparser requests python-dotenv pytesseract pymupdf Pillow python-docx
```

```bash
pip install aiohttp asyncio typing-extensions uuid
```

---

## Project Structure

```
.
├── flask_app/
│   ├── __init__.py
│   ├── server.py          # Main Flask server entry point
│   ├── database.py        # Firebase configuration
│   ├── summary.py         # Summarization or data processing logic
│   ├── Agent_1_trial.py   # Timetable Agent (study scheduler)
│   ├── Agent_2_trial.py   # Study Assistant (AI tutor)
│   ├── Agent_3.py         # Gamified Quiz Agent
├── requirements.txt
└── README.md
```

---

## Android Studio Configuration

Your Android app must connect to this Flask server using your **private system IP address**.
You can find it by running:

```bash
ipconfig
```

or by checking the IP displayed when Flask starts running.

### Files to Update in Android Studio

| File                  | Section to Modify             |
| --------------------- | ----------------------------- |
| `ApiClient.java`      | Base URL                      |
| `ApiConfig.java`      | API endpoint configuration    |
| `BadgesActivity.java` | Inside `fetchBadgesData()`    |
| `DashBoard3.java`     | Inside `fetchDashboardData()` |

Example:

```java
private static final String BASE_URL = "http://192.168.1.5:3000/";
```

> Replace `192.168.1.5` with your system’s private IP.

---

## Running the Application

To start the Flask server:

```bash
python flask_app/server.py
```

Once the server starts, you’ll see something like:

```
Running on http://192.168.1.5:3000/
```

Use that URL inside your Android code to connect to the backend.

---

## Troubleshooting
| Issue                   | Cause                              |Solution                                                        |
| ----------------------- | ---------------------------------- |----------------------------------------------------------------|
| **Port already in use** | Port 5000 is busy                  | Change port in `server.py` → `app.run(port=5000)`                                                                                                                               |
| **App not connecting**  | Different Wi-Fi networks           | Ensure both phone and PC are on the same Wi-Fi                                                                                                                           |
| **Firebase errors**     | Invalid credentials or permissions | Recheck Firebase configuration file and API key                                                                                                                             |
| **Import errors**       | Missing libraries                  | Run `pip install -r requirements.txt` again. If it still shows 
 a specific missing library, install it manually using `pip install <library_name>`                                             |


---
