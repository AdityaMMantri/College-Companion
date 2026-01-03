import os
import random
import json
import re
import hashlib
import time
import pickle
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# API Key
GOOGLE_API_KEY = ""

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.8,
    max_tokens=1000,
    api_key=GOOGLE_API_KEY,
    timeout=20
)

@dataclass
class Badge:
    id: str
    name: str
    description: str
    icon: str
    category: str
    rarity: str
    xp_reward: int
    coins_reward: int = 0
    unlock_condition: str = ""

@dataclass
class Quest:
    id: str
    name: str
    description: str
    target: int
    current_progress: int = 0
    reward_xp: int = 100
    reward_coins: int = 25
    quest_type: str = "daily"
    category: str = "general"
    completed: bool = False
    expires_at: Optional[datetime] = None

@dataclass
class UserProfile:
    username: str
    total_xp: int = 0
    coins: int = 200
    current_streak: int = 0
    best_streak: int = 0
    level: int = 1
    prestige: int = 0
    earned_badges: Set[str] = field(default_factory=set)
    completed_quests: Set[str] = field(default_factory=set)
    question_history: Set[str] = field(default_factory=set)
    topic_mastery: Dict[str, int] = field(default_factory=dict)
    daily_stats: Dict = field(default_factory=lambda: {
        "questions_answered": 0,
        "correct_answers": 0,
        "fast_answers": 0,
        "perfect_answers": 0,
        "topics_tried": set(),
        "last_active": datetime.now().date()
    })
    total_questions: int = 0
    total_correct: int = 0
    average_response_time: float = 0.0
    favorite_topics: List[str] = field(default_factory=list)

@dataclass
class QuizQuestion:
    question: str
    correct_answer: str
    explanation: str
    topic: str
    difficulty: str
    format_type: str
    options: Optional[List[str]] = None
    unique_id: str = ""
    question_hash: str = ""
    fun_fact: str = ""


class AdvancedGamificationEngine:
    def __init__(self):
        self.level_data = [
            {"level": 1, "title": "🌱 Curious Novice", "xp_required": 0, "xp_to_next": 100},
            {"level": 2, "title": "📚 Eager Learner", "xp_required": 100, "xp_to_next": 150},
            {"level": 3, "title": "🎯 Knowledge Seeker", "xp_required": 250, "xp_to_next": 200},
            {"level": 4, "title": "⚡ Quiz Apprentice", "xp_required": 450, "xp_to_next": 300},
            {"level": 5, "title": "🔥 Trivia Warrior", "xp_required": 750, "xp_to_next": 400},
            {"level": 6, "title": "🎓 Scholar Knight", "xp_required": 1150, "xp_to_next": 500},
            {"level": 7, "title": "💎 Wisdom Guardian", "xp_required": 1650, "xp_to_next": 750},
            {"level": 8, "title": "🚀 Knowledge Master", "xp_required": 2400, "xp_to_next": 1000},
            {"level": 9, "title": "👑 Quiz Royalty", "xp_required": 3400, "xp_to_next": 1500},
            {"level": 10, "title": "🌟 Learning Legend", "xp_required": 4900, "xp_to_next": 2000},
            {"level": 11, "title": "🔮 Mystic Scholar", "xp_required": 6900, "xp_to_next": 2500},
            {"level": 12, "title": "⚔️ Quiz Gladiator", "xp_required": 9400, "xp_to_next": 3000},
            {"level": 13, "title": "🏆 Grand Master", "xp_required": 12400, "xp_to_next": 4000},
            {"level": 14, "title": "🎭 Sage Emperor", "xp_required": 16400, "xp_to_next": 5000},
            {"level": 15, "title": "🌌 Cosmic Scholar", "xp_required": 21400, "xp_to_next": 7500},
            {"level": 16, "title": "⭐ Stellar Genius", "xp_required": 28900, "xp_to_next": 10000},
            {"level": 17, "title": "🎇 Quantum Mind", "xp_required": 38900, "xp_to_next": 15000},
            {"level": 18, "title": "🌠 Universal Sage", "xp_required": 53900, "xp_to_next": 20000},
            {"level": 19, "title": "💫 Omniscient Being", "xp_required": 73900, "xp_to_next": 30000},
            {"level": 20, "title": "🌈 Transcendent Master", "xp_required": 103900, "xp_to_next": 0}
        ]
        
        self.badges = {
            "first_steps": Badge("first_steps", "🌟 First Victory", "Answer your first question correctly", "🌟", "achievement", "common", 50, 10),
            "century_club": Badge("century_club", "💯 Century Club", "Answer 100 questions correctly", "💯", "achievement", "rare", 500, 100),
            "millennium_master": Badge("millennium_master", "🏆 Millennium Master", "Answer 1000 questions correctly", "🏆", "achievement", "legendary", 2000, 500),
            "hot_streak": Badge("hot_streak", "🔥 Hot Streak", "Get 5 correct answers in a row", "🔥", "streak", "common", 100, 20),
            "blazing_trail": Badge("blazing_trail", "⚡ Blazing Trail", "Get 10 correct answers in a row", "⚡", "streak", "rare", 300, 50),
            "unstoppable_force": Badge("unstoppable_force", "🚀 Unstoppable Force", "Get 25 correct answers in a row", "🚀", "streak", "epic", 1000, 200),
            "legend_born": Badge("legend_born", "👑 Legend Born", "Get 50 correct answers in a row", "👑", "streak", "legendary", 3000, 500),
            "quick_draw": Badge("quick_draw", "💨 Quick Draw", "Answer 10 questions in under 3 seconds each", "💨", "speed", "rare", 200, 40),
            "lightning_reflexes": Badge("lightning_reflexes", "⚡ Lightning Reflexes", "Answer 25 questions in under 2 seconds each", "⚡", "speed", "epic", 500, 100),
            "time_bender": Badge("time_bender", "⏰ Time Bender", "Answer 50 questions in under 1.5 seconds each", "⏰", "speed", "legendary", 1500, 300),
            "perfectionist": Badge("perfectionist", "💎 Perfectionist", "Score 100% on 10+ question quiz", "💎", "mastery", "epic", 750, 150),
            "scholar": Badge("scholar", "🎓 Scholar", "Master 5 different topics", "🎓", "mastery", "rare", 400, 75),
            "polymath": Badge("polymath", "🔬 Polymath", "Master 15 different topics", "🔬", "mastery", "legendary", 1200, 250),
            "xp_hunter": Badge("xp_hunter", "⭐ XP Hunter", "Earn 1000 total XP", "⭐", "progression", "common", 100, 25),
            "xp_master": Badge("xp_master", "🌟 XP Master", "Earn 10000 total XP", "🌟", "progression", "epic", 1000, 200),
            "xp_legend": Badge("xp_legend", "✨ XP Legend", "Earn 50000 total XP", "✨", "progression", "legendary", 2500, 500),
            "night_owl": Badge("night_owl", "🦉 Night Owl", "Answer questions between 10PM-6AM", "🦉", "special", "rare", 150, 30),
            "early_bird": Badge("early_bird", "🦅 Early Bird", "Answer questions between 5AM-8AM", "🦅", "special", "rare", 150, 30),
            "weekend_warrior": Badge("weekend_warrior", "⚔️ Weekend Warrior", "Play for 5 weekends in a row", "⚔️", "special", "rare", 300, 60),
            "daily_devotee": Badge("daily_devotee", "📅 Daily Devotee", "Play every day for a week", "📅", "special", "epic", 600, 120),
            "quiz_god": Badge("quiz_god", "🌈 Quiz God", "Reach level 20", "🌈", "legendary", "legendary", 5000, 1000),
            "the_chosen_one": Badge("the_chosen_one", "👼 The Chosen One", "Get perfect accuracy on 100+ questions", "👼", "legendary", "legendary", 10000, 2000),
        }
    
    def calculate_xp(self, correct: bool, difficulty: str, response_time: float, streak: int, level: int) -> int:
        if not correct:
            return 0
        
        base_xp = 15
        difficulty_multipliers = {"easy": 1.0, "medium": 1.5, "hard": 2.2, "expert": 3.0}
        difficulty_bonus = int(base_xp * difficulty_multipliers.get(difficulty, 1.5))
        
        if response_time <= 1:
            speed_bonus = 25
        elif response_time <= 2:
            speed_bonus = 15
        elif response_time <= 3:
            speed_bonus = 10
        elif response_time <= 5:
            speed_bonus = 5
        else:
            speed_bonus = 0
        
        if streak >= 50:
            streak_bonus = 100
        elif streak >= 25:
            streak_bonus = 50
        elif streak >= 10:
            streak_bonus = 25
        elif streak >= 5:
            streak_bonus = 15
        else:
            streak_bonus = streak * 2
        
        level_bonus = level * 2
        total_xp = base_xp + difficulty_bonus + speed_bonus + streak_bonus + level_bonus
        return max(total_xp, 10)
    
    def get_level_info(self, xp: int) -> Dict:
        for i, level_info in enumerate(self.level_data):
            if i == len(self.level_data) - 1:
                return {
                    "level": level_info["level"],
                    "title": level_info["title"],
                    "xp_to_next": 0,
                    "progress": 100.0,
                    "is_max": True
                }
            
            next_level = self.level_data[i + 1]
            if xp < next_level["xp_required"]:
                current_level_xp = level_info["xp_required"]
                xp_needed = next_level["xp_required"] - xp
                xp_for_level = next_level["xp_required"] - current_level_xp
                progress = ((xp - current_level_xp) / xp_for_level) * 100
                
                return {
                    "level": level_info["level"],
                    "title": level_info["title"],
                    "xp_to_next": xp_needed,
                    "progress": max(0, progress),
                    "is_max": False
                }
        
        return self.level_data[-1]


class EnhancedGamifiedQuizAgent:
    def __init__(self):
        self.gamification = AdvancedGamificationEngine()
        self.user_profiles: Dict[str, UserProfile] = {}
        self.session_questions: Set[str] = set()
        self.global_question_bank: Set[str] = set()
        self.load_user_data()
        
        self.format_configs = {
            "multiple_choice": {
                "instruction": "Create 4 unique, plausible options with ONE clearly correct answer. Make distractors challenging but fair.",
                "example": '{"question":"What is the primary function of mitochondria?","options":["A. Protein synthesis","B. Energy production","C. DNA replication","D. Waste removal"],"correct_answer":"B","explanation":"Mitochondria are known as the powerhouses of the cell because they produce ATP through cellular respiration.","fun_fact":"A single cell can contain hundreds of mitochondria!","topic":"Biology","difficulty":"medium","format_type":"multiple_choice"}'
            },
            "true_false": {
                "instruction": "Create a statement that is definitively true or false, avoiding ambiguous scenarios.",
                "example": '{"question":"True or False: The Great Wall of China is visible from space with the naked eye.","correct_answer":"False","explanation":"This is a common myth. The Great Wall is not visible from space with the naked eye.","fun_fact":"Astronauts report that city lights are much more visible from space than the Great Wall.","topic":"Geography","difficulty":"medium","format_type":"true_false"}'
            },
            "fill_in_blank": {
                "instruction": "Create a sentence with ONE blank that has a specific, unambiguous answer.",
                "example": '{"question":"The chemical symbol for gold is _____.","correct_answer":"Au","explanation":"Au comes from the Latin word aurum, meaning gold.","fun_fact":"Gold is one of the few elements that occurs naturally in its pure form.","topic":"Chemistry","difficulty":"easy","format_type":"fill_in_blank"}'
            },
            "short_answer": {
                "instruction": "Create a question requiring a 1-3 word specific answer, not an explanation.",
                "example": '{"question":"What planet is known as the Red Planet?","correct_answer":"Mars","explanation":"Mars appears red due to iron oxide (rust) on its surface.","fun_fact":"Mars has the largest volcano in the solar system - Olympus Mons!","topic":"Astronomy","difficulty":"easy","format_type":"short_answer"}'
            }
        }
        
        self.ENHANCED_QUIZ_PROMPT = PromptTemplate.from_template("""
You are creating a UNIQUE {format_type} question for Quiz Legends, an educational RPG game.

PLAYER CONTEXT:
- Player Level: {user_level} ({level_title})
- Topic Mastery: {topic_mastery} questions in this topic
- Recent Topics: {recent_topics}
- Difficulty: {difficulty}
- Session ID: {session_id} (ensure uniqueness)

UNIQUENESS REQUIREMENTS:
- This question must be completely different from previous questions
- Avoid repeating concepts, specific facts, or similar phrasings
- Question ID: {unique_id} - make it distinctive
- Focus on unexplored aspects of {topic}

GAMIFICATION REQUIREMENTS:
- Make it engaging and appropriately challenging for Level {user_level}
- Include an interesting "fun_fact" to boost engagement
- Difficulty should match: {difficulty}

FORMAT REQUIREMENTS:
{format_specific_instruction}

QUALITY STANDARDS:
- Question must be factually accurate and unambiguous
- Explanation should be educational and clear
- Fun fact should be genuinely interesting and related

JSON OUTPUT (no additional text):
{format_example}
""")

    def save_user_data(self):
        try:
            save_data = {
                "users": {},
                "global_question_bank": list(self.global_question_bank)
            }
            
            for username, profile in self.user_profiles.items():
                profile_dict = profile.__dict__.copy()
                profile_dict['earned_badges'] = list(profile_dict['earned_badges'])
                profile_dict['completed_quests'] = list(profile_dict['completed_quests'])
                profile_dict['question_history'] = list(profile_dict['question_history'])
                
                daily_stats = profile_dict['daily_stats'].copy()
                daily_stats['topics_tried'] = list(daily_stats['topics_tried'])
                profile_dict['daily_stats'] = daily_stats
                
                save_data["users"][username] = profile_dict
            
            with open('quiz_legends_save.json', 'w') as f:
                json.dump(save_data, f, default=str, indent=2)
        except Exception as e:
            pass

    def load_user_data(self):
        try:
            with open('quiz_legends_save.json', 'r') as f:
                save_data = json.load(f)
            
            # Load global question bank
            if "global_question_bank" in save_data:
                self.global_question_bank = set(save_data["global_question_bank"])
            
            # Load users
            users_data = save_data.get("users", save_data)  # Backward compatibility
            
            for username, profile_dict in users_data.items():
                if username == "global_question_bank":  # Skip if old format
                    continue
                    
                profile_dict['earned_badges'] = set(profile_dict['earned_badges'])
                profile_dict['completed_quests'] = set(profile_dict['completed_quests'])
                profile_dict['question_history'] = set(profile_dict['question_history'])
                
                daily_stats = profile_dict['daily_stats']
                daily_stats['topics_tried'] = set(daily_stats['topics_tried'])
                
                if isinstance(daily_stats['last_active'], str):
                    daily_stats['last_active'] = datetime.fromisoformat(daily_stats['last_active']).date()
                
                profile_dict['daily_stats'] = daily_stats
                self.user_profiles[username] = UserProfile(**profile_dict)
        except Exception as e:
            pass

    def get_user_profile(self, username: str) -> UserProfile:
        if username not in self.user_profiles:
            self.user_profiles[username] = UserProfile(username=username)
        
        profile = self.user_profiles[username]
        if profile.daily_stats['last_active'] != datetime.now().date():
            profile.daily_stats = {
                "questions_answered": 0,
                "correct_answers": 0,
                "fast_answers": 0,
                "perfect_answers": 0,
                "topics_tried": set(),
                "last_active": datetime.now().date()
            }
        
        return profile

    def generate_unique_id(self) -> str:
        return f"ql_{int(time.time())}_{random.randint(10000, 99999)}"

    def parse_user_request(self, user_input: str) -> Dict:
        lower = user_input.lower()
        
        topic = user_input
        removal_phrases = [
            "quiz me on", "questions about", "test me on", "quiz about", 
            "generate questions on", "ask me about", "challenge me with",
            "let's do", "give me", "create", "make"
        ]
        
        for phrase in removal_phrases:
            if phrase in lower:
                topic = user_input[lower.find(phrase) + len(phrase):].strip()
                break
        
        cleanup_patterns = [
            r'\b(easy|medium|hard|difficult|simple|expert)\b',
            r'\b(\d+)\s*(questions?|mcqs?|problems?)\b',
            r'\b(true.?false|fill.?in|multiple.?choice|short.?answer|mixed)\b'
        ]
        
        for pattern in cleanup_patterns:
            topic = re.sub(pattern, '', topic, flags=re.IGNORECASE).strip()
        
        if not topic or len(topic) < 2:
            topic = "General Knowledge"
        
        difficulty = "medium"
        if any(word in lower for word in ["easy", "simple", "basic", "beginner", "intro"]):
            difficulty = "easy"
        elif any(word in lower for word in ["hard", "difficult", "challenging", "advanced", "expert", "complex"]):
            difficulty = "hard"
        elif any(word in lower for word in ["expert", "master", "extreme", "insane"]):
            difficulty = "expert"
        
        format_type = "multiple_choice"
        format_keywords = {
            "true_false": ["true false", "true/false", "t/f", "true or false"],
            "fill_in_blank": ["fill in", "fill-in", "blank", "complete the", "fill the"],
            "short_answer": ["short answer", "one word", "name the", "what is", "who is"],
            "mixed": ["mixed", "variety", "different types", "random", "all types"]
        }
        
        for fmt, keywords in format_keywords.items():
            if any(keyword in lower for keyword in keywords):
                format_type = fmt
                break
        
        num_questions = 3
        numbers = re.findall(r'\b(\d+)\b', user_input)
        if numbers:
            try:
                num = int(numbers[0])
                if 1 <= num <= 50:
                    num_questions = num
            except:
                pass
        
        return {
            "topic": topic.title(),
            "difficulty": difficulty,
            "format_type": format_type,
            "num_questions": num_questions
        }

    async def generate_unique_question(self, topic: str, difficulty: str, format_type: str, profile: UserProfile) -> Optional[QuizQuestion]:
        max_attempts = 5
        
        for attempt in range(max_attempts):
            try:
                unique_id = self.generate_unique_id()
                level_info = self.gamification.get_level_info(profile.total_xp)
                
                topic_mastery = profile.topic_mastery.get(topic, 0)
                recent_topics = list(profile.daily_stats["topics_tried"])[-3:]
                
                config = self.format_configs.get(format_type, self.format_configs["multiple_choice"])
                
                prompt_vars = {
                    "topic": topic,
                    "difficulty": difficulty,
                    "format_type": format_type,
                    "unique_id": unique_id,
                    "user_level": level_info["level"],
                    "level_title": level_info["title"],
                    "topic_mastery": topic_mastery,
                    "recent_topics": ", ".join(recent_topics) if recent_topics else "None",
                    "session_id": unique_id,
                    "format_specific_instruction": config["instruction"],
                    "format_example": config["example"]
                }
                
                response = await asyncio.wait_for(
                    (self.ENHANCED_QUIZ_PROMPT | llm | StrOutputParser()).ainvoke(prompt_vars),
                    timeout=15.0
                )
                
                json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                json_match = re.search(json_pattern, response, re.DOTALL)
                
                if not json_match:
                    continue
                
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    continue
                
                question_content = f"{data['question']}_{data['correct_answer']}"
                question_hash = hashlib.md5(question_content.encode()).hexdigest()
                
                if (question_hash in profile.question_history or 
                    question_hash in self.session_questions or
                    question_hash in self.global_question_bank):
                    continue
                
                profile.question_history.add(question_hash)
                self.session_questions.add(question_hash)
                self.global_question_bank.add(question_hash)
                
                return QuizQuestion(
                    question=data["question"],
                    correct_answer=data["correct_answer"],
                    explanation=data.get("explanation", "No explanation provided."),
                    topic=data.get("topic", topic),
                    difficulty=difficulty,
                    format_type=format_type,
                    options=data.get("options"),
                    unique_id=unique_id,
                    question_hash=question_hash,
                    fun_fact=data.get("fun_fact", "")
                )
                
            except Exception as e:
                if attempt == max_attempts - 1:
                    return self.create_emergency_fallback(topic, difficulty, format_type)
                continue
        
        return None

    def create_emergency_fallback(self, topic: str, difficulty: str, format_type: str) -> QuizQuestion:
        fallback_questions = {
            "multiple_choice": {
                "question": f"Which of the following best describes {topic}?",
                "options": ["A. A fundamental concept", "B. An unrelated idea", "C. A complex theory", "D. A simple definition"],
                "correct_answer": "A",
                "explanation": f"This is a basic question about {topic}."
            },
            "true_false": {
                "question": f"True or False: {topic} is an important subject of study.",
                "correct_answer": "True",
                "explanation": f"{topic} is indeed considered an important area of knowledge."
            },
            "fill_in_blank": {
                "question": f"The study of {topic} involves understanding _____ principles.",
                "correct_answer": "basic",
                "explanation": "Basic principles form the foundation of any subject."
            },
            "short_answer": {
                "question": f"What is the main focus of {topic}?",
                "correct_answer": "knowledge",
                "explanation": f"{topic} primarily focuses on expanding knowledge and understanding."
            }
        }
        
        fallback = fallback_questions.get(format_type, fallback_questions["multiple_choice"])
        
        return QuizQuestion(
            question=fallback["question"],
            correct_answer=fallback["correct_answer"],
            explanation=fallback["explanation"],
            topic=topic,
            difficulty=difficulty,
            format_type=format_type,
            options=fallback.get("options"),
            unique_id="fallback",
            question_hash="fallback",
            fun_fact=f"Did you know? Learning about {topic} can improve your overall knowledge!"
        )

    def evaluate_answer(self, question: QuizQuestion, user_answer: str) -> bool:
        if not user_answer or not user_answer.strip():
            return False
        
        user_clean = user_answer.strip().lower()
        correct_clean = question.correct_answer.strip().lower()
        
        if question.format_type == "multiple_choice":
            user_choice = user_clean.upper()
            correct_choice = correct_clean.upper()
            
            if len(user_choice) == 1 and user_choice in 'ABCD':
                return user_choice == correct_choice
            else:
                for letter in 'ABCD':
                    if user_clean.startswith(letter.lower()):
                        return letter == correct_choice
                return False
                
        elif question.format_type == "true_false":
            user_bool_indicators = ["true", "t", "yes", "y", "1", "correct", "right"]
            correct_is_true = "true" in correct_clean
            user_is_true = any(indicator in user_clean for indicator in user_bool_indicators)
            return user_is_true == correct_is_true
            
        else:
            if user_clean == correct_clean:
                return True
            if correct_clean in user_clean or user_clean in correct_clean:
                return True
            
            user_words = set(user_clean.split())
            correct_words = set(correct_clean.split())
            
            overlap = len(user_words & correct_words)
            return overlap > 0 and overlap >= min(len(user_words), len(correct_words)) * 0.7

    def check_badge_unlocks(self, profile: UserProfile) -> List[Badge]:
        new_badges = []
        
        for badge_id, badge in self.gamification.badges.items():
            if badge_id in profile.earned_badges:
                continue
            
            earned = False
            
            if badge_id == "first_steps" and profile.total_correct >= 1:
                earned = True
            elif badge_id == "century_club" and profile.total_correct >= 100:
                earned = True
            elif badge_id == "millennium_master" and profile.total_correct >= 1000:
                earned = True
            elif badge_id == "hot_streak" and profile.current_streak >= 5:
                earned = True
            elif badge_id == "blazing_trail" and profile.current_streak >= 10:
                earned = True
            elif badge_id == "unstoppable_force" and profile.best_streak >= 25:
                earned = True
            elif badge_id == "legend_born" and profile.best_streak >= 50:
                earned = True
            elif badge_id == "quick_draw" and profile.daily_stats["fast_answers"] >= 10:
                earned = True
            elif badge_id == "lightning_reflexes" and profile.daily_stats.get("ultra_fast_answers", 0) >= 25:
                earned = True
            elif badge_id == "xp_hunter" and profile.total_xp >= 1000:
                earned = True
            elif badge_id == "xp_master" and profile.total_xp >= 10000:
                earned = True
            elif badge_id == "xp_legend" and profile.total_xp >= 50000:
                earned = True
            elif badge_id == "scholar" and len(profile.topic_mastery) >= 5:
                earned = True
            elif badge_id == "polymath" and len(profile.topic_mastery) >= 15:
                earned = True
            elif badge_id == "night_owl":
                current_hour = datetime.now().hour
                if 22 <= current_hour or current_hour <= 6:
                    earned = True
            elif badge_id == "early_bird":
                current_hour = datetime.now().hour
                if 5 <= current_hour <= 8:
                    earned = True
            elif badge_id == "quiz_god":
                level_info = self.gamification.get_level_info(profile.total_xp)
                if level_info["level"] >= 20:
                    earned = True
            
            if earned:
                profile.earned_badges.add(badge_id)
                profile.total_xp += badge.xp_reward
                profile.coins += badge.coins_reward
                new_badges.append(badge)
        
        return new_badges

    def get_dashboard_data(self, profile: UserProfile) -> Dict:
        """Return dashboard data as dictionary instead of printing"""
        level_info = self.gamification.get_level_info(profile.total_xp)
        accuracy = (profile.total_correct / max(profile.total_questions, 1)) * 100
        
        recent_badges = []
        recent_badge_ids = list(profile.earned_badges)[-5:] if profile.earned_badges else []
        for badge_id in recent_badge_ids:
            badge = self.gamification.badges.get(badge_id)
            if badge:
                recent_badges.append({
                    "id": badge_id,
                    "name": badge.name,
                    "description": badge.description,
                    "icon": badge.icon,
                    "rarity": badge.rarity
                })
        
        top_topics = []
        if profile.topic_mastery:
            sorted_topics = sorted(profile.topic_mastery.items(), key=lambda x: x[1], reverse=True)[:3]
            top_topics = [{"topic": topic, "count": count} for topic, count in sorted_topics]
        
        return {
            "username": profile.username,
            "level": level_info["level"],
            "title": level_info["title"],
            "total_xp": profile.total_xp,
            "coins": profile.coins,
            "current_streak": profile.current_streak,
            "best_streak": profile.best_streak,
            "badges_earned": len(profile.earned_badges),
            "total_badges": len(self.gamification.badges),
            "accuracy": round(accuracy, 1),
            "level_progress": round(level_info["progress"], 1),
            "xp_to_next": level_info["xp_to_next"],
            "is_max_level": level_info["is_max"],
            "total_questions": profile.total_questions,
            "total_correct": profile.total_correct,
            "daily_questions": profile.daily_stats["questions_answered"],
            "fast_answers_today": profile.daily_stats["fast_answers"],
            "perfect_answers": profile.daily_stats.get("perfect_answers", 0),
            "topics_mastered": len(profile.topic_mastery),
            "recent_badges": recent_badges,
            "top_topics": top_topics
        }

    def get_all_badges(self, profile: UserProfile) -> Dict:
        """Return all badges organized by category"""
        categories = defaultdict(list)
        
        for badge_id, badge in self.gamification.badges.items():
            categories[badge.category].append({
                "id": badge_id,
                "name": badge.name,
                "description": badge.description,
                "icon": badge.icon,
                "rarity": badge.rarity,
                "xp_reward": badge.xp_reward,
                "coins_reward": badge.coins_reward,
                "earned": badge_id in profile.earned_badges
            })
        
        return {
            "categories": dict(categories),
            "earned_count": len(profile.earned_badges),
            "total_count": len(self.gamification.badges),
            "completion_percentage": round((len(profile.earned_badges) / len(self.gamification.badges)) * 100, 1)
        }

    async def generate_quiz_questions(self, username: str, quiz_input: str) -> Dict:
        """Generate quiz questions and return as data structure"""
        profile = self.get_user_profile(username)
        self.session_questions.clear()
        
        level_info = self.gamification.get_level_info(profile.total_xp)
        params = self.parse_user_request(quiz_input)
        
        # Handle mixed format
        if params['format_type'] == 'mixed':
            formats = ["multiple_choice", "true_false", "fill_in_blank", "short_answer"]
            format_sequence = []
            for i in range(params['num_questions']):
                format_sequence.append(formats[i % len(formats)])
            random.shuffle(format_sequence)
        else:
            format_sequence = [params['format_type']] * params['num_questions']
        
        # Generate questions
        tasks = [
            self.generate_unique_question(params['topic'], params['difficulty'], fmt, profile)
            for fmt in format_sequence
        ]
        questions = await asyncio.gather(*tasks)
        questions = [q for q in questions if q is not None]
        
        if not questions:
            return {
                "success": False,
                "error": "Unable to generate questions. Please try a different topic!"
            }
        
        # Convert questions to serializable format
        questions_data = []
        for q in questions:
            questions_data.append({
                "unique_id": q.unique_id,
                "question": q.question,
                "options": q.options,
                "format_type": q.format_type,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "correct_answer": q.correct_answer,      
                "explanation": q.explanation,
                "question_hash": q.question_hash,
                "fun_fact": q.fun_fact
            })
        
        return {
            "success": True,
            "username": username,
            "level": level_info["level"],
            "title": level_info["title"],
            "topic": params["topic"],
            "difficulty": params["difficulty"],
            "num_questions": len(questions),
            "questions": questions_data,
            "current_streak": profile.current_streak
        }

    async def submit_answer(self, username: str, question_id: str, user_answer: str, response_time: float) -> Dict:
        """Submit an answer and return the result"""
        profile = self.get_user_profile(username)
        
        
        return {
            "success": False,
            "error": "Question session management needs to be implemented"
        }

    async def evaluate_quiz_session(self, username: str, answers: list,questions:list) -> Dict:
        """Evaluate a complete quiz session"""
        profile = self.get_user_profile(username)
        level_info = self.gamification.get_level_info(profile.total_xp)
        
        questions = questions
        answers = answers
        
        session_xp = 0
        session_correct = 0
        perfect_answers = 0
        new_badges = []
        level_ups = []
        
        # Process each answer
        for i, (q_data, answer_data) in enumerate(zip(questions, answers)):
    # Handle case where q_data might be missing required fields
            if not isinstance(q_data, dict):
                continue
    
    # Reconstruct question object with safe defaults
            question = QuizQuestion(
                question=q_data.get("question", ""),
                correct_answer=q_data.get("correct_answer", "A"),  # Default if missing
                explanation=q_data.get("explanation", "No explanation available"),
                topic=q_data.get("topic", "Unknown"),
                difficulty=q_data.get("difficulty", "medium"),
                format_type=q_data.get("format_type", "multiple_choice"),
                options=q_data.get("options", []),
                unique_id=q_data.get("unique_id", ""),
                question_hash=q_data.get("question_hash", ""),
                fun_fact=q_data.get("fun_fact", "")
            )
            
            user_answer = answer_data.get("answer", "")
            response_time = answer_data.get("response_time", 5.0)
            
            # Update profile stats
            profile.total_questions += 1
            profile.daily_stats["questions_answered"] += 1
            profile.daily_stats["topics_tried"].add(q_data["topic"])
            
            # Update topic mastery
            if q_data["topic"] not in profile.topic_mastery:
                profile.topic_mastery[q_data["topic"]] = 0
            
            # Evaluate answer
            is_correct = self.evaluate_answer(question, user_answer)
            
            if is_correct:
                profile.current_streak += 1
                profile.best_streak = max(profile.best_streak, profile.current_streak)
                profile.total_correct += 1
                profile.daily_stats["correct_answers"] += 1
                profile.topic_mastery[q_data["topic"]] += 1
                session_correct += 1
                
                # Track fast answers
                if response_time <= 3:
                    profile.daily_stats["fast_answers"] += 1
                if response_time <= 1.5:
                    profile.daily_stats["ultra_fast_answers"] = profile.daily_stats.get("ultra_fast_answers", 0) + 1
                
                # Perfect answer
                if response_time <= 2:
                    perfect_answers += 1
                    profile.daily_stats["perfect_answers"] = profile.daily_stats.get("perfect_answers", 0) + 1
                
                # Calculate XP
                old_xp = profile.total_xp
                old_level_info = self.gamification.get_level_info(old_xp)
                
                xp_earned = self.gamification.calculate_xp(
                    is_correct, q_data["difficulty"], response_time, 
                    profile.current_streak - 1, level_info["level"]
                )
                profile.total_xp += xp_earned
                session_xp += xp_earned
                
                # Check for level up
                new_level_info = self.gamification.get_level_info(profile.total_xp)
                if new_level_info["level"] > old_level_info["level"]:
                    profile.coins += 100
                    level_ups.append({
                        "new_level": new_level_info["level"],
                        "new_title": new_level_info["title"],
                        "bonus_coins": 100
                    })
                
                # Store answer result
                answers[i]["is_correct"] = True
                answers[i]["xp_earned"] = xp_earned
                answers[i]["explanation"] = question.explanation
                answers[i]["fun_fact"] = question.fun_fact
            else:
                profile.current_streak = 0
                answers[i]["is_correct"] = False
                answers[i]["xp_earned"] = 0
                answers[i]["correct_answer"] = question.correct_answer
                answers[i]["explanation"] = question.explanation
                answers[i]["fun_fact"] = question.fun_fact
        
        # Check badge unlocks
        new_badges = self.check_badge_unlocks(profile)
        badges_data = []
        for badge in new_badges:
            badges_data.append({
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "icon": badge.icon,
                "rarity": badge.rarity,
                "xp_reward": badge.xp_reward,
                "coins_reward": badge.coins_reward
            })
        
        # Calculate accuracy
        accuracy = (session_correct / len(questions)) * 100 if questions else 0
        
        # Save progress
        self.save_user_data()
        
        # Get updated level info
        final_level_info = self.gamification.get_level_info(profile.total_xp)
        
        return {
            "success": True,
            "session_correct": session_correct,
            "total_questions": len(questions),
            "accuracy": round(accuracy, 1),
            "session_xp": session_xp,
            "total_xp": profile.total_xp,
            "current_streak": profile.current_streak,
            "best_streak": profile.best_streak,
            "coins": profile.coins,
            "perfect_answers": perfect_answers,
            "level": final_level_info["level"],
            "title": final_level_info["title"],
            "level_progress": round(final_level_info["progress"], 1),
            "xp_to_next": final_level_info["xp_to_next"],
            "is_max_level": final_level_info["is_max"],
            "level_ups": level_ups,
            "new_badges": badges_data,
            "answers": answers
        }


# ======================
# SINGLE WEB API FUNCTION
# ======================

async def main(user_input: Dict) -> Dict:
    """
    Single unified function to handle all quiz operations.
    
    Args:
        user_input: Dictionary with structure:
        {
            "action": "dashboard" | "badges" | "generate_quiz" | "evaluate_session",
            "username": str,
            "data": str | Dict (optional, depends on action)
        }
    
    Returns:
        Dictionary with response data
    
    Examples:
        # Get dashboard
        result = await main({"action": "dashboard", "username": "John"})
        
        # Get badges
        result = await main({"action": "badges", "username": "John"})
        
        # Generate quiz
        result = await main({
            "action": "generate_quiz", 
            "username": "John",
            "data": "5 medium questions about space"
        })
        
        # Evaluate session
        result = await main({
            "action": "evaluate_session",
            "username": "John",
            "data": {
                "questions": [...],
                "answers": [...]
            }
        })
    """
    
    try:
        action = user_input.get("action")
        username = user_input.get("username")
        data = user_input.get("data")
        
        if not action or not username:
            return {
                "success": False,
                "error": "Missing required fields: 'action' and 'username'"
            }
        
        agent = EnhancedGamifiedQuizAgent()
        
        # Route to appropriate handler
        if action == "dashboard":
            profile = agent.get_user_profile(username)
            result = agent.get_dashboard_data(profile)
            return {"success": True, "data": result}
        
        elif action == "badges":
            profile = agent.get_user_profile(username)
            result = agent.get_all_badges(profile)
            return {"success": True, "data": result}
        
        elif action == "generate_quiz":
            if not data or not isinstance(data, str):
                return {
                    "success": False,
                    "error": "Missing or invalid 'data' field. Expected quiz topic string."
                }
            result = await agent.generate_quiz_questions(username, data)
            return result
        
        elif action == "evaluate_session":
            if not data or not isinstance(data, dict):
                return {
                    "success": False,
                    "error": "Missing or invalid 'data' field. Expected session dictionary."
                }
            result = await agent.evaluate_quiz_session(username, data)
            return result
        
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}. Valid actions: dashboard, badges, generate_quiz, evaluate_session"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Internal error: {str(e)}"
        }


async def example_usage():
    """Example of how to use the main function"""
    
    # Example 1: Get dashboard
    print("=== GET DASHBOARD ===")
    result = await main({
        "action": "dashboard",
        "username": "TestUser"
    })
    print(json.dumps(result, indent=2))
    
    # Example 2: Get badges
    print("\n=== GET BADGES ===")
    result = await main({
        "action": "badges",
        "username": "TestUser"
    })
    print(json.dumps(result, indent=2))
    
    # Example 3: Generate quiz
    print("\n=== GENERATE QUIZ ===")
    result = await main({
        "action": "generate_quiz",
        "username": "TestUser",
        "data": "3 easy questions about math"
    })
    print(json.dumps(result, indent=2))
    
    # Example 4: Evaluate session
    print("\n=== EVALUATE SESSION ===")
    session_data = {
        "questions": [
            {
                "unique_id": "q1",
                "question": "What is 2+2?",
                "correct_answer": "4",
                "explanation": "Basic addition",
                "topic": "Math",
                "difficulty": "easy",
                "format_type": "short_answer",
                "options": None,
                "fun_fact": "Math is universal!"
            }
        ],
        "answers": [
            {
                "question_id": "q1",
                "answer": "4",
                "response_time": 2.5
            }
        ]
    }
    
    result = await main({
        "action": "evaluate_session",
        "username": "TestUser",
        "data": session_data
    })
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    # Run examples
    asyncio.run(example_usage())
