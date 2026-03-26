import streamlit as st
import pickle
import pandas as pd
import numpy as np
from pathlib import Path

# Page Configuration
st.set_page_config(page_title="IPL Win Predictor", page_icon="🏏", layout="centered")

# Custom CSS
st.markdown("""
<style>
.main-title { font-size: 40px; font-weight: bold; text-align: center; color: #6366f1; }
.sub-title { font-size: 18px; text-align: center; color: #888; margin-bottom: 24px; }
.result-text { font-size: 22px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Load model artifacts with proper file handling and error handling
BASE_DIR = Path(__file__).parent

@st.cache_resource
def load_artifacts():
    with open(BASE_DIR / 'model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open(BASE_DIR / 'scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    with open(BASE_DIR / 'columns.pkl', 'rb') as f:
        columns_list = pickle.load(f)
    return model, scaler, columns_list

try:
    model, scaler, columns_list = load_artifacts()
except Exception as e:
    st.error(f"Failed to load model files: {e}")
    st.stop()

# Headers
st.markdown('<div class="main-title">🏏 IPL Win Probability Predictor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Second innings chase simulator</div>', unsafe_allow_html=True)

# Current IPL teams
teams = [
    'Chennai Super Kings', 'Delhi Capitals', 'Gujarat Titans',
    'Kolkata Knight Riders', 'Lucknow Super Giants', 'Mumbai Indians',
    'Punjab Kings', 'Rajasthan Royals', 'Royal Challengers Bengaluru',
    'Sunrisers Hyderabad'
]

# All cities from model training data (32 venues)
cities = [
    'Ahmedabad', 'Bangalore', 'Bengaluru', 'Bloemfontein', 'Cape Town',
    'Centurion', 'Chandigarh', 'Chennai', 'Cuttack', 'Delhi',
    'Dharamsala', 'Dubai', 'Durban', 'East London', 'Guwahati',
    'Hyderabad', 'Indore', 'Jaipur', 'Johannesburg', 'Kimberley',
    'Kolkata', 'Lucknow', 'Mohali', 'Mumbai', 'Nagpur',
    'Navi Mumbai', 'Port Elizabeth', 'Pune', 'Raipur', 'Ranchi',
    'Sharjah', 'Visakhapatnam'
]

# User Inputs
st.markdown("### 🏟️ Match Details")
col1, col2 = st.columns(2)
with col1:
    batting_team = st.selectbox('🏏 Batting Team', sorted(teams))
with col2:
    bowling_team = st.selectbox('🥎 Bowling Team', sorted(teams))

city = st.selectbox('📍 Host City', sorted(cities))

st.markdown("---")

st.markdown("### 📊 Current Situation")
col3, col4 = st.columns(2)
with col3:
    target = st.number_input('🎯 Target Score', min_value=0, step=1)
with col4:
    score = st.number_input('🏏 Current Score', min_value=0, step=1)

# Separate overs and balls inputs to avoid floating point issues
col5, col6, col7 = st.columns(3)
with col5:
    overs_completed = st.number_input('⏱️ Overs (0-20)', min_value=0, max_value=20, step=1)
with col6:
    balls_in_over = st.number_input('🏐 Balls (0-5)', min_value=0, max_value=5, step=1)
with col7:
    wickets = st.number_input('❌ Wickets Out', min_value=0, max_value=10, step=1)

# Auto-correct: if 20 overs, balls must be 0
if overs_completed == 20:
    balls_in_over = 0

st.markdown("---")

# Prediction
if st.button('🚀 Predict Winning Probability', use_container_width=True):

    if batting_team == bowling_team:
        st.warning("⚠️ Batting and Bowling teams cannot be the same!")
    elif target == 0:
        st.warning("⚠️ Please enter a valid Target Score.")
    elif overs_completed == 0 and balls_in_over == 0:
        st.warning("⚠️ Please enter overs > 0 to calculate Run Rate.")
    elif score >= target:
        st.success(f"🎉 {batting_team} has already won the match!")
    elif wickets == 10:
        st.error(f"❌ {batting_team} is all out. {bowling_team} won!")
    else:
        # Calculate total balls bowled
        balls_completed = overs_completed * 6 + balls_in_over
        balls_left = 120 - balls_completed

        if balls_left <= 0:
            st.error("❌ Innings is over (20 overs completed).")
        else:
            with st.spinner('Calculating Probabilities...'):
                # Feature Engineering
                runs_left = target - score
                wicket_left = 10 - wickets
                crr = (score / balls_completed) * 6 if balls_completed > 0 else 0
                rrr = (runs_left / balls_left) * 6 if balls_left > 0 else 0

                # Build input DataFrame
                input_data = pd.DataFrame(columns=columns_list)
                input_data.loc[0] = 0

                input_data['runs_left'] = runs_left
                input_data['balls_left'] = balls_left
                input_data['wicket_left'] = wicket_left
                input_data['total_runs_x'] = target
                input_data['crr'] = crr
                input_data['rrr'] = rrr

                # One-hot encode team and city
                batting_col = 'batting_team_' + batting_team
                bowling_col = 'bowling_team_' + bowling_team
                city_col = 'city_' + city

                if batting_col in columns_list:
                    input_data[batting_col] = 1
                if bowling_col in columns_list:
                    input_data[bowling_col] = 1
                if city_col in columns_list:
                    input_data[city_col] = 1

                # Scale numerical features only
                num_cols = ['runs_left', 'balls_left', 'wicket_left', 'total_runs_x', 'crr', 'rrr']
                input_data[num_cols] = scaler.transform(input_data[num_cols])

                # Predict
                result = model.predict_proba(input_data)[0]
                loss_prob = result[0]
                win_prob = result[1]

                # Display Results
                st.markdown("### 🏆 Prediction Results")

                st.markdown(f'<div class="result-text">{batting_team}</div>', unsafe_allow_html=True)
                st.progress(win_prob, text=f"{round(win_prob * 100, 1)}%")

                st.markdown(f'<div class="result-text">{bowling_team}</div>', unsafe_allow_html=True)
                st.progress(loss_prob, text=f"{round(loss_prob * 100, 1)}%")

                st.info(
                    f"📈 **CRR:** {round(crr, 2)} | **RRR:** {round(rrr, 2)} | "
                    f"**Runs Left:** {runs_left} | **Balls Left:** {balls_left}"
                )
