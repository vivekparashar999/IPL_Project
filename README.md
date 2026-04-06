# IPL Win Probability Predictor

Predict real-time IPL match win probabilities using a Logistic Regression model trained on ball-by-ball historical data.

## Highlights

- Built a **Logistic Regression model** to predict real-time IPL match win probabilities using ball-by-ball historical data
- Engineered **8+ features** (run rate, wickets, overs remaining, target) from raw match data, improving accuracy to **~78%**
- Performed data cleaning on **1000+ matches**, handled missing values, and applied label encoding for categorical features
- Deployed as an **interactive Streamlit web app** for users to input live match state and get real-time win predictions

## Tech Stack

- **Python** — Core language
- **Scikit-learn** — Logistic Regression model training and evaluation
- **Streamlit** — Interactive web app deployment
- **Pandas** — Data cleaning and feature engineering

## How to Run

```bash
git clone https://github.com/vivekparashar999/IPL_Project.git
cd IPL_Project
pip install -r requirements.txt
streamlit run app.py
```

## Author

**Vivek Parashar** — [LinkedIn](https://www.linkedin.com/in/vivek-parashar-845725281) | [GitHub](https://github.com/vivekparashar999)
