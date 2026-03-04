#!/usr/bin/env python3
"""Build the multi-color splash sealed deck HTML."""
import json, html

with open('/home/morris/Projects/mtga-draft-helper/sealed_pool_data.json') as f:
    pool = json.load(f)

cards_by_name = {}
for c in pool:
    cards_by_name[c['name']] = c

# Define the deck
deck = {
    "creatures": [
        # CMC 1
        {"name": "Squirrelanoids", "qty": 1, "cmc": 1, "splash": False,
         "note": "1/1 deathtouch — early trade, leaves battlefield for Disappear"},
        # CMC 2
        {"name": "Frog Butler", "qty": 2, "cmc": 2, "splash": False,
         "note": "1/1 deathtouch, tap for any color — key fixing creature"},
        {"name": "Rat King, Verminister", "qty": 1, "cmc": 2, "splash": False,
         "note": "Disappear engine: makes Rat tokens + grows with +1/+1 counters"},
        {"name": "Courier of Comestibles", "qty": 1, "cmc": 2, "splash": False,
         "note": "Tutors Food cards — fetches our pizza removal package"},
        # CMC 3
        {"name": "Mona Lisa, Science Geek", "qty": 1, "cmc": 3, "splash": False,
         "note": "1/3 reach, taps for 1 mana any color — additional fixing"},
        {"name": "Foot Elite", "qty": 1, "cmc": 3, "splash": False,
         "note": "2/4 grants indestructible — hybrid {W/B}, cast with just Black"},
        {"name": "Insectoid Exterminator", "qty": 3, "cmc": 3, "splash": False,
         "note": "2/2 flyer, Disappear scry 1 — evasion + card selection"},
        # CMC 4
        {"name": "Putrid Pals", "qty": 1, "cmc": 4, "splash": False,
         "note": "3/3 deathtouch (5/5 with Disappear) — hybrid {B/G}"},
        {"name": "Leonardo, Sewer Samurai", "qty": 1, "cmc": 4, "splash": "W",
         "note": "★ MYTHIC — 3/3 double strike, recast power≤1 from graveyard"},
        # CMC 6
        {"name": "Krang & Shredder", "qty": 1, "cmc": 6, "splash": False,
         "note": "6/7 Disappear free-cast from exile — hybrid {U/B}, cast with Black"},
        # CMC 7
        {"name": "Raph & Mikey, Troublemakers", "qty": 1, "cmc": 7, "splash": False,
         "note": "7/7 trample haste, reveals creature — hybrid {R/G}, cast with Green"},
        {"name": "West Wind Avatar", "qty": 1, "cmc": 7, "splash": False,
         "note": "7/7 trample, Disappear draws card — BG linchpin finisher"},
    ],
    "noncreature": [
        # CMC 1
        {"name": "Guac & Marshmallow Pizza", "qty": 1, "cmc": 1, "splash": False,
         "note": "Flash Food, +2/+2 trick — sac for Disappear triggers"},
        # CMC 2
        {"name": "Everything Pizza", "qty": 1, "cmc": 2, "splash": False,
         "note": "Food — fetches ANY basic land (splash enabler), WUBRG activation possible"},
        {"name": "Omni-Cheese Pizza", "qty": 2, "cmc": 2, "splash": False,
         "note": "Draws a card, sac for any color — fixing + Disappear trigger"},
        {"name": "Hard-Won Jitte", "qty": 1, "cmc": 2, "splash": "R",
         "note": "★ Equipment: gives DOUBLE STRIKE — devastating on any creature"},
        # CMC 3
        {"name": "Make Your Move", "qty": 1, "cmc": 3, "splash": "W",
         "note": "★ Destroy artifact/enchantment/power 4+ — premium instant removal"},
        {"name": "Novel Nunchaku", "qty": 1, "cmc": 3, "splash": False,
         "note": "Equipment: +1/+1 trample, ETB fight — removal on a stick"},
        {"name": "Tainted Treats", "qty": 1, "cmc": 3, "splash": False,
         "note": "Destroy creature/artifact + Food token — BG linchpin removal"},
        # CMC 4
        {"name": "Anchovy & Banana Pizza", "qty": 1, "cmc": 4, "splash": False,
         "note": "Destroy creature on ETB — removal Food, sac for Disappear"},
    ],
    "lands": [
        {"name": "Swamp", "qty": 6},
        {"name": "Forest", "qty": 5},
        {"name": "Illegitimate Business", "qty": 2},
        {"name": "Plains", "qty": 1},
        {"name": "Mountain", "qty": 1},
        {"name": "Escape Tunnel", "qty": 1},
    ]
}

# Count totals
creature_count = sum(c["qty"] for c in deck["creatures"])
noncreature_count = sum(c["qty"] for c in deck["noncreature"])
land_count = sum(l["qty"] for l in deck["lands"])
total = creature_count + noncreature_count + land_count
print(f"Creatures: {creature_count}")
print(f"Noncreature: {noncreature_count}")
print(f"Lands: {land_count}")
print(f"Total: {total}")

# Get image URIs
def get_img(name):
    if name in cards_by_name:
        return cards_by_name[name].get("image_uri", "")
    return ""

# Build mana curve data
curve = {}
for section in ["creatures", "noncreature"]:
    for card in deck[section]:
        cmc = card["cmc"]
        curve[cmc] = curve.get(cmc, 0) + card["qty"]

# Color source analysis
sources = {
    "B": {"lands": 8, "fixing": 5, "fetchable": 2, "total": 13, "label": "Black"},
    "G": {"lands": 7, "fixing": 5, "fetchable": 2, "total": 12, "label": "Green"},
    "W": {"lands": 1, "fixing": 5, "fetchable": 2, "total": 8, "label": "White (splash)"},
    "R": {"lands": 1, "fixing": 5, "fetchable": 2, "total": 8, "label": "Red (splash)"},
}

# Build HTML
basic_land_imgs = {
    "Swamp": "https://cards.scryfall.io/small/front/6/c/6ce4ef6c-6947-4faa-94e8-1853bdf14b57.jpg?1737065879",
    "Forest": "https://cards.scryfall.io/small/front/e/c/ec53f870-84f8-4e55-a1f1-3eafb8fe3187.jpg?1737065873",
    "Plains": "https://cards.scryfall.io/small/front/3/6/369a5823-882a-4a71-9e1c-906ed3c6cc3f.jpg?1737065867",
    "Mountain": "https://cards.scryfall.io/small/front/a/c/ac3c3821-8b1b-4d42-85c6-2c9fb1de9788.jpg?1737065876",
    "Island": "https://cards.scryfall.io/small/front/3/d/3d47e1a2-5660-424a-91bb-a3a5fcd21ed8.jpg?1737065870",
}

def card_html(card_data, section="creature"):
    name = card_data["name"]
    qty = card_data["qty"]
    cmc = card_data["cmc"]
    splash = card_data.get("splash", False)
    note = card_data.get("note", "")
    img = get_img(name)
    
    splash_badge = ""
    if splash == "W":
        splash_badge = '<span class="splash-badge splash-w">W</span>'
    elif splash == "R":
        splash_badge = '<span class="splash-badge splash-r">R</span>'
    
    # Get card details
    c = cards_by_name.get(name, {})
    type_line = c.get("type_line", "")
    power = c.get("power", "")
    toughness = c.get("toughness", "")
    pt = f"{power}/{toughness}" if power and toughness else ""
    mana_cost = c.get("mana_cost", "")
    rarity = c.get("rarity", "common")
    
    rarity_class = f"rarity-{rarity}"
    
    return f'''<div class="card-entry {rarity_class}" data-img="{img}">
        <div class="card-qty">{qty}×</div>
        <div class="card-info">
            <div class="card-name">{html.escape(name)} {splash_badge}</div>
            <div class="card-details">{html.escape(mana_cost)} · {html.escape(type_line)}{' · ' + pt if pt else ''}</div>
            <div class="card-note">{html.escape(note)}</div>
        </div>
        <div class="card-cmc">{cmc}</div>
    </div>'''

def land_html(land):
    name = land["name"]
    qty = land["qty"]
    img = get_img(name) or basic_land_imgs.get(name, "")
    c = cards_by_name.get(name, {})
    oracle = c.get("oracle_text", "")
    
    return f'''<div class="card-entry land-entry" data-img="{img}">
        <div class="card-qty">{qty}×</div>
        <div class="card-info">
            <div class="card-name">{html.escape(name)}</div>
            <div class="card-note">{html.escape(oracle[:80]) if oracle else 'Basic Land'}</div>
        </div>
    </div>'''

# Build curve bars
max_count = max(curve.values()) if curve else 1
curve_html = ""
for cmc in range(1, 8):
    count = curve.get(cmc, 0)
    height = int((count / max_count) * 120) if max_count > 0 else 0
    curve_html += f'''<div class="curve-col">
        <div class="curve-count">{count}</div>
        <div class="curve-bar" style="height:{height}px"></div>
        <div class="curve-label">{cmc}</div>
    </div>'''

# Source bars
source_html = ""
for color, data in sources.items():
    color_class = {"B": "src-black", "G": "src-green", "W": "src-white", "R": "src-red"}[color]
    pct = min(100, int(data["total"] / 15 * 100))
    source_html += f'''<div class="source-row">
        <div class="source-label">{data["label"]}</div>
        <div class="source-bar-bg">
            <div class="source-bar {color_class}" style="width:{pct}%"></div>
        </div>
        <div class="source-count">{data["lands"]} lands + {data["fixing"]} fixing = {data["total"]}</div>
    </div>'''

# Creature cards HTML
creature_cards = ""
for card in deck["creatures"]:
    creature_cards += card_html(card)

# Noncreature cards HTML
noncreature_cards = ""
for card in deck["noncreature"]:
    noncreature_cards += card_html(card, "noncreature")

# Land cards HTML
land_cards = ""
for land in deck["lands"]:
    land_cards += land_html(land)

full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TMT Sealed Deck — BG Disappear + W/R Splash</title>
<style>
:root {{
    --bg: #1a1a2e;
    --surface: #16213e;
    --surface2: #0f3460;
    --accent: #e94560;
    --gold: #f4a261;
    --green: #2a9d8f;
    --text: #e0e0e0;
    --text-dim: #888;
    --white-splash: #f5e6c8;
    --red-splash: #e8a0a0;
    --black-color: #b0a0c0;
    --green-color: #80c080;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 20px;
    max-width: 1100px;
    margin: 0 auto;
}}
h1 {{
    text-align: center;
    font-size: 1.6em;
    margin-bottom: 4px;
    background: linear-gradient(90deg, #2a9d8f, #e94560);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.subtitle {{
    text-align: center;
    color: var(--text-dim);
    font-size: 0.9em;
    margin-bottom: 20px;
}}
/* Stats bar */
.stats-bar {{
    display: flex;
    justify-content: center;
    gap: 24px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}}
.stat {{
    text-align: center;
}}
.stat-num {{
    font-size: 1.8em;
    font-weight: bold;
    color: var(--gold);
}}
.stat-label {{
    font-size: 0.75em;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 1px;
}}
/* Two column layout */
.main-grid {{
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 20px;
}}
.deck-col {{ }}
.side-col {{ }}
/* Sections */
.section {{
    background: var(--surface);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 16px;
}}
.section-title {{
    font-size: 1.1em;
    font-weight: 600;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid var(--surface2);
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.section-count {{
    font-size: 0.85em;
    color: var(--gold);
    font-weight: normal;
}}
/* Card entries */
.card-entry {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 8px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.15s;
    position: relative;
}}
.card-entry:hover {{
    background: var(--surface2);
}}
.card-qty {{
    font-weight: 700;
    color: var(--gold);
    min-width: 28px;
    text-align: center;
    font-size: 0.9em;
}}
.card-info {{
    flex: 1;
    min-width: 0;
}}
.card-name {{
    font-weight: 600;
    font-size: 0.95em;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.card-details {{
    font-size: 0.78em;
    color: var(--text-dim);
    margin-top: 1px;
}}
.card-note {{
    font-size: 0.75em;
    color: #6a9;
    margin-top: 2px;
    font-style: italic;
}}
.card-cmc {{
    background: var(--surface2);
    border-radius: 50%;
    width: 26px;
    height: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8em;
    font-weight: 600;
    flex-shrink: 0;
}}
/* Rarity colors */
.rarity-mythic .card-name {{ color: #e8a040; }}
.rarity-rare .card-name {{ color: #d4af37; }}
.rarity-uncommon .card-name {{ color: #c0c0c0; }}
.rarity-common .card-name {{ color: var(--text); }}
/* Splash badges */
.splash-badge {{
    font-size: 0.65em;
    padding: 1px 6px;
    border-radius: 8px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
.splash-w {{ background: #8b7530; color: #f5e6c8; }}
.splash-r {{ background: #8b3030; color: #e8a0a0; }}
/* Land entries */
.land-entry .card-name {{ color: #88aacc; }}
/* Mana Curve */
.curve-container {{
    display: flex;
    justify-content: center;
    align-items: flex-end;
    gap: 12px;
    height: 160px;
    padding: 10px 0;
}}
.curve-col {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
}}
.curve-bar {{
    width: 32px;
    background: linear-gradient(180deg, var(--accent), var(--green));
    border-radius: 4px 4px 0 0;
    min-height: 2px;
}}
.curve-count {{
    font-size: 0.85em;
    font-weight: 600;
    color: var(--gold);
}}
.curve-label {{
    font-size: 0.75em;
    color: var(--text-dim);
}}
/* Color sources */
.source-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}}
.source-label {{
    font-size: 0.8em;
    min-width: 90px;
    text-align: right;
    color: var(--text-dim);
}}
.source-bar-bg {{
    flex: 1;
    height: 14px;
    background: var(--surface2);
    border-radius: 7px;
    overflow: hidden;
}}
.source-bar {{
    height: 100%;
    border-radius: 7px;
    transition: width 0.5s;
}}
.src-black {{ background: linear-gradient(90deg, #6a5a8a, #b0a0c0); }}
.src-green {{ background: linear-gradient(90deg, #2a6a2a, #80c080); }}
.src-white {{ background: linear-gradient(90deg, #8b7530, #f5e6c8); }}
.src-red {{ background: linear-gradient(90deg, #8b3030, #e8a0a0); }}
.source-count {{
    font-size: 0.7em;
    color: var(--text-dim);
    min-width: 130px;
}}
/* Hover preview */
.preview-box {{
    position: fixed;
    top: 20px;
    right: 20px;
    width: 250px;
    z-index: 1000;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.2s;
}}
.preview-box.active {{
    opacity: 1;
}}
.preview-box img {{
    width: 100%;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}}
/* Synergies */
.synergy-list {{
    list-style: none;
    padding: 0;
}}
.synergy-list li {{
    padding: 5px 0;
    font-size: 0.82em;
    border-bottom: 1px solid var(--surface2);
    line-height: 1.4;
}}
.synergy-list li:last-child {{ border-bottom: none; }}
.synergy-list li::before {{
    content: "⚡";
    margin-right: 6px;
}}
/* Explanation */
.explanation {{
    background: var(--surface);
    border-radius: 10px;
    padding: 16px;
    margin-top: 16px;
    font-size: 0.85em;
    line-height: 1.6;
    color: var(--text-dim);
}}
.explanation h3 {{
    color: var(--gold);
    margin-bottom: 8px;
    font-size: 1em;
}}
.explanation p {{
    margin-bottom: 10px;
}}
.highlight {{ color: var(--accent); font-weight: 600; }}
.fixing-tag {{ color: var(--green); font-weight: 600; }}
@media (max-width: 800px) {{
    .main-grid {{ grid-template-columns: 1fr; }}
    .preview-box {{ display: none; }}
}}
</style>
</head>
<body>

<h1>TMT Sealed Deck — BG Disappear + W/R Splash</h1>
<div class="subtitle">The Kitchen Sink Build · Multi-Color Best Stuff with Maximum Fixing</div>

<div class="stats-bar">
    <div class="stat"><div class="stat-num">{creature_count}</div><div class="stat-label">Creatures</div></div>
    <div class="stat"><div class="stat-num">{noncreature_count}</div><div class="stat-label">Noncreature</div></div>
    <div class="stat"><div class="stat-num">{land_count}</div><div class="stat-label">Lands</div></div>
    <div class="stat"><div class="stat-num">{total}</div><div class="stat-label">Total</div></div>
    <div class="stat"><div class="stat-num">5</div><div class="stat-label">Colors</div></div>
</div>

<div class="main-grid">
<div class="deck-col">

<div class="section">
    <div class="section-title">Creatures <span class="section-count">{creature_count} cards</span></div>
    {creature_cards}
</div>

<div class="section">
    <div class="section-title">Noncreature Spells <span class="section-count">{noncreature_count} cards</span></div>
    {noncreature_cards}
</div>

<div class="section">
    <div class="section-title">Lands <span class="section-count">{land_count} cards</span></div>
    {land_cards}
</div>

</div>
<div class="side-col">

<div class="section">
    <div class="section-title">Mana Curve</div>
    <div class="curve-container">
        {curve_html}
    </div>
</div>

<div class="section">
    <div class="section-title">Color Sources</div>
    {source_html}
</div>

<div class="section">
    <div class="section-title">Key Synergies</div>
    <ul class="synergy-list">
        <li>Rat King + Food/Omni sac = Disappear trigger → Rat tokens + growth</li>
        <li>Everything Pizza fetches splash basics → enables Leonardo & Jitte</li>
        <li>Courier tutors any Food: Guac, Anchovy, Everything, or Omni-Cheese</li>
        <li>Krang & Shredder + Disappear = FREE CAST from opponent's exile</li>
        <li>Hard-Won Jitte (double strike) on Krang = 12 damage per swing</li>
        <li>Novel Nunchaku on Frog Butler (deathtouch) = guaranteed fight kill</li>
        <li>Foot Elite grants indestructible → protect Leonardo or Krang in combat</li>
        <li>Escape Tunnel: fetch splash basics OR make Rat King unblockable</li>
        <li>Everything Pizza WUBRG activation possible with Butler + Mona Lisa alive</li>
    </ul>
</div>

</div>
</div>

<div class="explanation">
    <h3>Why This Build?</h3>
    <p>This deck takes the powerful <span class="highlight">BG Disappear</span> core and supercharges it with
    the pool's best bombs from other colors, enabled by an unusually deep fixing package.
    With <span class="fixing-tag">2× Frog Butler</span>, <span class="fixing-tag">2× Omni-Cheese Pizza</span>,
    <span class="fixing-tag">Everything Pizza</span>, <span class="fixing-tag">Mona Lisa</span>, and
    <span class="fixing-tag">Escape Tunnel</span>, we have <strong>8+ sources each</strong> of White and Red mana
    on top of our BG base.</p>

    <p><strong>The White Splash</strong> brings <span class="highlight">Leonardo, Sewer Samurai</span> — a mythic 3/3
    double striker that recasts power≤1 creatures from the graveyard (Squirrelanoids, Frog Butler, Rat King all come back!).
    <span class="highlight">Make Your Move</span> adds premium instant-speed removal for artifacts, enchantments, or big creatures.</p>

    <p><strong>The Red Splash</strong> adds <span class="highlight">Hard-Won Jitte</span> — an equipment that gives
    double strike to ANY creature. Put this on Krang (12 combat damage), Putrid Pals (deathtouch + double strike),
    or West Wind Avatar (14 trample damage).</p>

    <p><strong>The "Free" Hybrids</strong> are the real secret: Krang & Shredder ({'{U/B}{U/B}'}), Raph & Mikey ({'{R/G}{R/G}'}),
    and Foot Elite ({'{W/B}'}) all cast with ONLY our base BG colors. No splash mana needed for these bombs.</p>

    <p><strong>Everything Pizza</strong> does triple duty: fetches a splash basic on ETB, triggers Disappear when sacrificed,
    and in ultra-late games with Butler + Mona Lisa alive, the WUBRG activation becomes a realistic game-ender.</p>
</div>

<div id="preview" class="preview-box">
    <img id="previewImg" src="" alt="">
</div>

<script>
const preview = document.getElementById('preview');
const previewImg = document.getElementById('previewImg');
document.querySelectorAll('.card-entry').forEach(el => {{
    el.addEventListener('mouseenter', e => {{
        const img = el.dataset.img;
        if (img) {{
            previewImg.src = img.replace('/small/', '/normal/');
            preview.classList.add('active');
        }}
    }});
    el.addEventListener('mouseleave', () => {{
        preview.classList.remove('active');
    }});
}});
</script>
</body>
</html>'''

with open('/home/morris/Projects/mtga-draft-helper/TMT_Sealed_Deck.html', 'w') as f:
    f.write(full_html)

print(f"\n✅ TMT_Sealed_Deck.html written!")
print(f"   {creature_count} creatures + {noncreature_count} noncreature + {land_count} lands = {total} cards")
