"""
Vercel Serverless Function — GET /api/matches
Returns list of live/recent IPL 2026 matches scraped from Cricbuzz (server-side, no CORS).
"""
from http.server import BaseHTTPRequestHandler
import json, requests, re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Referer': 'https://www.cricbuzz.com/',
}

IPL_SLUGS = ['premier-league-2026', 'ipl-2026', 'indian-premier-league-2026', 'tata-ipl']

TEAM_ABBR = {
    'LSG': 'Lucknow Super Giants', 'DC': 'Delhi Capitals',
    'MI': 'Mumbai Indians', 'CSK': 'Chennai Super Kings',
    'KKR': 'Kolkata Knight Riders', 'RCB': 'Royal Challengers Bengaluru',
    'RR': 'Rajasthan Royals', 'PBKS': 'Punjab Kings',
    'SRH': 'Sunrisers Hyderabad', 'GT': 'Gujarat Titans',
}
ABBRS = list(TEAM_ABBR.keys())


def extract_matches_from_html(text):
    matches = []
    seen = set()
    for m in re.finditer(r'href="(/live-cricket-scores/(\d+)/([^"]+))"', text):
        href, mid, slug = m.group(1), m.group(2), m.group(3).lower()
        if mid in seen:
            continue
        if not any(p in slug for p in IPL_SLUGS):
            continue
        seen.add(mid)
        # Try to pull team names from surrounding context
        pos = text.find(m.group(0))
        ctx = text[max(0, pos - 300):pos + 300]
        ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
        team_m = re.search(r'([A-Z]{2,5})\s+vs\s+([A-Z]{2,5})', ctx_clean)
        if team_m and team_m.group(1) in ABBRS and team_m.group(2) in ABBRS:
            name = f"{team_m.group(1)} vs {team_m.group(2)} — IPL 2026"
        else:
            # Humanise the slug
            parts = slug.split('-vs-')
            if len(parts) == 2:
                t1 = parts[0].split('-')[-1].upper()
                t2 = parts[1].split('-')[0].upper()
                name = f"{t1} vs {t2} — IPL 2026"
            else:
                name = slug.replace('-', ' ').title()
        matches.append({'id': mid, 'name': name})
    return matches


def get_ipl_matches():
    matches = []
    seen_ids = set()

    # 1. Scrape live-scores page + homepage
    for url in [
        'https://www.cricbuzz.com/cricket-match/live-scores',
        'https://www.cricbuzz.com',
    ]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            for m in extract_matches_from_html(r.text):
                if m['id'] not in seen_ids:
                    seen_ids.add(m['id'])
                    matches.append(m)
        except Exception:
            pass

    # 2. If nothing found, try the IPL 2026 schedule page
    if not matches:
        for series_id in ['8048', '7728', '8032']:  # common Cricbuzz IPL series IDs
            try:
                url = f'https://www.cricbuzz.com/cricket-series/{series_id}/indian-premier-league-2026/matches'
                r = requests.get(url, headers=HEADERS, timeout=10)
                for m in extract_matches_from_html(r.text):
                    if m['id'] not in seen_ids:
                        seen_ids.add(m['id'])
                        matches.append(m)
                if matches:
                    break
            except Exception:
                pass

    return matches


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data = get_ipl_matches()
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
