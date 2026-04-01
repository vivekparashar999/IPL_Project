import pickle
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent  # IPL_Project root

# ── Load model once ────────────────────────────────────────────────────────────
def _load():
    with open(BASE_DIR / 'model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open(BASE_DIR / 'scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    with open(BASE_DIR / 'columns.pkl', 'rb') as f:
        cols = pickle.load(f)
    return model, scaler, cols

try:
    _model, _scaler, _cols = _load()
    MODEL_LOADED = True
except Exception as e:
    print(f'Model load error: {e}')
    MODEL_LOADED = False


# ── 1. Win Probability ─────────────────────────────────────────────────────────
def predict_win_probability(batting_team, bowling_team, city, target,
                             score, balls_completed, wickets):
    """Returns (batting_win_prob, bowling_win_prob) as floats 0-1."""
    if not MODEL_LOADED:
        return 0.5, 0.5

    runs_left = target - score
    balls_left = 120 - balls_completed
    if balls_left <= 0:
        return (1.0, 0.0) if score >= target else (0.0, 1.0)

    wicket_left = 10 - wickets
    crr = (score / balls_completed) * 6 if balls_completed > 0 else 0
    rrr = (runs_left / balls_left) * 6 if balls_left > 0 else 0

    try:
        df = pd.DataFrame(columns=_cols)
        df.loc[0] = 0
        df['runs_left'] = runs_left
        df['balls_left'] = balls_left
        df['wicket_left'] = wicket_left
        df['total_runs_x'] = target
        df['crr'] = crr
        df['rrr'] = rrr

        for col, val in [
            (f'batting_team_{batting_team}', 1),
            (f'bowling_team_{bowling_team}', 1),
            (f'city_{city}', 1),
        ]:
            if col in _cols:
                df[col] = val

        num_cols = ['runs_left', 'balls_left', 'wicket_left', 'total_runs_x', 'crr', 'rrr']
        df[num_cols] = _scaler.transform(df[num_cols])

        result = _model.predict_proba(df)[0]
        return float(result[1]), float(result[0])
    except Exception as e:
        print(f'Win pred error: {e}')
        # Fallback: heuristic
        req_rr = rrr
        cur_rr = crr
        ratio = cur_rr / max(req_rr, 0.1)
        win = min(0.95, max(0.05, ratio / (ratio + 1)))
        return win, 1 - win


# ── 2. Next Ball Prediction ────────────────────────────────────────────────────
def predict_next_ball(batsman_sr=130.0, bowler_economy=8.0,
                      wickets=0, balls_left=60, runs_needed=60):
    """
    Returns probability % for each next-ball outcome.
    Uses a pressure-adjusted statistical model.
    """
    pressure = runs_needed / max(balls_left, 1)   # runs needed per ball

    # Base rates (T20 historical averages)
    p = {
        'dot': 0.32,
        '1':   0.27,
        '2':   0.09,
        '3':   0.02,
        '4':   0.13,
        '6':   0.08,
        'W':   0.05,
        'wd':  0.04,
    }

    # Batsman influence (SR vs baseline 130)
    sr_factor = batsman_sr / 130.0
    p['4']   *= min(1.8, sr_factor ** 1.5)
    p['6']   *= min(2.0, sr_factor ** 2.0)
    p['dot'] *= max(0.5, 2.0 - sr_factor)
    p['1']   *= max(0.7, sr_factor ** 0.5)

    # Bowler influence (economy vs baseline 8.5)
    eco_factor = 8.5 / max(bowler_economy, 1)     # low eco → tighter bowling
    p['dot'] *= min(1.5, eco_factor)
    p['4']   *= max(0.6, 1 / eco_factor)
    p['W']   *= min(2.0, eco_factor ** 1.2)

    # Pressure adjustment
    if pressure > 1.5:   # aggressive needed
        p['4'] *= 1.3;  p['6'] *= 1.4;  p['W'] *= 1.3;  p['dot'] *= 0.8
    elif pressure < 0.7:  # comfortable chase
        p['4'] *= 0.85; p['6'] *= 0.8;  p['dot'] *= 1.15

    # Wicket desperation
    if wickets >= 7:
        p['6'] *= 1.4;  p['W'] *= 1.3

    # Normalize to 100%
    total = sum(p.values())
    return {k: round(v / total * 100, 1) for k, v in p.items()}


# ── 3. Player Batting Projections ──────────────────────────────────────────────
def project_batting(batters, balls_left_total, wickets_down):
    """
    Project final runs for each active batter.
    Uses their current SR and estimated remaining balls.
    """
    wickets_remaining = 10 - wickets_down
    balls_per_batter = max(1, balls_left_total // max(wickets_remaining, 1))
    projections = []

    for b in batters:
        if b.get('dismissed', False):
            projections.append({
                'name': b['name'],
                'current': b['runs'],
                'projected': b['runs'],
                'balls': b['balls'],
                'sr': b.get('sr', 0),
                'status': 'Out',
            })
            continue

        sr = b.get('sr', 120)
        if sr == 0 and b.get('balls', 0) > 3:
            sr = b['runs'] / b['balls'] * 100 if b['balls'] > 0 else 120
        elif sr == 0:
            sr = 120

        # Probability of being dismissed before using all balls
        # Simple: assume geometric distribution with p_out = 0.045/ball
        p_survive = (1 - 0.045) ** balls_per_batter
        expected_balls = balls_per_batter * p_survive + (balls_per_batter * 0.5) * (1 - p_survive)
        additional = (expected_balls * sr / 100)
        projected = b['runs'] + additional

        projections.append({
            'name': b['name'],
            'current': b['runs'],
            'projected': round(projected),
            'balls': b['balls'],
            'sr': round(sr, 1),
            'status': 'Batting',
        })

    return projections


# ── 4. Bowler Wicket Projections ───────────────────────────────────────────────
def project_bowling(bowlers, total_overs=20):
    """Project final wickets and economy for each bowler."""
    projections = []
    for bw in bowlers:
        overs = bw.get('overs', 0)
        # Parse overs like 3.4 = 3 overs + 4 balls
        overs_int = int(overs)
        balls_int = round((overs - overs_int) * 10)
        balls_bowled = overs_int * 6 + balls_int

        wickets = bw.get('wickets', 0)
        # Wicket rate per ball
        w_per_ball = wickets / max(balls_bowled, 1)
        # Max 4 overs per bowler in T20
        max_overs = 4
        overs_left = max(0, max_overs - overs)
        balls_left = round(overs_left * 6)

        projected_wickets = wickets + (w_per_ball * balls_left)
        # Economy projection
        runs_per_ball = bw.get('runs', 0) / max(balls_bowled, 1)
        projected_runs = bw.get('runs', 0) + (runs_per_ball * balls_left)
        projected_economy = (projected_runs / (overs_int + overs_left)) if (overs_int + overs_left) > 0 else bw.get('economy', 0)

        projections.append({
            'name': bw['name'],
            'current_wickets': wickets,
            'projected_wickets': round(projected_wickets, 1),
            'overs_done': f"{overs_int}.{balls_int}",
            'overs_left': round(overs_left, 1),
            'economy': bw.get('economy', 0),
            'projected_economy': round(projected_economy, 2),
        })

    return sorted(projections, key=lambda x: x['projected_wickets'], reverse=True)


# ── 5. Man of the Match ────────────────────────────────────────────────────────
def predict_mom(all_players):
    """
    Impact score model:
      Batting:  runs + SR_bonus + milestone bonus
      Bowling:  wickets × 20 + economy_bonus
      Fielding: catches × 8 + run_outs × 12
    """
    scores = []
    for p in all_players:
        runs         = p.get('runs', 0)
        balls_faced  = p.get('balls_faced', 1) or 1
        sr           = p.get('sr', runs / balls_faced * 100) if balls_faced > 0 else 0
        wickets      = p.get('wickets', 0)
        catches      = p.get('catches', 0)

        # Batting impact
        batting_impact = runs
        if sr > 150: batting_impact += (sr - 150) * 0.15   # SR bonus
        if runs >= 50:  batting_impact += 10                 # half-century
        if runs >= 100: batting_impact += 25                 # century

        # Bowling impact
        bowling_impact = wickets * 20
        eco = p.get('economy', 8.5)
        if eco > 0 and wickets > 0:
            economy_bonus = max(0, (9.0 - eco) * 2)
            bowling_impact += economy_bonus

        # Fielding
        fielding_impact = catches * 8 + p.get('run_outs', 0) * 12

        total = batting_impact + bowling_impact + fielding_impact
        scores.append({
            'name':   p['name'],
            'team':   p.get('team', ''),
            'runs':   runs,
            'wickets': wickets,
            'catches': catches,
            'impact': round(total, 1),
        })

    return sorted(scores, key=lambda x: x['impact'], reverse=True)[:5]


# ── 6. First Innings Score Projection ─────────────────────────────────────────
def project_first_innings(score, balls_completed, wickets):
    """When target isn't set yet, project likely final score."""
    if balls_completed == 0:
        return {'low': 140, 'mid': 165, 'high': 185}

    crr = (score / balls_completed) * 6
    balls_left = 120 - balls_completed
    # Death overs acceleration factor
    over = balls_completed / 6
    accel = 1.0
    if over < 6:    accel = 0.9   # powerplay — slightly lower pace
    elif over < 15: accel = 1.0
    else:            accel = 1.15  # death overs

    # Wicket penalty
    w_penalty = 1.0 - (wickets * 0.03)
    projected_more = (balls_left * crr / 6) * accel * w_penalty

    mid = round(score + projected_more)
    return {
        'low':  round(mid * 0.92),
        'mid':  mid,
        'high': round(mid * 1.08),
    }
