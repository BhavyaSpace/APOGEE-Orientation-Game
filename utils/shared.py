# utils/shared.py
# Shared utility functions for APOGEE Space Club apps

import os
import json
from datetime import datetime

############################
# ---- CONFIGURABLES ---- #
############################
LEADERBOARD_FILE = "leaderboard.json"
SHEET_ENABLED = True
SHEET_NAME = os.environ.get("APOGEE_SHEET_NAME", "APOGEE_Orientation_Responses")
GOOGLE_CREDS_JSON = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
GOOGLE_CREDS_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")

############################
# ---- GOOGLE SHEETS ---- #
############################
def get_gspread_client():
    """Get authenticated Google Sheets client"""
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
        print(f"Google Sheets client error: {e}")
        return None

def append_row_to_sheet(row):
    """Append a row to the Google Sheet (thread-safe)"""
    if not SHEET_ENABLED:
        return
    
    client = get_gspread_client()
    if not client:
        return
        
    try:
        # Open or create spreadsheet
        try:
            sh = client.open(SHEET_NAME)
        except Exception:
            sh = client.create(SHEET_NAME)
        
        # Open or create worksheet
        try:
            ws = sh.worksheet("Responses")
        except Exception:
            ws = sh.add_worksheet(title="Responses", rows=1000, cols=20)
            # Add header row
            header = [
                "timestamp", "name", "email", "branch", "astronaut_name",
                "mission_or_q", "mission_correct", "mission_time_left",
                "physics_qid", "physics_correct", "physics_time_left", "notes",
            ]
            ws.append_row(header)
        
        # Append the data row
        ws.append_row(row)
        
    except Exception as e:
        print(f"Error appending to sheet: {e}")

############################
# ---- LEADERBOARD ---- #
############################
def load_leaderboard():
    """Load leaderboard data from JSON file"""
    if not os.path.exists(LEADERBOARD_FILE):
        return {"mission_game": [], "quiz_game": []}
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"mission_game": [], "quiz_game": []}

def save_leaderboard(data):
    """Save leaderboard data to JSON file"""
    try:
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving leaderboard: {e}")

def add_score(game_key, name, branch, nickname, score):
    """Add a score entry to the leaderboard"""
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
# ---- NICKNAME GEN ---- #
############################
def generate_fun_nickname(name: str) -> str:
    """Generate a fun astronaut nickname from real name"""
    base = (name.strip().split()[0] if name.strip() else "Cadet").lower()
    base = "".join(ch for ch in base if ch.isalpha())[:5].capitalize()
    
    prefixes = ["Zap", "Neo", "Geo", "Vex", "Blu", "Zen", "Pyro", "Quip", "Nova", "Tiki"]
    suffixes = ["tron", "pop", "bit", "do", "ster", "zo", "ly", "ix", "o", "a"]
    
    # Deterministic based on name hash
    h = sum(ord(c) for c in name) if name else 999
    p = prefixes[h % len(prefixes)]
    s = suffixes[(h // len(prefixes)) % len(suffixes)]
    
    return f"{p}{base}{s}"

############################
# ---- TIME UTILS ---- #
############################
import time

def seconds_left(start_time, duration):
    """Calculate seconds remaining from start time"""
    elapsed = time.time() - start_time
    return max(0, int(duration - elapsed))

def format_time(seconds):
    """Format seconds as MM:SS"""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"