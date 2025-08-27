# pages/quiz_game.py
# APOGEE Space Club – Quiz Game (Separate App) 
# Multiple choice space knowledge quiz

import os
import random
import time
import json
from datetime import datetime
import streamlit as st

############################
# ---- CONFIGURABLES ---- #
############################
QUIZ_TIMER_SEC = 15
LEADERBOARD_FILE = "leaderboard.json" 
SHEET_ENABLED = True
SHEET_NAME = os.environ.get("APOGEE_SHEET_NAME", "APOGEE_Orientation_Responses")
GOOGLE_CREDS_JSON = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
GOOGLE_CREDS_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")

############################
# ---- GOOGLE SHEETS ---- #
############################
def get_gspread_client():
    if not SHEET_ENABLED:
        return None
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        creds_file = GOOGLE_CREDS_FILE
        if GOOGLE_CREDS_JSON:
            creds_file = "_sa_from_env.json"
            with open(creds_file, "w", encoding="utf-8") as f:
                f.write(GOOGLE_CREDS_JSON)

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets", 
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.warning(f"Google Sheets disabled: {e}")
        return None

def append_row_to_sheet(row):
    if not SHEET_ENABLED:
        return
    client = get_gspread_client()
    if not client:
        return
    try:
        sh = None
        try:
            sh = client.open(SHEET_NAME)
        except Exception:
            sh = client.create(SHEET_NAME)
        try:
            ws = sh.worksheet("Quiz_Game")
        except Exception:
            ws = sh.add_worksheet(title="Quiz_Game", rows=1000, cols=15)
            ws.append_row([
                "timestamp", "name", "email", "branch", "astronaut_name",
                "total_questions", "correct_answers", "score", "question_ids",
                "user_answers", "correct_answers_detail", "time_taken", "notes",
            ])
        ws.append_row(row)
    except Exception as e:
        st.error(f"Sheet error: {e}")

############################
# ---- LEADERBOARD ---- #
############################
def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return {"mission_game": [], "quiz_game": []}
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"mission_game": [], "quiz_game": []}

def save_leaderboard(data):
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def add_score(game_key, name, branch, nickname, score):
    data = load_leaderboard()
    entry = {
        "name": name,
        "branch": branch,
        "nickname": nickname,
        "score": score,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    data.setdefault(game_key, []).append(entry)
    save_leaderboard(data)

############################
# ---- QUIZ DATA ---- #
############################
QUIZ_POOL = [
    {
        "id": "q1",
        "q": "On the Moon (g≈1.6 m/s²), you drop a tool from 3.6 m height. Approximate time to hit surface?",
        "options": ["1.5 seconds", "2.1 seconds", "2.8 seconds", "3.0 seconds"],
        "answer_idx": 1,
        "explain": "Using t = √(2h/g) = √(2×3.6/1.6) ≈ 2.12 seconds"
    },
    {
        "id": "q2", 
        "q": "If a LEO satellite doubles its orbital radius, its orbital speed becomes:",
        "options": ["Same speed", "2× faster", "1/√2 slower", "√2 faster"],
        "answer_idx": 2,
        "explain": "Orbital speed v ∝ 1/√r, so doubling radius reduces speed by factor √2"
    },
    {
        "id": "q3",
        "q": "Complete the countdown code:\n```python\nimport time\nn = 10\nwhile n > 0:\n    print(n)\n    time.sleep(1)\n    n = n __ 1\nprint('LIFTOFF!')\n```",
        "options": ["+ (plus)", "- (minus)", "* (multiply)", "/ (divide)"],
        "answer_idx": 1,
        "explain": "Need to decrement n, so n = n - 1 (or n -= 1)"
    },
    {
        "id": "q4",
        "q": "Which celestial body requires the highest escape velocity?",
        "options": ["Moon", "Mars", "Earth", "Jupiter"], 
        "answer_idx": 3,
        "explain": "Jupiter has the highest escape velocity (~59.5 km/s) due to its massive size"
    },
    {
        "id": "q5",
        "q": "What is the orbital period of a geostationary satellite?",
        "options": ["12 hours", "24 hours", "36 hours", "48 hours"],
        "answer_idx": 1,
        "explain": "Geostationary satellites orbit in 24 hours to match Earth's rotation"
    },
    {
        "id": "q6",
        "q": "The first artificial satellite launched by India was:",
        "options": ["Rohini-1", "Aryabhata", "Bhaskara-1", "IRS-1A"],
        "answer_idx": 1,
        "explain": "Aryabhata was India's first satellite, launched in 1975"
    },
    {
        "id": "q7",
        "q": "In space, the primary method of heat transfer is:",
        "options": ["Conduction", "Convection", "Radiation", "All equally"],
        "answer_idx": 2,
        "explain": "In vacuum, only radiation can transfer heat (no medium for conduction/convection)"
    }
]

############################
# ---- TIMER FUNCTIONS ---- #
############################
def seconds_left(start_time, duration):
    elapsed = time.time() - start_time
    return max(0, int(duration - elapsed))

def format_time(seconds):
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

############################
# ---- MAIN QUIZ APP ---- #
############################
st.set_page_config(
    page_title="Quiz Game - APOGEE Space Club",
    page_icon="🛰️", 
    layout="centered"
)

# Check if user data exists
if "game_user" not in st.session_state:
    st.error("❌ No user data found. Please register first.")
    if st.button("🏠 Go to Main App"):
        st.switch_page("streamlit_app.py")
    st.stop()

user = st.session_state["game_user"]

st.title("🛰️ Space Knowledge Quiz")
st.caption(f"Astronaut: **{user['astronaut_name']}** | {user['name']} ({user['branch']})")

# Initialize quiz state only once
if "quiz_state" not in st.session_state:
    # Select 3 random questions for this quiz session
    selected_questions = random.sample(QUIZ_POOL, min(3, len(QUIZ_POOL)))
    
    st.session_state["quiz_state"] = {
        "questions": selected_questions,
        "current_question": 0,
        "answers": [],
        "start_time": time.time(),
        "question_start_time": time.time(),
        "quiz_complete": False,
        "data_saved": False,
        "selected_answer": None,
        "answer_submitted": False
    }

state = st.session_state["quiz_state"]

# Quiz complete - show results
if state["quiz_complete"]:
    st.markdown("### 🎯 Quiz Complete!")
    
    correct_count = sum(1 for ans in state["answers"] if ans["correct"])
    total_questions = len(state["questions"])
    
    # Show score with visual feedback
    if correct_count == total_questions:
        st.success(f"🎉 **PERFECT SCORE!** {correct_count}/{total_questions}")
        st.balloons()
    elif correct_count >= total_questions * 0.7:
        st.success(f"🌟 **EXCELLENT!** {correct_count}/{total_questions}")
    elif correct_count >= total_questions * 0.5:
        st.warning(f"📚 **GOOD EFFORT!** {correct_count}/{total_questions}")
    else:
        st.error(f"🔄 **KEEP LEARNING!** {correct_count}/{total_questions}")
    
    # Detailed results
    st.markdown("### 📊 Detailed Results")
    for i, (question, answer) in enumerate(zip(state["questions"], state["answers"])):
        with st.expander(f"Question {i+1}: {'✅' if answer['correct'] else '❌'}"):
            st.write(f"**Q:** {question['q']}")
            st.write(f"**Your Answer:** {answer['user_answer']}")
            st.write(f"**Correct Answer:** {question['options'][question['answer_idx']]}")
            if answer['correct']:
                st.success("✅ Correct!")
            else:
                st.error("❌ Incorrect")
                st.info(f"💡 **Explanation:** {question['explain']}")
            st.write(f"**Time taken:** {QUIZ_TIMER_SEC - answer['time_left']} seconds")
    
    # Save data only once
    if not state["data_saved"]:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare consolidated data for single sheet entry
        question_ids = [q["id"] for q in state["questions"]]
        user_answers = [ans["user_answer"] for ans in state["answers"]]
        correct_answers_detail = [state["questions"][i]["options"][state["questions"][i]["answer_idx"]] for i in range(len(state["questions"]))]
        total_time_taken = sum(QUIZ_TIMER_SEC - ans["time_left"] for ans in state["answers"])
        
        # Single row for entire quiz session
        row = [
            ts, user["name"], user["email"], user["branch"], user["astronaut_name"],
            str(total_questions), str(correct_count), str(correct_count), " | ".join(question_ids),
            " | ".join(user_answers), " | ".join(correct_answers_detail), str(total_time_taken),
            f"Quiz completed with {correct_count}/{total_questions} correct answers"
        ]
        append_row_to_sheet(row)
        
        # Save to leaderboard
        add_score("quiz_game", user["name"], user["branch"], user["astronaut_name"], correct_count)
        
        state["data_saved"] = True
        st.success("✅ Results saved successfully!")
    
    # Navigation buttons
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🏠 Main Menu", use_container_width=True):
            st.session_state.pop("quiz_state", None)
            st.switch_page("streamlit_app.py")
    
    with col2:
        if st.button("📊 Leaderboard", use_container_width=True):
            st.session_state.pop("quiz_state", None)
            # Set page to leaderboard in main app
            st.session_state["page"] = "leaderboard"
            st.switch_page("streamlit_app.py")
    
    with col3:
        if st.button("🔄 Play Again", use_container_width=True, type="primary"):
            st.session_state.pop("quiz_state", None)
            st.rerun()
    
    with col4:
        if st.button("🚀 Try Mission", use_container_width=True):
            st.session_state.pop("quiz_state", None)
            st.switch_page("pages/mission_game.py")

# Active quiz - show current question
else:
    current_q_data = state["questions"][state["current_question"]]
    
    # Timer for current question
    time_left = seconds_left(state["question_start_time"], QUIZ_TIMER_SEC)
    time_display = format_time(time_left)
    
    # Progress indicator
    progress = (state["current_question"] + 1) / len(state["questions"])
    st.progress(progress)
    
    # Question header
    st.markdown(f"### Question {state['current_question'] + 1} of {len(state['questions'])}")
    
    # Timer display
    if time_left > 10:
        st.success(f"⏱️ Time Remaining: **{time_display}**")
    elif time_left > 5:
        st.warning(f"⏱️ Time Remaining: **{time_display}**")
    else:
        st.error(f"⏱️ Time Remaining: **{time_display}**")
    
    # Show question
    st.markdown("---")
    st.markdown(f"**{current_q_data['q']}**")
    
    # Show options and handle selection
    if not state["answer_submitted"]:
        # Initialize selected answer if not set
        if state["selected_answer"] is None:
            state["selected_answer"] = current_q_data["options"][0]
        
        # Radio button for options (no auto-refresh to prevent state loss)
        selected = st.radio(
            "Choose your answer:",
            current_q_data["options"],
            index=current_q_data["options"].index(state["selected_answer"]),
            key=f"q_{state['current_question']}_radio"
        )
        state["selected_answer"] = selected
        
        # Submit button or auto-submit on timeout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submit_clicked = st.button("✅ Submit Answer", use_container_width=True, type="primary", disabled=(time_left <= 0))
        
        with col2:
            st.metric("Time", time_display)
        
        # Auto-submit when time runs out
        if time_left <= 0 or submit_clicked:
            # Process the answer
            user_answer = state["selected_answer"]
            correct_idx = current_q_data["answer_idx"]
            is_correct = (current_q_data["options"].index(user_answer) == correct_idx)
            
            # Store answer
            state["answers"].append({
                "user_answer": user_answer,
                "correct": is_correct,
                "time_left": time_left,
                "question_id": current_q_data["id"]
            })
            
            state["answer_submitted"] = True
            st.rerun()
    
    else:
        # Show feedback for submitted answer
        last_answer = state["answers"][-1]
        
        if last_answer["correct"]:
            st.success("🎉 **Correct!** Well done!")
        else:
            st.error("❌ **Incorrect**")
            st.info(f"**Correct Answer:** {current_q_data['options'][current_q_data['answer_idx']]}")
            st.info(f"💡 **Explanation:** {current_q_data['explain']}")
        
        # Next question or finish
        if state["current_question"] + 1 < len(state["questions"]):
            if st.button("➡️ Next Question", use_container_width=True, type="primary"):
                # Move to next question
                state["current_question"] += 1
                state["question_start_time"] = time.time()
                state["selected_answer"] = None
                state["answer_submitted"] = False
                st.rerun()
        else:
            if st.button("🏁 Finish Quiz", use_container_width=True, type="primary"):
                state["quiz_complete"] = True
                st.rerun()