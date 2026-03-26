import streamlit as st
import pickle
import pandas as pd
import numpy as np

# 1. Page Configuration (Tab ka naam aur icon)
st.set_page_config(page_title="IPL Win Predictor", page_icon="🏏", layout="centered")

# Custom CSS for UI improvement
st.markdown("""
    <style>
    .main-title { font-size: 40px; font-weight: bold; text-align: center; color: #1E88E5; }
    .sub-title { font-size: 20px; text-align: center; color: #555555; margin-bottom: 30px; }
    .result-text { font-size: 25px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. Fast Loading ke liye Cache use karna
@st.cache_resource
def load_artifacts():
    model = pickle.load(open('model.pkl', 'rb'))
    scaler = pickle.load(open('scaler.pkl', 'rb'))
    columns_list = pickle.load(open('columns.pkl', 'rb'))
    return model, scaler, columns_list

model, scaler, columns_list = load_artifacts()

# Website Headers
st.markdown('<div class="main-title">🏏 IPL Win Probability Predictor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Live Match Situation Simulator</div>', unsafe_allow_html=True)

# Data Lists
teams = ['Chennai Super Kings', 'Delhi Capitals', 'Gujarat Titans', 
         'Kolkata Knight Riders', 'Lucknow Super Giants', 'Mumbai Indians', 
         'Punjab Kings', 'Rajasthan Royals', 'Royal Challengers Bangalore', 'Sunrisers Hyderabad']

cities = ['Mumbai', 'Kolkata', 'Delhi', 'Chennai', 'Bangalore', 'Hyderabad', 
          'Chandigarh', 'Pune', 'Jaipur', 'Ahmedabad', 'Navi Mumbai', 'Sharjah', 'Dubai']

# 3. User Inputs (Clean Layout with Divider)
st.markdown("### 🏟️ Match Details")
col1, col2 = st.columns(2)
with col1:
    batting_team = st.selectbox('🏏 Batting Team', sorted(teams))
with col2:
    bowling_team = st.selectbox('🥎 Bowling Team', sorted(teams))

city = st.selectbox('📍 Host City', sorted(cities))

st.markdown("---") # Ek line draw karne ke liye

st.markdown("### 📊 Current Situation")
col3, col4 = st.columns(2)
with col3:
    target = st.number_input('🎯 Target Score', min_value=0, step=1)
with col4:
    score = st.number_input('🏏 Current Score', min_value=0, step=1)

col5, col6 = st.columns(2)
with col5:
    overs = st.number_input('⏱️ Overs Completed (e.g., 10.5)', min_value=0.0, max_value=20.0, step=0.1)
with col6:
    wickets = st.number_input('❌ Wickets Out', min_value=0, max_value=10, step=1)

st.markdown("---")

# 4. Prediction Button & Logic
if st.button('🚀 Predict Winning Probability', use_container_width=True):
    
    # Basic Checks
    if batting_team == bowling_team:
        st.warning("⚠️ Batting and Bowling teams cannot be the same!")
    elif target == 0:
        st.warning("⚠️ Please enter a valid Target Score.")
    elif overs == 0:
        st.warning("⚠️ Please enter overs > 0 to calculate Run Rate.")
    elif score >= target:
         st.success(f"🎉 {batting_team} has already won the match!")
    elif wickets == 10:
         st.error(f"❌ {batting_team} is all out. {bowling_team} won!")
    else:
        with st.spinner('Calculating Probabilities...'):
            # Feature Engineering
            runs_left = target - score
            
            # Handling overs properly (e.g., 10.5 overs means 10 overs + 5 balls = 65 balls)
            overs_completed_int = int(overs)
            balls_completed = (overs_completed_int * 6) + int((overs - overs_completed_int) * 10)
            balls_left = 120 - balls_completed
            
            wicket_left = 10 - wickets
            crr = score / (balls_completed / 6) if balls_completed > 0 else 0
            rrr = (runs_left * 6) / balls_left if balls_left > 0 else 0

            # 64 Columns Setup
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

            if batting_col in columns_list: input_data[batting_col] = 1
            if bowling_col in columns_list: input_data[bowling_col] = 1
            if city_col in columns_list: input_data[city_col] = 1

            # Scaling
            num_cols = ['runs_left', 'balls_left', 'wicket_left', 'total_runs_x', 'crr', 'rrr']
            input_data[num_cols] = scaler.transform(input_data[num_cols])

            # Prediction
            result = model.predict_proba(input_data)[0]
            loss_prob = result[0]
            win_prob = result[1]

            # 5. BEAUTIFUL DISPLAY (Visual Progress Bars)
            st.markdown("### 🏆 Prediction Results")
            
            st.markdown(f'<div class="result-text">{batting_team}</div>', unsafe_allow_html=True)
            st.progress(win_prob, text=f"{round(win_prob*100, 1)}%")
            
            st.markdown(f'<div class="result-text">{bowling_team}</div>', unsafe_allow_html=True)
            st.progress(loss_prob, text=f"{round(loss_prob*100, 1)}%")
            
            # Quick Stats
            st.info(f"📈 **Required Run Rate (RRR):** {round(rrr, 2)} | **Current Run Rate (CRR):** {round(crr, 2)}")