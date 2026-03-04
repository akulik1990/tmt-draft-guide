#!/usr/bin/env python3
"""Build TMT Sealed Deck HTML — UR Artifacts build."""

import json, html

with open("/home/morris/Projects/mtga-draft-helper/sealed_pool_data.json") as f:
    pool = json.load(f)

card_lookup = {}
for c in pool:
    card_lookup[c["name"]] = c

def get_image(name):
    c = card_lookup.get(name)
    if c and c.get("image_uri"):
        return c["image_uri"]
    return ""

def get_card(name):
    return card_lookup.get(name, {})

# === DECK DEFINITION ===
deck = {
    "creatures": [
        {"name": "Squirrelanoids", "qty": 1, "cmc": 1, "splash": True,
         "note": "Deathtouch 1-drop — trades with anything, easy B splash"},
        {"name": "Casey Jones, Jury-Rig Justiciar", "qty": 1, "cmc": 2, "splash": False,
         "note": "2/1 haste, digs top 4 for artifacts on ETB"},
        {"name": "Wingnut, Bat on the Belfry", "qty": 1, "cmc": 2, "splash": False,
         "note": "Alliance — gains flying, menace, or haste each trigger"},
        {"name": "Purple Dragon Punks", "qty": 2, "cmc": 2, "splash": False,
         "note": "2/2 body, taps for {R} toward artifact spells"},
        {"name": "Buzz Bots", "qty": 1, "cmc": 2, "splash": False,
         "note": "1/1 flying vigilance, draws a card on death"},
        {"name": "Chrome Dome", "qty": 1, "cmc": 2, "splash": False,
         "note": "RARE — Artifact creatures get +1/+0. Copies artifacts for {5}"},
        {"name": "Mondo Gecko", "qty": 1, "cmc": 3, "splash": False,
         "note": "MYTHIC — Hexproof trick, draws + discards EACH end step"},
        {"name": "Donatello, Way with Machines", "qty": 2, "cmc": 3, "splash": False,
         "note": "1/2 flying, gets +1/+1 counter whenever an artifact enters"},
        {"name": "Nobody", "qty": 2, "cmc": 3, "splash": False,
         "note": "3/2 hybrid, bounces your artifact to hand (reuse ETB) + scry 1"},
        {"name": "Null Group Biological Assets", "qty": 1, "cmc": 3, "splash": False,
         "note": "3/1 first strike on your turn, loots when attacking"},
        {"name": "Donatello, Mutant Mechanic", "qty": 1, "cmc": 4, "splash": False,
         "note": "MYTHIC — 3/5, taps to put three +1/+1 on artifact & animate it"},
        {"name": "Turtle Blimp", "qty": 1, "cmc": 5, "splash": False,
         "note": "3/4 flying vehicle, creates 2/2 Mutant token on ETB. Crew 2"},
        {"name": "Kitsune, Dragon's Daughter", "qty": 1, "cmc": 6, "splash": False,
         "note": "RARE — 6/6 vigilance, exchanges control of two creatures on ETB/hit"},
        {"name": "Krang & Shredder", "qty": 1, "cmc": 6, "splash": True,
         "note": "RARE — 6/7 hybrid (just {B}{B}), exiles opponent's cards & casts them"},
    ],
    "noncreature": [
        {"name": "Hard-Won Jitte", "qty": 1, "cmc": 2, "splash": False,
         "note": "Equipment — gives double strike! Equip {2}"},
        {"name": "Cool but Rude", "qty": 1, "cmc": 2, "splash": False,
         "note": "RARE — Level up: draws on attack, then deals 4 damage removal"},
        {"name": "Mouser Attack!", "qty": 1, "cmc": 2, "splash": False,
         "note": "Modal: create 1/1 robot token OR +3/+0 and first strike trick"},
        {"name": "Omni-Cheese Pizza", "qty": 2, "cmc": 2, "splash": False,
         "note": "Draws a card on ETB. Sac for any color mana or {2} sac for Food"},
        {"name": "Bespoke Bō", "qty": 1, "cmc": 3, "splash": False,
         "note": "Bounces a nonland permanent on ETB + equips for +1/+1 & ward 1"},
        {"name": "Bot Bashing Time", "qty": 1, "cmc": 4, "splash": False,
         "note": "6 damage to a creature + exiles it. Premium removal"},
    ],
    "lands": [
        {"name": "Island", "qty": 7},
        {"name": "Mountain", "qty": 6},
        {"name": "Swamp", "qty": 1},
        {"name": "Escape Tunnel", "qty": 1},
        {"name": "Illegitimate Business", "qty": 1},
    ],
}

# === COUNTS ===
creature_count = sum(c["qty"] for c in deck["creatures"])
noncreature_count = sum(c["qty"] for c in deck["noncreature"])
land_count = sum(c["qty"] for c in deck["lands"])
total = creature_count + noncreature_count + land_count

# Mana curve
from collections import Counter
curve = Counter()
for section in ["creatures", "noncreature"]:
    for c in deck[section]:
        curve[c["cmc"]] += c["qty"]

# === HTML ===
html_out = []
html_out.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>TMT Sealed Deck — UR Artifacts</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#1a1a2e; color:#e0e0e0; font-family:'Segoe UI',system-ui,sans-serif; padding:20px; }}
h1 {{ color:#ff6b6b; text-align:center; margin-bottom:4px; font-size:1.8em; }}
h2 {{ color:#4ecdc4; margin:20px 0 10px; font-size:1.3em; border-bottom:1px solid #333; padding-bottom:5px; }}
h3 {{ color:#ffe66d; margin:16px 0 8px; font-size:1.1em; }}
.subtitle {{ text-align:center; color:#888; margin-bottom:20px; font-size:0.95em; }}
.stats-bar {{ display:flex; justify-content:center; gap:24px; margin:16px 0; padding:12px; background:#16213e; border-radius:8px; flex-wrap:wrap; }}
.stat {{ text-align:center; }}
.stat-num {{ font-size:1.6em; font-weight:bold; }}
.stat-label {{ font-size:0.8em; color:#888; }}
.stat-creatures .stat-num {{ color:#4ecdc4; }}
.stat-noncreature .stat-num {{ color:#ffe66d; }}
.stat-lands .stat-num {{ color:#95e1d3; }}
.stat-total .stat-num {{ color:#ff6b6b; }}

.card-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(320px,1fr)); gap:8px; }}
.card-entry {{ background:#16213e; border-radius:6px; padding:10px 14px; display:flex; justify-content:space-between; align-items:center; position:relative; cursor:pointer; transition:background 0.15s; }}
.card-entry:hover {{ background:#1a2744; }}
.card-name {{ font-weight:600; }}
.card-qty {{ color:#888; margin-right:6px; }}
.card-meta {{ font-size:0.82em; color:#999; }}
.card-note {{ font-size:0.78em; color:#777; margin-top:3px; }}
.splash-badge {{ background:#ff6b6b33; color:#ff6b6b; font-size:0.7em; padding:1px 6px; border-radius:3px; margin-left:6px; }}

.rarity-mythic .card-name {{ color:#ff8c00; }}
.rarity-rare .card-name {{ color:#ffd700; }}
.rarity-uncommon .card-name {{ color:#c0c0c0; }}
.rarity-common .card-name {{ color:#e0e0e0; }}

.card-preview {{ display:none; position:fixed; z-index:1000; pointer-events:none; border-radius:12px; box-shadow:0 8px 32px rgba(0,0,0,0.7); max-width:250px; }}

.curve-container {{ display:flex; align-items:flex-end; gap:6px; height:120px; padding:10px; background:#16213e; border-radius:8px; margin:10px 0; }}
.curve-bar {{ display:flex; flex-direction:column; align-items:center; flex:1; }}
.curve-fill {{ background: linear-gradient(to top, #ff6b6b, #4ecdc4); border-radius:4px 4px 0 0; width:100%; min-width:28px; transition: height 0.3s; }}
.curve-label {{ font-size:0.75em; color:#888; margin-top:4px; }}
.curve-count {{ font-size:0.85em; font-weight:bold; color:#fff; margin-bottom:2px; }}

.color-sources {{ display:flex; gap:12px; flex-wrap:wrap; margin:10px 0; }}
.color-source {{ background:#16213e; border-radius:8px; padding:10px 16px; flex:1; min-width:140px; }}
.color-source-name {{ font-weight:bold; margin-bottom:4px; }}
.color-source-bar {{ height:8px; border-radius:4px; margin-top:4px; }}

.synergy-list {{ background:#16213e; border-radius:8px; padding:14px; margin:10px 0; }}
.synergy-item {{ margin:6px 0; padding:4px 0; border-bottom:1px solid #ffffff0a; }}
.synergy-item:last-child {{ border-bottom:none; }}
.synergy-label {{ color:#ffe66d; font-weight:600; }}

.explanation {{ background:#16213e; border-radius:8px; padding:16px; margin:10px 0; line-height:1.6; }}
.explanation p {{ margin:8px 0; }}

.land-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(200px,1fr)); gap:8px; }}
.land-entry {{ background:#16213e; border-radius:6px; padding:8px 14px; }}
</style>
</head>
<body>
<h1>TMT Sealed Deck — UR Artifacts</h1>
<p class="subtitle">Forget synergy scores — play the best cards, curve out, win with bombs</p>

<div class="stats-bar">
  <div class="stat stat-creatures"><div class="stat-num">{creature_count}</div><div class="stat-label">Creatures</div></div>
  <div class="stat stat-noncreature"><div class="stat-num">{noncreature_count}</div><div class="stat-label">Noncreature</div></div>
  <div class="stat stat-lands"><div class="stat-num">{land_count}</div><div class="stat-label">Lands</div></div>
  <div class="stat stat-total"><div class="stat-num">{total}</div><div class="stat-label">Total</div></div>
</div>
""")

# Mana Curve
max_count = max(curve.values()) if curve else 1
html_out.append('<h2>Mana Curve</h2>\n<div class="curve-container">\n')
for cmc_val in range(1, 8):
    count = curve.get(cmc_val, 0)
    height = int((count / max_count) * 90) if max_count else 0
    html_out.append(f'  <div class="curve-bar"><div class="curve-count">{count}</div><div class="curve-fill" style="height:{height}px"></div><div class="curve-label">CMC {cmc_val}</div></div>\n')
html_out.append('</div>\n')

# Color Sources
html_out.append("""<h2>Color Sources</h2>
<div class="color-sources">
  <div class="color-source">
    <div class="color-source-name" style="color:#4ecdc4;">Blue — ~10 sources</div>
    <div style="font-size:0.82em;color:#999;">7 Island + 1 Escape Tunnel + 2 Omni-Cheese</div>
    <div class="color-source-bar" style="background:linear-gradient(90deg,#4ecdc4 100%,#333 0%);"></div>
  </div>
  <div class="color-source">
    <div class="color-source-name" style="color:#ff6b6b;">Red — ~9 sources</div>
    <div style="font-size:0.82em;color:#999;">6 Mountain + 1 Escape Tunnel + 2 Omni-Cheese</div>
    <div class="color-source-bar" style="background:linear-gradient(90deg,#ff6b6b 90%,#333 0%);"></div>
  </div>
  <div class="color-source">
    <div class="color-source-name" style="color:#9b59b6;">Black (splash) — ~5 sources</div>
    <div style="font-size:0.82em;color:#999;">1 Swamp + 1 IB + 1 Escape Tunnel + 2 Omni-Cheese</div>
    <div class="color-source-bar" style="background:linear-gradient(90deg,#9b59b6 50%,#333 0%);"></div>
  </div>
</div>
""")

# Card sections
def render_section(title, cards, show_notes=True):
    html_out.append(f'<h2>{title}</h2>\n<div class="card-grid">\n')
    for entry in cards:
        name = entry["name"]
        qty = entry["qty"]
        cmc = entry.get("cmc", 0)
        splash = entry.get("splash", False)
        note = entry.get("note", "")
        card_data = get_card(name)
        rarity = card_data.get("rarity", "common")
        mana_cost = card_data.get("mana_cost", "")
        pt = ""
        if card_data.get("power"):
            pt = f"{card_data['power']}/{card_data['toughness']}"
        img = get_image(name)
        splash_html = '<span class="splash-badge">SPLASH</span>' if splash else ""
        note_html = f'<div class="card-note">{html.escape(note)}</div>' if note and show_notes else ""

        html_out.append(f"""  <div class="card-entry rarity-{rarity}" data-img="{img}">
    <div>
      <div><span class="card-qty">{qty}x</span><span class="card-name">{html.escape(name)}</span>{splash_html}</div>
      <div class="card-meta">{mana_cost} · CMC {cmc}{(' · ' + pt) if pt else ''}</div>
      {note_html}
    </div>
  </div>
""")
    html_out.append('</div>\n')

render_section(f"Creatures ({creature_count})", deck["creatures"])
render_section(f"Noncreature Spells ({noncreature_count})", deck["noncreature"])

# Lands
html_out.append(f'<h2>Lands ({land_count})</h2>\n<div class="land-grid">\n')
for entry in deck["lands"]:
    name = entry["name"]
    qty = entry["qty"]
    html_out.append(f'  <div class="land-entry"><span class="card-qty">{qty}x</span> {html.escape(name)}</div>\n')
html_out.append('</div>\n')

# Synergy
html_out.append("""<h2>Key Synergies</h2>
<div class="synergy-list">
  <div class="synergy-item"><span class="synergy-label">Artifact Flood:</span> Omni-Cheese Pizza, Mouser Attack! tokens, Turtle Blimp token, Mutagen tokens — each one grows Donatello Way with Machines</div>
  <div class="synergy-item"><span class="synergy-label">Chrome Dome Lord:</span> All artifact creatures (robots, vehicles) get +1/+0. Copy an Omni-Cheese or Jitte for {5}</div>
  <div class="synergy-item"><span class="synergy-label">Donatello Mechanic:</span> Tap to put three +1/+1 counters on any artifact and animate it. Turn Omni-Cheese into a 3/3, Jitte into a 3/3 double-striker</div>
  <div class="synergy-item"><span class="synergy-label">Nobody Bounce:</span> Return Omni-Cheese or Bespoke Bō to hand → replay for ETB value (draw card, bounce permanent) + grows Donatello</div>
  <div class="synergy-item"><span class="synergy-label">Double Strike Package:</span> Hard-Won Jitte on any creature = double damage. On Mondo Gecko (hexproof) or a Donatello with counters = lethal</div>
  <div class="synergy-item"><span class="synergy-label">Mondo Gecko Engine:</span> Draws + discards every end step. Filters to your bombs, fuels graveyard</div>
  <div class="synergy-item"><span class="synergy-label">Kitsune Finisher:</span> 6/6 vigilance that steals a creature on ETB or combat damage. Swings the board</div>
  <div class="synergy-item"><span class="synergy-label">Free Splashes:</span> Krang ({U/B}{U/B} = just {B}{B}), Squirrelanoids ({B}) — only need 1 Swamp + fixing</div>
</div>
""")

# Explanation
html_out.append("""<h2>Why UR over BG?</h2>
<div class="explanation">
  <p><strong>The BG Disappear deck had a fatal flaw:</strong> weak payoffs. Insectoid Exterminator's scry 1 is not worth building around. The deck had 9 cards at CMC 4, splashed two colors, and the reward for all that complexity was... scry 1. It got run over by turn 4-5.</p>
  <p><strong>This UR build fixes everything:</strong></p>
  <p>• <strong>11 two-drops</strong> vs the old deck's 5-6. You actually curve out and contest the board early.</p>
  <p>• <strong>Real bombs:</strong> Mondo Gecko, Donatello Mechanic, Kitsune, Krang & Shredder, Cool but Rude, Chrome Dome — six rares/mythics that each win the game on their own.</p>
  <p>• <strong>Artifact synergy has teeth:</strong> Unlike Disappear's scry, artifacts here create a snowball effect. Donatello grows, Chrome Dome pumps the team, Mechanic animates artifacts into threats, Nobody bounces for repeated ETBs.</p>
  <p>• <strong>Minimal splash:</strong> Just 1 Swamp + Escape Tunnel + IB + 2 Omni-Cheese for Squirrelanoids and Krang hybrid. No greedy 4-color manabase.</p>
  <p>• <strong>Real removal:</strong> Bot Bashing Time (6 damage exile), Cool but Rude (level 3 = 4 damage), Bespoke Bō (bounce), Kitsune (steal).</p>
</div>
""")

# Card preview JS
html_out.append("""
<img id="card-preview" class="card-preview" src="" alt="">
<script>
const preview = document.getElementById('card-preview');
document.querySelectorAll('.card-entry').forEach(el => {
    const img = el.dataset.img;
    if (!img) return;
    el.addEventListener('mouseenter', e => {
        preview.src = img;
        preview.style.display = 'block';
    });
    el.addEventListener('mousemove', e => {
        let x = e.clientX + 20, y = e.clientY - 100;
        if (x + 260 > window.innerWidth) x = e.clientX - 270;
        if (y < 10) y = 10;
        if (y + 360 > window.innerHeight) y = window.innerHeight - 360;
        preview.style.left = x + 'px';
        preview.style.top = y + 'px';
    });
    el.addEventListener('mouseleave', () => { preview.style.display = 'none'; });
});
</script>
</body></html>""")

output = "\n".join(html_out)
with open("/home/morris/Projects/mtga-draft-helper/TMT_Sealed_Deck.html", "w") as f:
    f.write(output)

print(f"Written TMT_Sealed_Deck.html ({len(output)} bytes)")
print(f"Deck: {creature_count} creatures + {noncreature_count} noncreature + {land_count} lands = {total} cards")
