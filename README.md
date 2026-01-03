# College Companion

College Companion is an **AI-powered academic assistance platform** designed to help students manage
their academic life intelligently. The system integrates an **Android application**, a **Flask-based backend**,
**Firebase**, and multiple **AI agents** to provide smart scheduling, study assistance, and gamified learning.

This repository contains **both the Android frontend and the Python backend**, structured to scale and
support multi-agent reasoning.

---

## Project Overview

College Companion addresses common student problems such as:
- Poor time management
- Lack of personalized study guidance
- Low engagement in self-study
- Fragmented academic tools

By combining **AI agents**, **cloud storage**, and a **mobile-first interface**, the system delivers:
- Automated timetable generation
- AI-powered study assistance
- Gamified quizzes and badges
- Real-time data synchronization

---

## System Architecture

```

Android App (Java)
|
| REST APIs
v
Flask Backend (Python)
|
| Firebase Admin SDK
v
Firebase (Auth + Firestore)
|
| Agent Orchestration
v
Multiple AI Agents (LangChain / LangGraph)

```

### Architecture Breakdown

- **Android App**
  - User interface
  - Authentication
  - API consumption
  - Gamification and dashboards

- **Flask Backend**
  - Central orchestration layer
  - API gateway for Android
  - Agent coordination
  - Business logic enforcement

- **Firebase**
  - Authentication
  - Persistent user data
  - Timetable, progress, and badge storage

- **AI Agents**
  - Independent task-specific agents
  - Stateless execution
  - Shared memory via Firebase

---

## AI Agents Overview

| Agent | Name | Responsibility |
|-----|-----|----------------|
| Agent 1 | Timetable Agent | Generates and optimizes study schedules based on subjects, deadlines, and availability |
| Agent 2 | Study Assistant | Acts as an AI tutor for explanations, doubts, and concept clarification |
| Agent 3 | Gamification Agent | Generates quizzes, awards badges, and tracks progress |

Each agent is **loosely coupled**, allowing independent upgrades and experimentation.

---

## Project Structure

```

.
├── app/                         # Android application
│   ├── src/main/java/
│   │   └── com/example/ui_demo/
│   │       ├── ui/              # Feature-based UI packages
│   │       ├── network/         # API clients and configs
│   │       ├── adapter/         # RecyclerView adapters
│   │       ├── model/           # Data models
│   │       └── util/            # Utilities
│   └── src/main/res/             # XML resources
│
├── flask_app/                   # Flask backend
│   ├── server.py                # Main Flask server
│   ├── database.py              # Firebase configuration
│   ├── summary.py               # Processing / summarization logic
│   ├── Agent_1_trial.py          # Timetable Agent
│   ├── Agent_2_trial.py          # Study Assistant Agent
│   ├── Agent_3.py                # Gamification Agent
│
├── requirements.txt
├── README.md
└── LICENSE

````

---

## Prerequisites

### Python
- Python **3.10 or 3.11**
- Ensure **Add Python to PATH** is checked during installation

Verify:
```bash
python --version
````

---

## Backend Setup (Flask)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

If the above fails:

```bash
pip install flask flask-cors firebase-admin langchain langchain-core langchain-google-genai langgraph
pip install pydantic dateparser requests python-dotenv pytesseract pymupdf Pillow python-docx
pip install aiohttp asyncio typing-extensions uuid
```

---

### Step 2: Environment Variables

Create a `.env` file in the project root:

```env
FIREBASE_CREDENTIALS=path/to/firebase_service_account.json
GOOGLE_API_KEY=your_google_genai_key
FLASK_ENV=development
```

Load variables in Python:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

### Step 3: Run Flask Server

```bash
python flask_app/server.py
```

Example output:

```
Running on http://192.168.1.5:3000/
```

---

## Android App Configuration

The Android app connects to the Flask backend using your **local private IP**.

Find your IP:

```bash
ipconfig
```

### Files to Update

| File                  | Purpose                |
| --------------------- | ---------------------- |
| `ApiClient.java`      | Base URL               |
| `ApiConfig.java`      | Endpoint configuration |
| `BadgesActivity.java` | Badge fetch logic      |
| `DashBoard3.java`     | Dashboard data fetch   |

Example:

```java
private static final String BASE_URL = "http://192.168.1.5:3000/";
```

Ensure:

* Phone and PC are on the **same Wi-Fi**
* Firewall allows incoming connections

---

## Android ↔ Backend Communication Flow

1. Android sends REST request
2. Flask validates request
3. Firebase data is fetched or updated
4. AI agents process logic
5. Flask returns structured JSON
6. Android updates UI

---

## Troubleshooting

| Issue               | Cause               | Solution                    |
| ------------------- | ------------------- | --------------------------- |
| Port already in use | Port conflict       | Change port in `server.py`  |
| App not connecting  | Different networks  | Use same Wi-Fi              |
| Firebase errors     | Invalid credentials | Verify service account file |
| Import errors       | Missing packages    | Reinstall requirements      |

---

## Development Notes

* Feature-based Android package structure
* Git-only refactoring (no IDE refactor)
* Agents are intentionally stateless
* Firebase acts as shared memory

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit with clear messages
4. Open a pull request

Follow clean architecture principles.

---
```
