import bcrypt
import pandas as pd
import os
import streamlit as st
from lang import swahili, english

USERS_FILE = "data/users.csv"

def load_users():
    if not os.path.exists(USERS_FILE):
        return pd.DataFrame(columns=["username", "password"])
    return pd.read_csv(USERS_FILE)

def save_users(df):
    os.makedirs("data", exist_ok=True)
    df.to_csv(USERS_FILE, index=False)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def signup(username, password):
    lang = st.session_state.get("language", "Swahili")
    t = swahili if lang == "Swahili" else english
    
    df = load_users()
    if username in df["username"].values:
        return False, t["username_exists"]

    hashed_pwd = hash_password(password)
    new_user = pd.DataFrame([{"username": username, "password": hashed_pwd}])
    df = pd.concat([df, new_user], ignore_index=True)
    save_users(df)
    
    # Return the complete translated message
    return True, t["signup_success"]

def login(username, password):
    # Get current language
    lang = st.session_state.get("language", "Swahili")
    t = swahili if lang == "Swahili" else english
    
    df = load_users()
    user = df[df["username"] == username]
    
    # User not found
    if user.empty:
        return False, t["user_not_found"]
    
    # Check password
    hashed_pwd = user.iloc[0]["password"]
    if check_password(password, hashed_pwd):
        return True, t["login_success"]
    else:
        return False, t["incorrect_password"]