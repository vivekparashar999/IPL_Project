import os
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

# Base directory — absolute path, works from any working directory
BASE_DIR = Path(__file__).parent

@st.cache_resource
def load_artifacts():
    try:
        with open(BASE_DIR / 'model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open(BASE_DIR / 'scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        with open(BASE_DIR / 'columns.pkl', 'rb') as f:
            columns_list = pickle.load(f)
        return model, scaler, columns_list
    except FileNotFoundError as e:
        st.error(f"❌ Model file not found: {e}. Make sure model.pkl, scaler.pkl, columns.pkl are in the project folder.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Failed to load model: {e}")
        st.stop()

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

# All venues from model training data (30 venues)
venue_map = {
    # India
    'Ahmedabad - Narendra Modi Stadium, Gujarat': 'Ahmedabad',
    'Bengaluru - M. Chinnaswamy Stadium, Karnataka': 'Bengaluru',
    'Chennai - M.A. Chidambaram Stadium, Tamil Nadu': 'Chennai',
    'Cuttack - Barabati Stadium, Odisha': 'Cuttack',
    'Delhi - Arun Jaitley Stadium': 'Delhi',
    'Dharamsala - HPCA Stadium, Himachal Pradesh': 'Dharamsala',
    'Guwahati - Barsapara Stadium, Assam': 'Guwahati',
    'Hyderabad - Rajiv Gandhi Intl. Stadium, Telangana': 'Hyderabad',
    'Indore - Holkar Stadium, Madhya Pradesh': 'Indore',
    'Jaipur - Sawai Mansingh Stadium, Rajasthan': 'Jaipur',
    'Kolkata - Eden Gardens, West Bengal': 'Kolkata',
    'Lucknow - Ekana Stadium, Uttar Pradesh': 'Lucknow',
    'Mohali - I.S. Bindra PCA Stadium, Punjab': 'Mohali',
    'Mumbai - Wankhede Stadium, Maharashtra': 'Mumbai',
    'Nagpur - VCA Stadium, Maharashtra': 'Nagpur',
    'Navi Mumbai - DY Patil Stadium, Maharashtra': 'Navi Mumbai',
    'Pune - MCA Stadium, Maharashtra': 'Pune',
    'Raipur - Shaheed Veer Narayan Singh Intl. Stadium, Chhattisgarh': 'Raipur',
    'Ranchi - JSCA Intl. Stadium, Jharkhand': 'Ranchi',
    'Visakhapatnam - ACA-VDCA Stadium, Andhra Pradesh': 'Visakhapatnam',
    # UAE
    'Dubai - Dubai Intl. Cricket Stadium': 'Dubai',
    'Sharjah - Sharjah Cricket Stadium': 'Sharjah',
    # South Africa
    'Bloemfontein - OUTsurance Oval': 'Bloemfontein',
    'Cape Town - Newlands': 'Cape Town',
    'Centurion - SuperSport Park': 'Centurion',
    'Durban - Kingsmead': 'Durban',
    'East London - Buffalo Park': 'East London',
    'Johannesburg - Wanderers Stadium': 'Johannesburg',
    'Kimberley - De Beers Diamond Oval': 'Kimberley',
    "Port Elizabeth - St George's Park": 'Port Elizabeth',
}

# User Inputs
st.markdown("### 🏟️ Match Details")
col1, col2 = st.columns(2)
with col1:
    batting_team = st.selectbox('🏏 Batting Team', sorted(teams))
with col2:
    bowling_options = [t for t in sorted(teams) if t != batting_team]
    bowling_team = st.selectbox('🥎 Bowling Team', bowling_options)

city_label = st.selectbox('📍 Venue', list(venue_map.keys()))
city = venue_map[city_label]

st.markdown("---")

st.markdown("### 📊 Current Situation")
col3, col4 = st.columns(2)
with col3:
    target = st.number_input('🎯 Target Score', min_value=1, step=1)
with col4:
    score = st.number_input('🏏 Current Score', min_value=0, step=1)

# Separate overs and balls — prevents invalid inputs like 10.7 overs
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

# Pitch & Conditions (heuristic adjustments in log-odds space)
st.markdown("### 🌤️ Pitch & Conditions")
st.caption("Optional - adjusts prediction based on ground and weather conditions")

adj_values = {}

col_p1, col_p2 = st.columns(2)
with col_p1:
    pitch_opts = {'Flat (Batting)': 0.15, 'Balanced': 0, 'Turning (Spin)': -0.20,
                  'Seaming (Pace)': -0.18, 'Cracked': -0.25}
    pitch_type = st.selectbox('Pitch Type', list(pitch_opts.keys()), index=1)
    adj_values['pitch'] = pitch_opts[pitch_type]
with col_p2:
    wear_opts = {'Fresh (1st match)': 0, 'Used (2-3 matches)': -0.10, 'Worn (4+ matches)': -0.18}
    pitch_wear = st.selectbox('Pitch Wear', list(wear_opts.keys()), index=0)
    adj_values['wear'] = wear_opts[pitch_wear]

col_d1, col_d2 = st.columns(2)
with col_d1:
    dew_opts = {'None': 0, 'Light Dew': 0.12, 'Heavy Dew': 0.25}
    dew_factor = st.selectbox('Dew Factor', list(dew_opts.keys()), index=0)
    adj_values['dew'] = dew_opts[dew_factor]
with col_d2:
    match_opts = {'Day': 0, 'Day-Night': 0.05, 'Night': 0.10}
    match_type = st.selectbox('Match Type', list(match_opts.keys()), index=0)
    adj_values['match'] = match_opts[match_type]

col_w1, col_w2 = st.columns(2)
with col_w1:
    hum_opts = {'Low (<40%)': -0.05, 'Moderate (40-70%)': 0, 'High (>70%)': 0.08}
    humidity = st.selectbox('Humidity', list(hum_opts.keys()), index=1)
    adj_values['humidity'] = hum_opts[humidity]
with col_w2:
    temp_opts = {'Cool (<25°C)': -0.05, 'Moderate (25-35°C)': 0, 'Hot (>35°C)': 0.05}
    temperature = st.selectbox('Temperature', list(temp_opts.keys()), index=1)
    adj_values['temp'] = temp_opts[temperature]

toss_opts = {'Not Specified': 0, 'Batting Team': 0.12, 'Bowling Team': -0.05}
toss_winner = st.selectbox('Toss Won By', list(toss_opts.keys()), index=0)
adj_values['toss'] = toss_opts[toss_winner]

total_adj = sum(adj_values.values())

st.markdown("---")

# Prediction
if st.button('🚀 Predict Winning Probability', use_container_width=True):

    balls_completed = overs_completed * 6 + balls_in_over
    balls_left = 120 - balls_completed

    if batting_team == bowling_team:
        st.warning("⚠️ Batting and Bowling teams cannot be the same!")
    elif target <= 0:
        st.warning("⚠️ Please enter a valid Target Score.")
    elif score < 0:
        st.warning("⚠️ Score cannot be negative.")
    elif balls_completed == 0:
        st.warning("⚠️ Please enter overs/balls > 0 to calculate Run Rate.")
    elif balls_left <= 0:
        st.error("❌ Innings is over (20 overs completed).")
    elif score >= target:
        st.success(f"🎉 {batting_team} has already won the match!")
    elif wickets == 10:
        st.error(f"❌ {batting_team} is all out. {bowling_team} won!")
    else:
        with st.spinner('Calculating Probabilities...'):
            try:
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

                batting_col = 'batting_team_' + batting_team
                bowling_col = 'bowling_team_' + bowling_team
                city_col = 'city_' + city

                if batting_col in columns_list:
                    input_data[batting_col] = 1
                if bowling_col in columns_list:
                    input_data[bowling_col] = 1
                if city_col in columns_list:
                    input_data[city_col] = 1

                # Scale numerical features
                num_cols = ['runs_left', 'balls_left', 'wicket_left', 'total_runs_x', 'crr', 'rrr']
                input_data[num_cols] = scaler.transform(input_data[num_cols])

                # Predict
                result = model.predict_proba(input_data)[0]
                loss_prob = result[0]
                win_prob = result[1]

                # Apply conditions adjustment in log-odds space
                if total_adj != 0:
                    log_odds = np.log(win_prob / (1 - win_prob)) + total_adj
                    win_prob = 1 / (1 + np.exp(-log_odds))
                    loss_prob = 1 - win_prob

                # Display Results
                st.markdown("### 🏆 Prediction Results")

                if total_adj > 0.01:
                    st.caption(f"Conditions favor batting team (+{total_adj:.2f} adjustment)")
                elif total_adj < -0.01:
                    st.caption(f"Conditions favor bowling team ({total_adj:.2f} adjustment)")

                st.markdown(f'<div class="result-text">🏏 {batting_team} (Batting)</div>', unsafe_allow_html=True)
                st.progress(float(win_prob), text=f"Win: {round(win_prob * 100, 1)}%")

                st.markdown(f'<div class="result-text">🥎 {bowling_team} (Bowling)</div>', unsafe_allow_html=True)
                st.progress(float(loss_prob), text=f"Win: {round(loss_prob * 100, 1)}%")

                st.info(
                    f"📈 **CRR:** {round(crr, 2)} | **RRR:** {round(rrr, 2)} | "
                    f"**Runs Left:** {runs_left} | **Balls Left:** {balls_left}"
                )

            except Exception as e:
                st.error(f"❌ Prediction failed: {e}")
