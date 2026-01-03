import asyncio
import json
from firebase_admin import firestore

from flask import Flask, jsonify, request

from flask_app.database import add
from flask_app.summary import summarizer

from flask_app.python_agents.Agent1 import main as agent1_main
from flask_app.python_agents.Agent2 import start_conversation
from flask_app.python_agents.Agent3 import EnhancedGamifiedQuizAgent


# Create a SINGLE global agent instance that persists across requests
quiz_agent = EnhancedGamifiedQuizAgent()

app = Flask(__name__)

response_array = []
conversation_array = []
chat_array = []

@app.route('/agent1', methods=['POST'])
def agent_1():
    data = request.get_json(silent=True) or {}
    question = data.get('question')
    user = data.get('user')
    
    if not user:
        return jsonify({"error": "No user provided"}), 400
    
    if not question:
        return jsonify({"error": "No question provided"}), 400

    if question.lower() == "quit":
        if not response_array:
            return jsonify({"error": "No data to store"}), 400
        time_table = response_array[-1]
        data_to_store = {
            "id": 2,
            "agent": "agent-1",
            "response": time_table,
            "timestamp": firestore.SERVER_TIMESTAMP 
        }
        add(2, user, data_to_store, "1")
        return jsonify({"message": "Data stored!"})

    if asyncio.iscoroutinefunction(agent1_main):
        agent_com = asyncio.run(agent1_main(question, user)) 
    else:
        agent_com = agent1_main(question, user) 

    response_array.append(agent_com)
    return jsonify({"response": agent_com})

@app.route('/agent2', methods=['POST'])
def agent_2():
    data = request.get_json(silent=True) or {}
    question = data.get('question', '').strip()
    user = data.get('user')
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
        
    if question.lower() == "quit":
        if not chat_array:
            return jsonify({"error": "No data to store"}), 400
        summarized_response = summarizer(chat_array)
        data_to_store = {
            "id": 1,
            "agent": "agent-2",
            "response": summarized_response,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        add(1, user, data_to_store, "2")
        return jsonify({"message": "Data stored!"})
    
    if asyncio.iscoroutinefunction(start_conversation):
        agent_2 = asyncio.run(start_conversation(question))
    else:
        agent_2 = start_conversation(question)
    
    chat_array.append(agent_2)
    return jsonify({"response": agent_2})

@app.route('/agent3', methods=['POST'])
def agent_3():
    data = request.get_json(silent=True) or {}
    action = data.get('action', '').strip()
    question = data.get('question', '').strip()
    user = data.get('user')
    answers = data.get('answers')
    
    print(f"[DEBUG] Received request - Action: {action}, User: {user}")
    
    if not user:
        return jsonify({"error": "No user provided"}), 400

    try:
        # Handle DASHBOARD action
        if action == "dashboard":
            print(f"[DEBUG] Fetching dashboard for user: {user}")
            
            # Get profile from the persistent agent
            profile = quiz_agent.get_user_profile(user)
            dashboard_data = quiz_agent.get_dashboard_data(profile)
            
            print(f"[DEBUG] Dashboard data: Level {dashboard_data.get('level')}, XP {dashboard_data.get('total_xp')}")
            
            # Save snapshot to Firebase
            try:
                save_dashboard_to_firebase(user, dashboard_data)
            except Exception as e:
                print(f"[WARNING] Firebase dashboard save failed: {e}")
            
            return jsonify({
                "success": True,
                "data": dashboard_data
            })
        
        # Handle BADGES action
        elif action == "badges":
            print(f"[DEBUG] Fetching badges for user: {user}")
            
            # Get profile from the persistent agent
            profile = quiz_agent.get_user_profile(user)
            badges_data = quiz_agent.get_all_badges(profile)
            
            print(f"[DEBUG] Badges: {badges_data.get('earned_count')}/{badges_data.get('total_count')}")
            
            return jsonify({
                "success": True,
                "data": badges_data
            })
        
        # Handle GENERATE_QUIZ action
        elif action == "generate_quiz":
            if not question:
                return jsonify({"error": "No question/topic provided"}), 400
            
            print(f"[DEBUG] Generating quiz: {question}")
            
            # Use the global agent instance
            quiz_response = asyncio.run(quiz_agent.generate_quiz_questions(user, question))
            
            if not quiz_response.get("success"):
                print(f"[ERROR] Quiz generation failed: {quiz_response.get('error')}")
                return jsonify(quiz_response), 400
            
            # Validate and add missing fields
            for q in quiz_response.get("questions", []):
                if "correct_answer" not in q:
                    q["correct_answer"] = "A"
                if "explanation" not in q:
                    q["explanation"] = "No explanation provided"
                if "question_hash" not in q:
                    q["question_hash"] = ""
                if "fun_fact" not in q:
                    q["fun_fact"] = ""
            
            print(f"[DEBUG] Generated {len(quiz_response.get('questions', []))} questions")
            
            # Store for evaluation (session storage)
            response_array.append({"response": quiz_response})
            
            return jsonify({"response": quiz_response})
        
        # Handle EVALUATE_SESSION action
        elif action == "evaluate_session":
            if not answers:
                return jsonify({"error": "No answers provided"}), 400
            
            print(f"[DEBUG] Evaluating session for user: {user}")
            
            if not response_array or "response" not in response_array[-1]:
                return jsonify({"error": "No quiz session found. Generate quiz first."}), 400
            
            # Extract questions from stored session
            questions_list = response_array[-1]["response"].get("questions", [])
            
            if not questions_list:
                return jsonify({"error": "No questions found in session"}), 400
            
            print(f"[DEBUG] Evaluating {len(answers)} answers against {len(questions_list)} questions")
            
            # Evaluate using the global agent
            final_result = asyncio.run(
                quiz_agent.evaluate_quiz_session(user, answers, questions_list)
            )
            
            if final_result.get("success"):
                print(f"[DEBUG] Evaluation success: Score {final_result.get('session_correct')}/{final_result.get('total_questions')}")
                print(f"[DEBUG] XP Earned: {final_result.get('session_xp')}, New Level: {final_result.get('level')}")
                
                # The agent automatically saves to quiz_legends_save.json
                
                # Also save to Firebase for persistence across server restarts
                try:
                    save_quiz_to_firebase(user, final_result)
                except Exception as e:
                    print(f"[WARNING] Firebase save failed (but local save succeeded): {e}")
            
            # Clear session after evaluation
            response_array.clear()
            
            return jsonify({"response": final_result})
        
        # Handle SAVE/QUIT action
        elif action == "save" or question.lower() == "quit":
            if not response_array:
                return jsonify({"error": "No data to store"}), 400
            
            last_response = response_array[-1]
            data_to_store = {
                "agent": "agent-3",
                "response": json.dumps(last_response),
                "timestamp": firestore.SERVER_TIMESTAMP
            }
            add(3, user, data_to_store, "agent-3-saved")
            response_array.clear()
            
            return jsonify({"message": "Data stored successfully!"})
        
        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400
    
    except Exception as e:
        print(f"[ERROR] Exception in agent3 endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


# Firebase helper functions
def save_quiz_to_firebase(user, results_data):
    """Save quiz results to Firebase"""
    try:
        data_to_store = {
            "agent": "agent-3",
            "type": "quiz_results",
            "session_correct": results_data.get("session_correct"),
            "total_questions": results_data.get("total_questions"),
            "accuracy": results_data.get("accuracy"),
            "session_xp": results_data.get("session_xp"),
            "total_xp": results_data.get("total_xp"),
            "level": results_data.get("level"),
            "title": results_data.get("title"),
            "current_streak": results_data.get("current_streak"),
            "coins": results_data.get("coins"),
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        
        # add(id, user_name, data, agent)
        result = add(3, user, data_to_store, "agent-3-quiz-results")
        print(f"✓ {result}")
        
    except Exception as e:
        print(f"✗ Error saving to Firebase: {e}")
        raise


def save_dashboard_to_firebase(user, dashboard_data):
    """Save dashboard snapshot to Firebase"""
    try:
        data_to_store = {
            "agent": "agent-3",
            "type": "dashboard",
            "level": dashboard_data.get("level"),
            "title": dashboard_data.get("title"),
            "total_xp": dashboard_data.get("total_xp"),
            "coins": dashboard_data.get("coins"),
            "current_streak": dashboard_data.get("current_streak"),
            "best_streak": dashboard_data.get("best_streak"),
            "badges_earned": dashboard_data.get("badges_earned"),
            "total_questions": dashboard_data.get("total_questions"),
            "total_correct": dashboard_data.get("total_correct"),
            "accuracy": dashboard_data.get("accuracy"),
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        
        # add(id, user_name, data, agent)
        result = add(3, user, data_to_store, "agent-3-dashboard")
        print(f"✓ {result}")
        
    except Exception as e:
        print(f"✗ Error saving dashboard to Firebase: {e}")


# API Routes
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "agents": ["agent1", "agent2", "agent3"]})


@app.route('/clear', methods=['POST'])
def clear_conversations():
    response_array.clear()
    conversation_array.clear()
    chat_array.clear()
    return jsonify({"message": "All conversations cleared"})


@app.route('/debug/users', methods=['GET'])
def debug_users():
    """Debug endpoint to see all users in the system"""
    try:
        users_info = {}
        for username, profile in quiz_agent.user_profiles.items():
            users_info[username] = {
                "level": quiz_agent.gamification.get_level_info(profile.total_xp)["level"],
                "total_xp": profile.total_xp,
                "total_questions": profile.total_questions,
                "badges": len(profile.earned_badges)
            }
        
        return jsonify({
            "total_users": len(quiz_agent.user_profiles),
            "users": users_info,
            "save_file_exists": os.path.exists('quiz_legends_save.json')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Quiz Legends Server Starting...")
    print("=" * 60)
    
    # Check if save file exists
    if os.path.exists('quiz_legends_save.json'):
        print("✓ Found existing save file: quiz_legends_save.json")
        try:
            with open('quiz_legends_save.json', 'r') as f:
                save_data = json.load(f)
                users = save_data.get("users", {})
                print(f"✓ Loaded {len(users)} user profiles")
                for username in list(users.keys())[:3]:  # Show first 3
                    print(f"  - {username}")
        except Exception as e:
            print(f"✗ Error reading save file: {e}")
    else:
        print("ℹ No save file found - will create on first user")
    
    print("=" * 60)
    print("Server ready at http://0.0.0.0:3000")
    print("Debug endpoint: http://0.0.0.0:3000/debug/users")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=3000, debug=True)
