# streamlit_app.py
# APOGEE Space Club – Main Hub
# Features:
# - Registration -> Menu -> Choose Game -> Leaderboard
# - Links to separate game apps
# - Centralized user management and leaderboards

import os
import json
from datetime import datetime
import streamlit as st

############################
# ---- CONFIGURABLES ---- #
############################
APP_TITLE = "APOGEE Space Club – Cadet Trials 🚀"
LEADERBOARD_FILE = "leaderboard.json"

############################
# ---- NICKNAME GEN ---- #
############################
def generate_fun_nickname(name: str) -> str:
    base = (name.strip().split()[0] if name.strip() else "Cadet").lower()
    base = "".join(ch for ch in base if ch.isalpha())[:5].capitalize()
    prefixes = ["Zap", "Neo", "Geo", "Vex", "Blu", "Zen", "Pyro", "Quip", "Nova", "Tiki"]
    suffixes = ["tron", "pop", "bit", "do", "ster", "zo", "ly", "ix", "o", "a"]
    h = sum(ord(c) for c in name) if name else 999
    p = prefixes[h % len(prefixes)]
    s = suffixes[(h // len(prefixes)) % len(suffixes)]
    return f"{p}{base}{s}"

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

############################
# ---- MAIN APP ---- #
############################
st.set_page_config(
    page_title=APP_TITLE, 
    page_icon="🚀", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "page" not in st.session_state:
    st.session_state["page"] = "form"
if "user" not in st.session_state:
    st.session_state["user"] = None

st.title(APP_TITLE)

# === Registration Form ===
if st.session_state["page"] == "form":
    st.subheader("🚀 Enroll as a Cadet")
    st.write("Welcome to the APOGEE Space Club Cadet Trials! Complete the registration to access mission simulations and quizzes.")
    
    with st.form("reg_form", clear_on_submit=False):
        name = st.text_input("Full Name *", placeholder="Enter your full name")
        email = st.text_input("Email *", placeholder="your.email@example.com")
        branch = st.text_input("Branch/Department *", placeholder="ECE / CSE / ME / EE / etc.")
        agree = st.checkbox("I agree to share my details with APOGEE Space Club for club communications and updates.")
        submitted = st.form_submit_button("🚀 Start Cadet Trials", use_container_width=True)
        
    if submitted:
        if not (name and email and branch and agree):
            st.error("⚠️ Please fill all required fields and provide consent.")
        else:
            nickname = generate_fun_nickname(name)
            st.session_state["user"] = {
                "name": name.strip(),
                "email": email.strip(),
                "branch": branch.strip(),
                "astronaut_name": nickname,
            }
            st.session_state["page"] = "menu"
            st.success(f"✅ Registration successful! Your Astronaut ID: **{nickname}**")
            st.rerun()

# === Main Menu ===
elif st.session_state["page"] == "menu":
    user = st.session_state.get("user", {})
    
    # User info header
    st.success(f"👨‍🚀 **Astronaut ID:** {user.get('astronaut_name','Cadet')} | {user.get('name','')} ({user.get('branch','')})")
    
    st.subheader("🎯 Choose Your Mission")
    st.write("Select a challenge to test your space knowledge and skills:")
    
    # Game options with descriptions
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 Mission Game
        **Landing Sequence Challenge**
        - Arrange mission steps in correct order
        - Real-time countdown (45 seconds)
        - Test your mission planning skills
        """)
        if st.button("🚀 Play Mission Game", use_container_width=True, type="primary"):
            # Store user data for the game apps
            st.session_state["game_user"] = user
            st.switch_page("pages/mission_game.py")
    
    with col2:
        st.markdown("""
        ### 🛰️ Quiz Game  
        **Space Knowledge Test**
        - Multiple choice questions
        - Physics and space concepts
        - 15 seconds per question
        """)
        if st.button("🛰️ Play Quiz Game", use_container_width=True, type="primary"):
            # Store user data for the game apps
            st.session_state["game_user"] = user
            st.switch_page("pages/quiz_game.py")
    
    st.markdown("---")
    
    # Additional options
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("📊 View Leaderboard", use_container_width=True):
            st.session_state["page"] = "leaderboard"
            st.rerun()
    
    with col4:
        if st.button("🔄 New Cadet Registration", use_container_width=True):
            st.session_state["page"] = "form"
            st.session_state["user"] = None
            st.session_state.pop("game_user", None)
            st.rerun()

# === Leaderboard Page ===
elif st.session_state["page"] == "leaderboard":
    st.subheader("🏆 Leaderboards")
    data = load_leaderboard()

    tab1, tab2 = st.tabs(["🚀 Mission Game", "🛰️ Quiz Game"])
    
    with tab1:
        st.write("**Mission Game Rankings** (Best performers first)")
        if data.get("mission_game"):
            # Sort by score (descending) then by time (ascending for same scores)
            sorted_missions = sorted(data["mission_game"], key=lambda x: (-x["score"], x.get("time", "")))
            for i, entry in enumerate(sorted_missions[:10], 1):  # Top 10
                score_icon = "🥇" if entry["score"] == 1 else "❌"
                st.write(f"**{i}.** {score_icon} **{entry['nickname']}** - {entry['name']} ({entry['branch']}) | {entry.get('time', 'N/A')}")
        else:
            st.info("🚀 No mission attempts yet. Be the first to try!")

    with tab2:
        st.write("**Quiz Game Rankings** (Highest scores first)")
        if data.get("quiz_game"):
            # Sort by score descending
            sorted_quiz = sorted(data["quiz_game"], key=lambda x: -x["score"])
            for i, entry in enumerate(sorted_quiz[:10], 1):  # Top 10
                stars = "⭐" * min(entry["score"], 5)  # Max 5 stars
                st.write(f"**{i}.** {stars} **{entry['nickname']}** - {entry['name']} ({entry['branch']}) | Score: {entry['score']}")
        else:
            st.info("🛰️ No quiz attempts yet. Be the first to try!")

    st.markdown("---")
    if st.button("🏠 Back to Menu", use_container_width=True):
        st.session_state["page"] = "menu"
        st.rerun()

# === Footer ===
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
    🚀 APOGEE Space Club | Cadet Trials v2.0<br>
    Contact us for any issues or questions
</div>
""", unsafe_allow_html=True)