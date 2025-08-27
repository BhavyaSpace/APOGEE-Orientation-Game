# pages/mission_game.py
# APOGEE Space Club – Mission Game (Separate App)
# Landing sequence challenge with timer

import os
import random
import time
import json
from datetime import datetime
import streamlit as st

############################
# ---- CONFIGURABLES ---- #
############################
MISSION_TIMER_SEC = 45
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
            ws = sh.worksheet("Mission_Game")
        except Exception:
            ws = sh.add_worksheet(title="Mission_Game", rows=1000, cols=15)
            ws.append_row([
                "timestamp", "name", "email", "branch", "astronaut_name",
                "mission_name", "mission_correct", "time_left_seconds", 
                "user_sequence", "correct_sequence", "score", "notes",
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
# ---- MISSION DATA ---- #
############################
MISSIONS = {
    "Chandrayaan-2": {
        "blurb": "🇮🇳 You are Mission Commander for Vikram lander's final descent. Stabilize, slow down, align, and achieve soft touchdown.",
        "emoji": "🌙",
        "steps_correct": [
            "🔄 Stabilize attitude using RCS thrusters",
            "⬇️ Reduce vertical descent rate", 
            "🚀 Adjust main engine thrust for soft descent",
            "🎯 Align lander over safe landing site",
            "🛑 Final braking burn",
            "🏁 Touchdown and engine cutoff",
        ],
    },
    "Apollo 11": {
        "blurb": "🇺🇸 Guide Eagle to Tranquility Base. Navigate hazards, manage fuel consumption, and land manually.",
        "emoji": "🌕",
        "steps_correct": [
            "🚀 Initiate powered descent (PDI)",
            "📡 Pitch over and acquire landing site",
            "🎮 Manual control to avoid boulder field", 
            "⚡ Reduce vertical and horizontal velocity",
            "🚁 Final descent and hover",
            "🛑 Engine shutdown at touchdown",
        ],
    },
    "Gaganyaan": {
        "blurb": "🇮🇳 Indian crewed mission profile. Ensure nominal ascent, orbital insertion, and safe crew recovery.",
        "emoji": "🛰️",
        "steps_correct": [
            "🚀 Liftoff and ascent monitoring",
            "💨 Max-Q passage and throttle management",
            "🔗 Stage separation and guidance to orbit",
            "👨‍🚀 Crew module separation", 
            "🔥 De-orbit burn and re-entry",
            "🪂 Drogue then main parachute deployment and splashdown",
        ],
    },
}

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
# ---- MAIN GAME APP ---- #
############################
st.set_page_config(
    page_title="Mission Game - APOGEE Space Club", 
    page_icon="🚀", 
    layout="centered"
)

# Check if user data exists
if "game_user" not in st.session_state:
    st.error("❌ No user data found. Please register first.")
    if st.button("🏠 Go to Main App"):
        st.switch_page("streamlit_app.py")
    st.stop()

user = st.session_state["game_user"]

st.title("🚀 Mission Landing Sequence")
st.caption(f"Astronaut: **{user['astronaut_name']}** | {user['name']} ({user['branch']})")

# Initialize game state only once
if "mission_state" not in st.session_state:
    mission_name = random.choice(list(MISSIONS.keys()))
    mission = MISSIONS[mission_name]
    
    st.session_state["mission_state"] = {
        "mission_name": mission_name,
        "mission": mission,
        "options": random.sample(mission["steps_correct"], len(mission["steps_correct"])),
        "selected_sequence": [],
        "start_time": time.time(),
        "game_over": False,
        "score": 0,
        "data_saved": False
    }

state = st.session_state["mission_state"]

# Show mission info
st.subheader(f"{state['mission']['emoji']} Mission: {state['mission_name']}")
st.info(state["mission"]["blurb"])

# Calculate time remaining
time_left = seconds_left(state["start_time"], MISSION_TIMER_SEC)
time_display = format_time(time_left)

# Show timer and progress (only update if game not over)
if not state["game_over"]:
    progress = min(1.0, (MISSION_TIMER_SEC - time_left) / MISSION_TIMER_SEC)
    st.progress(progress)
    
    # Color-code the timer
    if time_left > 20:
        st.success(f"⏱️ Time Remaining: **{time_display}**")
    elif time_left > 10:
        st.warning(f"⏱️ Time Remaining: **{time_display}**")
    else:
        st.error(f"⏱️ Time Remaining: **{time_display}**")
    
    # Auto-end game when time runs out
    if time_left <= 0 and not state["game_over"]:
        state["game_over"] = True
        st.rerun()

    # Show game interface if not completed
    # Add reset button for redoing sequence
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 🎯 Select Mission Steps in Correct Order")
    with col2:
        if st.button("🔄 Reset Order") and state["selected_sequence"]:
            state["selected_sequence"] = []
            st.rerun()
    
    st.write("📋 **Instructions:** Click the mission steps below in the proper chronological sequence:")
    
    # Mission reference guide
    with st.expander(f"📖 {state['mission_name']} Reference Guide"):
        if state['mission_name'] == "Chandrayaan-2":
            st.write("**🌙 Lunar Landing Sequence:**")
            st.write("• **RCS Thrusters**: Small attitude control rockets")
            st.write("• **Descent Rate**: Speed of coming down")
            st.write("• **Main Engine**: Primary propulsion system")
            st.write("• **Landing Site**: Safe, flat surface area")
            st.write("• **Braking Burn**: Final slowdown maneuver")
        elif state['mission_name'] == "Apollo 11":
            st.write("**🌕 Eagle Lander Sequence:**")
            st.write("• **PDI**: Powered Descent Initiation")
            st.write("• **Pitch Over**: Tilt to see landing site")
            st.write("• **Boulder Field**: Rocky hazardous area to avoid")
            st.write("• **Hover**: Stationary flight before touchdown")
        elif state['mission_name'] == "Gaganyaan":
            st.write("**🛰️ Crewed Mission Profile:**")
            st.write("• **Max-Q**: Maximum aerodynamic pressure")
            st.write("• **Stage Separation**: Jettison used rocket stages")
            st.write("• **Crew Module**: Astronaut compartment")
            st.write("• **De-orbit**: Burn to return to Earth")
    
    # Display options in a grid
    cols = st.columns(2)
    for i, step in enumerate(state["options"]):
        col = cols[i % 2]
        # Disable if already selected or time's up
        disabled = (step in state["selected_sequence"]) or (time_left <= 0)
        
        if col.button(
            step, 
            key=f"step_{i}", 
            disabled=disabled,
            help="Click to add this step to your sequence",
            use_container_width=True
        ):
            state["selected_sequence"].append(step)
            # Check if sequence is complete
            if len(state["selected_sequence"]) == len(state["options"]):
                state["game_over"] = True
            st.rerun()
    
    # Show current sequence
    st.markdown("### 📝 Your Current Sequence:")
    if state["selected_sequence"]:
        for idx, step in enumerate(state["selected_sequence"], 1):
            st.write(f"**{idx}.** {step}")
    else:
        st.write("*No steps selected yet. Click steps above to build your sequence.*")

# Game over - show results
else:
    # Stop any auto-refresh
    st.markdown("### 🎯 Mission Complete!")
    
    # Calculate score
    correct_sequence = state["mission"]["steps_correct"]
    is_correct = (state["selected_sequence"] == correct_sequence)
    state["score"] = 1 if is_correct else 0
    
    # Show results
    if is_correct:
        st.success("🎉 **PERFECT LANDING!** Your sequence was correct!")
        st.balloons()
    else:
        st.error("💥 **MISSION CRITICAL!** Sequence was incorrect.")
    
    # Show sequences comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Your Sequence:")
        if state["selected_sequence"]:
            for idx, step in enumerate(state["selected_sequence"], 1):
                st.write(f"**{idx}.** {step}")
        else:
            st.write("*No sequence completed*")
    
    with col2:
        st.markdown("#### Correct Sequence:")
        for idx, step in enumerate(correct_sequence, 1):
            # Highlight correct/incorrect steps
            if idx <= len(state["selected_sequence"]):
                if state["selected_sequence"][idx-1] == step:
                    st.write(f"✅ **{idx}.** {step}")
                else:
                    st.write(f"❌ **{idx}.** {step}")
            else:
                st.write(f"**{idx}.** {step}")
    
    # Save data only once
    if not state["data_saved"]:
        # Save to Google Sheets
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_seq = " → ".join(state["selected_sequence"]) if state["selected_sequence"] else "No sequence"
        correct_seq = " → ".join(correct_sequence)
        row = [
            ts, user["name"], user["email"], user["branch"], user["astronaut_name"],
            state["mission_name"], str(is_correct), str(time_left),
            user_seq, correct_seq, str(state["score"]), "Mission Game Completed"
        ]
        append_row_to_sheet(row)
        
        # Save to leaderboard
        add_score("mission_game", user["name"], user["branch"], user["astronaut_name"], state["score"])
        
        state["data_saved"] = True
        st.success("✅ Results saved successfully!")
    
    # Navigation buttons
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🏠 Main Menu", use_container_width=True):
            # Clear game state
            st.session_state.pop("mission_state", None)
            st.switch_page("streamlit_app.py")
    
    with col2:
        if st.button("📊 Leaderboard", use_container_width=True):
            # Clear game state and go to leaderboard
            st.session_state.pop("mission_state", None)
            st.session_state["page"] = "leaderboard"
            st.switch_page("streamlit_app.py")
    
    with col3:
        if st.button("🔄 Play Again", use_container_width=True, type="primary"):
            # Reset game state
            st.session_state.pop("mission_state", None)
            st.rerun()
    
    with col4:
        if st.button("🛰️ Try Quiz", use_container_width=True):
            # Clear game state and go to quiz
            st.session_state.pop("mission_state", None)
            st.switch_page("pages/quiz_game.py")