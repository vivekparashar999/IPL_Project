from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from live_data import get_live_matches, get_scorecard
from predictor import (
    predict_win_probability, predict_next_ball,
    project_batting, project_bowling, predict_mom,
    project_first_innings
)
import os

app = Flask(__name__)
CORS(app)


# ── Pages ──────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('dashboard.html')


# ── API: List live matches ─────────────────────────────────────────────────────
@app.route('/api/matches')
def api_matches():
    matches = get_live_matches()
    simplified = []
    for m in matches:
        simplified.append({
            'id':     m.get('id', 'demo'),
            'name':   m.get('name', 'Unknown Match'),
            'status': m.get('status', ''),
        })
    return jsonify(simplified)


# ── API: Full match data + all predictions ─────────────────────────────────────
@app.route('/api/match/<match_id>')
def api_match(match_id):
    data = get_scorecard(match_id)
    if not data:
        return jsonify({'error': 'Match not found'}), 404

    target          = data.get('target')
    score           = data.get('score', 0)
    overs_completed = data.get('overs_completed', 0)
    balls_in_over   = data.get('balls_in_over', 0)
    wickets         = data.get('wickets', 0)
    batting_team    = data.get('batting_team', '')
    bowling_team    = data.get('bowling_team', '')
    city            = data.get('city', 'Mumbai')
    batters         = data.get('batters', [])
    bowlers         = data.get('bowlers', [])
    all_players     = data.get('all_players', [])

    balls_completed = overs_completed * 6 + balls_in_over
    balls_left      = 120 - balls_completed
    runs_needed     = (target - score) if target else None

    response = {
        'match': data,
        'predictions': {}
    }

    preds = response['predictions']

    # 1. Win probability (2nd innings only)
    if target and balls_left > 0:
        w, l = predict_win_probability(
            batting_team, bowling_team, city,
            target, score, balls_completed, wickets
        )
        preds['win_probability'] = {
            'batting_team': batting_team,
            'batting_prob': round(w * 100, 1),
            'bowling_team': bowling_team,
            'bowling_prob': round(l * 100, 1),
        }
    else:
        preds['win_probability'] = None

    # 2. Next ball prediction
    striker = next((b for b in batters if not b.get('dismissed', True)), None)
    current_bowler = bowlers[-1] if bowlers else None

    batsman_sr     = striker['sr'] if striker else 130.0
    bowler_economy = current_bowler['economy'] if current_bowler else 8.5

    preds['next_ball'] = predict_next_ball(
        batsman_sr=batsman_sr or 130.0,
        bowler_economy=bowler_economy or 8.5,
        wickets=wickets,
        balls_left=balls_left,
        runs_needed=runs_needed or 0,
    )

    # 3. Batting projections
    preds['batting_projections'] = project_batting(batters, balls_left, wickets)

    # 4. Bowling projections
    preds['bowling_projections'] = project_bowling(bowlers)

    # 5. Man of the Match
    preds['mom'] = predict_mom(all_players)

    # 6. First innings projection (when no target yet)
    if not target:
        preds['score_projection'] = project_first_innings(score, balls_completed, wickets)
    else:
        preds['score_projection'] = None

    # Extra computed fields
    preds['match_state'] = {
        'crr':        round((score / balls_completed * 6) if balls_completed > 0 else 0, 2),
        'rrr':        round((runs_needed / balls_left * 6) if (runs_needed and balls_left > 0) else 0, 2),
        'runs_needed': runs_needed,
        'balls_left':  balls_left,
        'overs_left':  f"{balls_left // 6}.{balls_left % 6}",
    }

    return jsonify(response)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5050))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)
