# IPL Win Probability Predictor

A Streamlit web app that predicts the winning probability of IPL teams during a live match based on the current match situation.

## Features

- Select batting and bowling teams from all 10 IPL franchises
- Input match details: host city, target score, current score, overs + balls completed, and wickets fallen
- Real-time win probability prediction using a trained ML model
- Visual progress bars showing win/loss probabilities
- Displays Current Run Rate (CRR) and Required Run Rate (RRR)

## Tech Stack

- **Frontend:** Streamlit
- **ML Model:** Scikit-learn (pre-trained classifier with scaler)
- **Data Processing:** Pandas, NumPy

## How to Run

1. Clone the repository:
   ```bash
   git clone https://github.com/vivekparashar999/IPL_Project.git
   cd IPL_Project
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Project Structure

```
IPL_Project/
├── app.py              # Streamlit application
├── model.pkl           # Trained ML model
├── scaler.pkl          # Feature scaler
├── columns.pkl         # Column names for input features
├── requirements.txt    # Python dependencies
└── README.md
```

## Screenshot

Once running, open `http://localhost:8501` in your browser to use the predictor.
