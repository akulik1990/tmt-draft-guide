#!/usr/bin/env python3
"""Fetch latest 17lands card ratings for TMT set.

Usage:
    python3 update_data.py              # fetch card ratings (default)
    python3 update_data.py --scryfall   # also refresh Scryfall card data
    python3 update_data.py --all        # fetch everything

After updating data, rebuild the guide:
    python3 build_draft_guide_v2.py
    cp TMT_Draft_Guide.html docs/index.html
"""

import json
import sys
import time
import urllib.request
import urllib.error

PROJECT_DIR = '/home/morris/Projects/tmt-draft-guide'

# ── 17Lands Card Ratings ──────────────────────────────────────────────────
RATINGS_URL = 'https://www.17lands.com/card_ratings/data?expansion=TMT&format=PremierDraft'
RATINGS_FILE = f'{PROJECT_DIR}/tmt_17lands_ratings.json'

# ── Scryfall Card Data ────────────────────────────────────────────────────
SCRYFALL_URL = 'https://api.scryfall.com/cards/search?q=set:tmt+is:booster&unique=cards&order=collector'
SCRYFALL_FILE = f'{PROJECT_DIR}/tmt_scryfall_cards.json'


def fetch_json(url, description):
    """Fetch JSON from a URL with user-agent header."""
    print(f'Fetching {description}...')
    print(f'  URL: {url}')
    req = urllib.request.Request(url, headers={
        'User-Agent': 'TMTDraftGuide/1.0 (contact: github.com/akulik1990)',
        'Accept': 'application/json',
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f'  OK — received {len(json.dumps(data)):,} bytes')
            return data
    except urllib.error.HTTPError as e:
        print(f'  ERROR: HTTP {e.code} — {e.reason}')
        return None
    except Exception as e:
        print(f'  ERROR: {e}')
        return None


def save_json(data, filepath, description):
    """Save JSON data to file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    size_kb = len(json.dumps(data, ensure_ascii=False)) / 1024
    print(f'  Saved {description} → {filepath} ({size_kb:.0f} KB)')


def update_ratings():
    """Fetch latest 17lands card ratings (GIH WR, ALSA, etc.)."""
    data = fetch_json(RATINGS_URL, '17lands card ratings')
    if data:
        print(f'  Cards: {len(data)}')
        top = sorted(data, key=lambda c: c.get('game_count') or 0, reverse=True)[:3]
        for c in top:
            print(f'    {c["name"]}: {c.get("game_count", 0):,} games, '
                  f'GIH WR: {c.get("ever_drawn_win_rate", 0):.1%}, '
                  f'ALSA: {c.get("avg_seen", 0):.1f}')
        save_json(data, RATINGS_FILE, 'card ratings')
        return True
    return False


def update_scryfall():
    """Fetch latest Scryfall card data (images, oracle text, stats)."""
    all_cards = {}
    url = SCRYFALL_URL
    page = 1

    while url:
        data = fetch_json(url, f'Scryfall page {page}')
        if not data:
            break

        for card in data.get('data', []):
            name = card.get('name', '')
            if card.get('layout') == 'token':
                continue

            image_uris = card.get('image_uris', {})
            if not image_uris and card.get('card_faces'):
                image_uris = card['card_faces'][0].get('image_uris', {})

            # Prefer lowest collector number (main art)
            if name in all_cards:
                existing_cn = int(all_cards[name].get('collector_number', '999'))
                new_cn = int(card.get('collector_number', '999'))
                if new_cn >= existing_cn:
                    continue

            all_cards[name] = {
                'name': name,
                'mana_cost': card.get('mana_cost', ''),
                'cmc': card.get('cmc', 0),
                'type_line': card.get('type_line', ''),
                'oracle_text': card.get('oracle_text', ''),
                'colors': card.get('colors', []),
                'color_identity': card.get('color_identity', []),
                'rarity': card.get('rarity', ''),
                'collector_number': card.get('collector_number', ''),
                'image_small': image_uris.get('small', ''),
                'image_normal': image_uris.get('normal', ''),
                'image_large': image_uris.get('large', ''),
                'image_art_crop': image_uris.get('art_crop', ''),
            }

        if data.get('has_more'):
            url = data.get('next_page')
            page += 1
            time.sleep(0.1)
        else:
            url = None

    if all_cards:
        print(f'  Total unique cards: {len(all_cards)}')
        save_json(all_cards, SCRYFALL_FILE, 'Scryfall cards')
        return True
    return False


def main():
    args = set(sys.argv[1:])
    do_scryfall = '--scryfall' in args or '--all' in args

    print('=' * 60)
    print('TMT Draft Guide — Data Update')
    print('=' * 60)

    results = []

    ok = update_ratings()
    results.append(('Card ratings', ok))
    print()

    if do_scryfall:
        ok = update_scryfall()
        results.append(('Scryfall', ok))
        print()

    print('=' * 60)
    for name, ok in results:
        status = '✓' if ok else '✗ FAILED'
        print(f'  {status}  {name}')
    print('=' * 60)

    if all(ok for _, ok in results):
        print('\nNext steps:')
        print('  1. python3 build_draft_guide_v2.py')
        print('  2. cp TMT_Draft_Guide.html docs/index.html')
        print('  3. git add -A && git commit -m "Update 17lands data"')
        print('  4. git push origin main')
    else:
        print('\nSome fetches failed. Check errors above.')
        sys.exit(1)


if __name__ == '__main__':
    main()
