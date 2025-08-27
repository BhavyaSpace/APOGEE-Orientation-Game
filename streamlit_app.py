# streamlit_app.py
# APOGEE Space Club – Main Hub
# Centralized Google Sheets leaderboard

import os
from datetime import datetime
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

############################
# ---- CONFIGURABLES ---- #
############################
APP_TITLE = "APOGEE Space Club – Cadet Trials 🚀"
SHEET_NAME = os.environ.get("APOGEE_SHEET_NAME", "Apogee_Cadet_Trials")
WORKSHEET_NAME = "Leaderboard"

############################
# ---- GOOGLE SHEETS ---- #
############################
def get_gspread_client():
    try:
        creds_file = "service_account.json"
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"❌ Google Sheets auth failed: {e}")
        return None

def save_to_google_sheets(game, entry):
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
            ws = sh.worksheet(WORKSHEET_NAME)
        except Exception:
            ws = sh.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=10)
            ws.append_row(["Game", "Nickname", "Name", "Branch", "Score", "Time"])
        ws.append_row([
            game,
            entry["nickname"],
            entry["name"],
            entry["branch"],
            entry["score"],
            entry.get("time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ])
    except Exception as e:
        st.error(f"❌ Error saving to Google Sheets: {e}")

def load_leaderboard():
    client = get_gspread_client()
    if not client:
        return {"mission_game": [], "quiz_game": []}
    try:
        sh = client.open(SHEET_NAME)
        ws = sh.worksheet(WORKSHEET_NAME)
        rows = ws.get_all_records()
        data = {"mission_game": [], "quiz_game": []}
        for row in rows:
            entry = {
                "nickname": row.get("Nickname"),
                "name": row.get("Name"),
                "branch": row.get("Branch"),
                "score": int(row.get("Score", 0)),
                "time": row.get("Time")
            }
            if row.get("Game") == "mission_game":
                data["mission_game"].append(entry)
            elif row.get("Game") == "quiz_game":
                data["quiz_game"].append(entry)
        return data
    except Exception as e:
        st.error(f"❌ Error loading leaderboard: {e}")
        return {"mission_game": [], "quiz_game": []}

############################
# ---- NICKNAME GEN ---- #
############################
def generate_fun_nickname(name: str) -> str:
    base = (name.strip().split()[0] if name.strip() else "Cadet").lower()
    base = "".join(ch for ch in base if ch.isalpha())[:5].capitalize()
    prefixes = ["Zap", "Neo", "Geo", "Vex", "Blu", "Zen", "Pyro", "Quip", "Nova", "Tiki"]
    suffixes = ["tron", "pop", "bit", "do", "ster", "zo", "ly", "ix", "o", "a"]
    h = sum(ord(c) for c in name) if name else 999
    return f"{prefixes[h % len(prefixes)]}{base}{suffixes[(h // len(prefixes)) % len(suffixes)]}"

############################
# ---- MAIN APP ---- #
############################
st.set_page_config(page_title=APP_TITLE, page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")

if "page" not in st.session_state:
    st.session_state["page"] = "form"
if "user" not in st.session_state:
    st.session_state["user"] = None

st.title(APP_TITLE)

# === Registration Form ===
if st.session_state["page"] == "form":
    st.subheader("🚀 Enroll as a Cadet")
    with st.form("reg_form", clear_on_submit=False):
        name = st.text_input("Full Name *")
        email = st.text_input("Email *")
        branch = st.text_input("Branch/Department *")
        agree = st.checkbox("I agree to share my details with APOGEE Space Club")
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
    st.success(f"👨‍🚀 **Astronaut ID:** {user.get('astronaut_name')} | {user.get('name')} ({user.get('branch')})")
    st.subheader("🎯 Choose Your Mission")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Play Mission Game", use_container_width=True, type="primary"):
            st.session_state["game_user"] = user
            st.switch_page("pages/mission_game.py")
    with col2:
        if st.button("🛰️ Play Quiz Game", use_container_width=True, type="primary"):
            st.session_state["game_user"] = user
            st.switch_page("pages/quiz_game.py")
    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
        if st.button("📊 View Leaderboard", use_container_width=True):
            st.session_state["page"] = "leaderboard"
            st.rerun()
    with col4:
        if st.button("🔄 New Registration", use_container_width=True):
            st.session_state["page"] = "form"
            st.session_state["user"] = None
            st.session_state.pop("game_user", None)
            st.rerun()

# === Leaderboard ===
elif st.session_state["page"] == "leaderboard":
    st.subheader("🏆 Leaderboards")
    data = load_leaderboard()
    tab1, tab2 = st.tabs(["🚀 Mission Game", "🛰️ Quiz Game"])
    with tab1:
        if data.get("mission_game"):
            sorted_missions = sorted(data["mission_game"], key=lambda x: (-x["score"], x.get("time", "")))
            for i, entry in enumerate(sorted_missions[:10], 1):
                st.write(f"**{i}.** {entry['nickname']} - {entry['name']} ({entry['branch']}) | {entry['score']} | {entry['time']}")
        else:
            st.info("🚀 No mission attempts yet.")
    with tab2:
        if data.get("quiz_game"):
            sorted_quiz = sorted(data["quiz_game"], key=lambda x: -x["score"])
            for i, entry in enumerate(sorted_quiz[:10], 1):
                st.write(f"**{i}.** {entry['nickname']} - {entry['name']} ({entry['branch']}) | {entry['score']}")
        else:
            st.info("🛰️ No quiz attempts yet.")
    if st.button("🏠 Back to Menu", use_container_width=True):
        st.session_state["page"] = "menu"
        st.rerun()
