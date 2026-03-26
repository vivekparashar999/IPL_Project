# IPL Win Probability Predictor

Predict IPL match outcomes in real-time using a logistic regression model trained on historical IPL data (2008-2024). Enter the current match situation during a second innings chase and get instant win/loss probabilities.

**Live Demo:** [https://hardikdewra.github.io/IPL_Project](https://hardikdewra.github.io/IPL_Project)

## Features

- All 10 current IPL franchises with team colors and badges
- 32 match venues (India, UAE, South Africa)
- Real-time win probability prediction
- Animated probability bars and stat display
- Current Run Rate (CRR) and Required Run Rate (RRR)
- Cricket-correct overs input (separate overs and balls - no more 10.7 overs)
- Mobile responsive design
- Works entirely in the browser (no server needed for the static version)

## Tech Stack

**Static Version (GitHub Pages)**
- Vanilla HTML, CSS, JavaScript
- Logistic regression model exported as JS coefficients
- Zero dependencies - runs in any modern browser

**Streamlit Version (Local)**
- Python, Streamlit
- Scikit-learn (pre-trained classifier + StandardScaler)
- Pandas, NumPy

## Quick Start

### Option 1: Static Site (Recommended)

Just open `index.html` in your browser. No setup needed.

### Option 2: Streamlit App

```bash
git clone https://github.com/vivekparashar999/IPL_Project.git
cd IPL_Project
pip install -r requirements.txt
streamlit run app.py
```

## Project Structure

```
IPL_Project/
├── index.html         # Static web app (GitHub Pages)
├── app.py             # Streamlit application
├── model.pkl          # Trained logistic regression model
├── scaler.pkl         # StandardScaler for numerical features
├── columns.pkl        # 64 feature column names
├── requirements.txt   # Python dependencies
├── .nojekyll          # GitHub Pages config
└── README.md
```

## How It Works

1. Takes match situation inputs: teams, city, target, score, overs, wickets
2. Engineers features: runs_left, balls_left, wickets_left, CRR, RRR
3. One-hot encodes teams and city into a 64-feature vector
4. Scales numerical features with a pre-trained StandardScaler
5. Runs logistic regression: sigmoid(coefficients . features + intercept)
6. Returns win/loss probability for the batting team

## Built By

- [Hardik](https://github.com/HardikDewra)
- [Vivek](https://github.com/vivekparashar999)
