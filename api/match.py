"""
Vercel Serverless Function — GET /api/match?id=<match_id>
Returns full live match data (score, batters, bowlers, commentary, ball-by-ball)
scraped from Cricbuzz server-side. No CORS proxies needed.
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, requests, re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Referer': 'https://www.cricbuzz.com/',
}

TEAM_ABBR = {
    'LSG': 'Lucknow Super Giants', 'DC': 'Delhi Capitals',
    'MI': 'Mumbai Indians', 'CSK': 'Chennai Super Kings',
    'KKR': 'Kolkata Knight Riders', 'RCB': 'Royal Challengers Bengaluru',
    'RR': 'Rajasthan Royals', 'PBKS': 'Punjab Kings',
    'SRH': 'Sunrisers Hyderabad', 'GT': 'Gujarat Titans',
}

VENUE_CITY = {
    'lucknow': 'Lucknow', 'delhi': 'Delhi', 'mumbai': 'Mumbai',
    'chennai': 'Chennai', 'kolkata': 'Kolkata', 'bengaluru': 'Bengaluru',
    'bangalore': 'Bengaluru', 'hyderabad': 'Hyderabad', 'ahmedabad': 'Ahmedabad',
    'jaipur': 'Jaipur', 'pune': 'Pune', 'mohali': 'Mohali',
    'dharamsala': 'Dharamsala', 'navi mumbai': 'Navi Mumbai',
    'ranchi': 'Ranchi', 'indore': 'Indore', 'visakhapatnam': 'Visakhapatnam',
}


def parse_match(match_id, text):
    # ── 1. Title & match name ──────────────────────────────────────────────────
    title_m = re.search(r'<title>(.*?)</title>', text)
    raw_title = title_m.group(1) if title_m else ''
    match_name = re.sub(r'^Cricket commentary\s*\|\s*', '', raw_title).strip()
    if not match_name:
        match_name = 'IPL 2026 Live Match'

    # ── 2. Teams ───────────────────────────────────────────────────────────────
    teams_m = re.match(r'([^,]+?)\s+vs\s+([^,]+?),', match_name, re.IGNORECASE)
    team1 = teams_m.group(1).strip() if teams_m else 'Team A'
    team2 = teams_m.group(2).strip() if teams_m else 'Team B'

    # ── 3. Live score: "LSG 65/4 (8.5)" ──────────────────────────────────────
    abbrs_pat = '|'.join(TEAM_ABBR.keys())
    score_m = re.search(rf'({abbrs_pat})\s+(\d+)/(\d+)\s+\((\d+)\.(\d+)\)', text)
    score = wickets = overs_comp = balls_in = 0
    batting_abbr = ''
    if score_m:
        batting_abbr = score_m.group(1)
        score      = int(score_m.group(2))
        wickets    = int(score_m.group(3))
        overs_comp = int(score_m.group(4))
        balls_in   = int(score_m.group(5))

    # Target (2nd innings): look for "Target: 185" or "need 185 runs"
    target = None
    tgt_m = re.search(r'[Tt]arget[:\s]+(\d+)', text)
    if tgt_m:
        target = int(tgt_m.group(1))

    # ── 4. Active batters from meta ────────────────────────────────────────────
    meta_bat = re.search(r'\(([A-Z][^)]{3,60}\d+\(\d+\)[^)]*)\)', text)
    active_batters = []
    if meta_bat:
        for b in re.findall(r'([A-Z][a-zA-Z\s]+?)\s+(\d+)\((\d+)\)', meta_bat.group(1)):
            balls = int(b[2]); runs = int(b[1])
            active_batters.append({
                'name': b[0].strip(), 'runs': runs, 'balls': balls,
                'fours': 0, 'sixes': 0,
                'sr': round(runs / balls * 100, 1) if balls > 0 else 0.0,
                'dismissed': False,
            })

    # ── 5. Detailed data from Next.js JSON chunks ──────────────────────────────
    batsmen_map, bowlers_map = {}, {}
    commentary, recent_balls, fow_list = [], [], []

    for chunk in re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', text, re.DOTALL):
        try:
            decoded = bytes(chunk, 'utf-8').decode('unicode_escape')
        except Exception:
            decoded = chunk

        # Batsmen
        for bm in re.finditer(
            r'"batsmanName"\s*:\s*"([^"]+)"[^}]*?"runs"\s*:\s*(\d+)[^}]*?"balls"\s*:\s*(\d+)[^}]*?"fours"\s*:\s*(\d+)[^}]*?"sixes"\s*:\s*(\d+)',
            decoded
        ):
            name = bm.group(1); balls = int(bm.group(3)); runs = int(bm.group(2))
            batsmen_map[name] = {
                'name': name, 'runs': runs, 'balls': balls,
                'fours': int(bm.group(4)), 'sixes': int(bm.group(5)),
                'sr': round(runs / balls * 100, 1) if balls > 0 else 0.0,
                'dismissed': False,
            }

        # Bowlers
        for bw in re.finditer(
            r'"bowlerName"\s*:\s*"([^"]+)"[^}]*?"overs"\s*:\s*([\d.]+)[^}]*?"maidens"\s*:\s*(\d+)[^}]*?"runs"\s*:\s*(\d+)[^}]*?"wickets"\s*:\s*(\d+)[^}]*?"economy"\s*:\s*([\d.]+)',
            decoded
        ):
            name = bw.group(1)
            bowlers_map[name] = {
                'name': name, 'overs': float(bw.group(2)), 'maidens': int(bw.group(3)),
                'runs': int(bw.group(4)), 'wickets': int(bw.group(5)), 'economy': float(bw.group(6)),
            }

        # Commentary + ball outcomes
        for cm in re.finditer(r'"commText"\s*:\s*"([^"]+)"[^}]*?"ballMetric"\s*:\s*([\d.]+)', decoded):
            comm_text = re.sub(r'<[^>]+>', '', cm.group(1))
            ball_num = float(cm.group(2))
            commentary.append({'text': comm_text, 'ball': ball_num})
            tl = comm_text.lower()
            if 'six' in tl:
                recent_balls.append('6')
            elif 'four' in tl or 'boundary' in tl:
                recent_balls.append('4')
            elif any(x in tl for x in ['wicket', 'out!!', 'caught', 'bowled', 'lbw', 'stumped', 'run out']):
                recent_balls.append('W')
            elif 'wide' in tl:
                recent_balls.append('wd')
            elif 'no ball' in tl:
                recent_balls.append('nb')
            elif 'no run' in tl or 'dot' in tl:
                recent_balls.append('0')
            else:
                rm = re.search(r'(\d+) run', tl)
                recent_balls.append(rm.group(1) if rm else '1')

        # Fall of wickets
        for fw in re.finditer(
            r'"fowScore"\s*:\s*(\d+)[^}]*?"fowOver"\s*:\s*"([^"]+)"[^}]*?"fowBatsman"\s*:\s*"([^"]+)"',
            decoded
        ):
            fow_list.append({'score': int(fw.group(1)), 'over': fw.group(2), 'batsman': fw.group(3)})

    # ── 6. Resolve batters / bowlers ───────────────────────────────────────────
    batters = list(batsmen_map.values()) if batsmen_map else active_batters
    bowlers = list(bowlers_map.values())

    # ── 7. Assign batting/bowling teams ───────────────────────────────────────
    batting_full = TEAM_ABBR.get(batting_abbr, '')
    batting_team, bowling_team = team1, team2
    if batting_full:
        t2_words = team2.split()
        if any(w in batting_full for w in t2_words) or batting_full in team2:
            batting_team, bowling_team = team2, team1

    # ── 8. Venue / city ────────────────────────────────────────────────────────
    city = 'Lucknow'
    snippet = text.lower()[:5000]
    for key, val in VENUE_CITY.items():
        if key in snippet:
            city = val
            break

    # ── 9. Dedup & sort commentary ─────────────────────────────────────────────
    seen_balls = set()
    comm_dedup = []
    for c in sorted(commentary, key=lambda x: -x['ball']):
        if c['ball'] not in seen_balls:
            seen_balls.add(c['ball'])
            comm_dedup.append(c)

    all_players = [
        {'name': b['name'], 'runs': b['runs'], 'balls_faced': b['balls'],
         'sr': b.get('sr', 0), 'wickets': 0, 'catches': 0, 'team': batting_team}
        for b in batters
    ] + [
        {'name': bw['name'], 'runs': 0, 'balls_faced': 0, 'sr': 0,
         'wickets': bw['wickets'], 'catches': 0, 'economy': bw.get('economy', 0), 'team': bowling_team}
        for bw in bowlers
    ]

    return {
        'id':          match_id,
        'matchName':   match_name,
        'battingTeam': batting_team,
        'bowlingTeam': bowling_team,
        'score':       score,
        'wickets':     wickets,
        'oversComp':   overs_comp,
        'ballsIn':     balls_in,
        'target':      target,
        'city':        city,
        'batters':     batters[:6],
        'bowlers':     bowlers[:6],
        'recentBalls': list(reversed(recent_balls))[-12:],
        'fowList':     fow_list,
        'commentary':  comm_dedup[:10],
        'allPlayers':  all_players,
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        match_id = (qs.get('id') or [None])[0]
        if not match_id:
            body = json.dumps({'error': 'id param required'}).encode()
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
            return
        try:
            url = f'https://www.cricbuzz.com/live-cricket-scores/{match_id}'
            r = requests.get(url, headers=HEADERS, timeout=12)
            r.raise_for_status()
            data = parse_match(match_id, r.text)
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store')
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            body = json.dumps({'error': str(e)}).encode()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, *args):
        pass
