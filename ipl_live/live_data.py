"""
Live data source: Cricbuzz scraper (no API key needed) + demo fallback.
"""
from cricbuzz_scraper import get_live_ipl_matches, get_live_match_data


def get_live_matches():
    """Return list of live IPL 2026 matches from Cricbuzz."""
    matches = get_live_ipl_matches()
    if matches:
        return matches
    return [{'id': 'demo', 'name': 'Demo: MI vs CSK • IPL 2025', 'status': 'Demo'}]


def get_scorecard(match_id):
    """Return full match + player data."""
    if match_id == 'demo':
        return get_demo_match()

    data = get_live_match_data(match_id)
    if data:
        return data
    return get_demo_match()


def get_demo_match():
    return {
        'id': 'demo',
        'name': 'Mumbai Indians vs Chennai Super Kings • IPL 2025 • Match 42',
        'venue': 'Wankhede Stadium, Mumbai',
        'status': 'Live — 2nd Innings',
        'batting_team': 'Chennai Super Kings',
        'bowling_team': 'Mumbai Indians',
        'target': 187,
        'score': 124,
        'overs_completed': 14,
        'balls_in_over': 3,
        'wickets': 4,
        'city': 'Mumbai',
        'batters': [
            {'name': 'MS Dhoni',        'runs': 28, 'balls': 18, 'fours': 2, 'sixes': 2, 'sr': 155.6, 'dismissed': False},
            {'name': 'Ravindra Jadeja', 'runs': 41, 'balls': 29, 'fours': 4, 'sixes': 1, 'sr': 141.4, 'dismissed': False},
        ],
        'bowlers': [
            {'name': 'Jasprit Bumrah',   'overs': 3.0, 'maidens': 0, 'runs': 22, 'wickets': 2, 'economy': 7.33},
            {'name': 'Hardik Pandya',    'overs': 2.3, 'maidens': 0, 'runs': 28, 'wickets': 1, 'economy': 11.2},
            {'name': 'Suryakumar Yadav', 'overs': 1.0, 'maidens': 0, 'runs': 9,  'wickets': 1, 'economy': 9.0},
        ],
        'recent_balls': ['1', '4', 'W', '0', '2', '6', '1', '0', '4', '1', '6', '0'],
        'fall_of_wickets': [
            {'wicket': 1, 'score': 34,  'over': '5.2',  'batsman': 'Devon Conway'},
            {'wicket': 2, 'score': 67,  'over': '8.4',  'batsman': 'Ruturaj Gaikwad'},
            {'wicket': 3, 'score': 89,  'over': '11.1', 'batsman': 'Ajinkya Rahane'},
            {'wicket': 4, 'score': 107, 'over': '13.0', 'batsman': 'Shivam Dube'},
        ],
        'all_players': [
            {'name': 'Rohit Sharma',     'team': 'MI',  'runs': 62, 'balls_faced': 41, 'sr': 151.2, 'wickets': 0, 'catches': 0},
            {'name': 'Suryakumar Yadav', 'team': 'MI',  'runs': 48, 'balls_faced': 27, 'sr': 177.8, 'wickets': 1, 'catches': 0},
            {'name': 'Hardik Pandya',    'team': 'MI',  'runs': 22, 'balls_faced': 14, 'sr': 157.1, 'wickets': 1, 'catches': 0},
            {'name': 'Jasprit Bumrah',   'team': 'MI',  'runs': 0,  'balls_faced': 0,  'sr': 0,     'wickets': 2, 'catches': 0},
            {'name': 'Ruturaj Gaikwad',  'team': 'CSK', 'runs': 35, 'balls_faced': 28, 'sr': 125.0, 'wickets': 0, 'catches': 0},
            {'name': 'Ravindra Jadeja',  'team': 'CSK', 'runs': 41, 'balls_faced': 29, 'sr': 141.4, 'wickets': 0, 'catches': 1},
            {'name': 'MS Dhoni',         'team': 'CSK', 'runs': 28, 'balls_faced': 18, 'sr': 155.6, 'wickets': 0, 'catches': 0},
        ],
        'commentary': [],
    }
