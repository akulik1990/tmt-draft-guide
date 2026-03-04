#!/usr/bin/env python3
"""Build an HTML table of the sealed pool with full card details."""

import json

MANA_SYMBOLS = {
    "{W}": '<span class="mana mana-w">W</span>',
    "{U}": '<span class="mana mana-u">U</span>',
    "{B}": '<span class="mana mana-b">B</span>',
    "{R}": '<span class="mana mana-r">R</span>',
    "{G}": '<span class="mana mana-g">G</span>',
    "{C}": '<span class="mana mana-c">C</span>',
    "{X}": '<span class="mana mana-x">X</span>',
}
for i in range(21):
    MANA_SYMBOLS[f"{{{i}}}"] = f'<span class="mana mana-n">{i}</span>'

COLOR_MAP = {"W": "#f9faf4", "U": "#0e68ab", "B": "#150b00", "R": "#d3202a", "G": "#00733e"}
COLOR_NAME = {"W": "White", "U": "Blue", "B": "Black", "R": "Red", "G": "Green"}
RARITY_COLOR = {"common": "#8a8a8a", "uncommon": "#8cc4c4", "rare": "#dbb44e", "mythic": "#e86420"}
RARITY_ABBR = {"common": "C", "uncommon": "U", "rare": "R", "mythic": "M"}

MECH_COLOR = {
    "Sneak": "#a855f7",
    "Disappear": "#6b7280",
    "Alliance": "#ef4444",
    "Mutagen": "#22c55e",
    "Artifacts-matter": "#3b82f6",
    "Food": "#a3693b",
}

ROLE_COLOR = {
    "Removal": "#ef4444",
    "Evasion": "#60a5fa",
    "Card Advantage": "#a78bfa",
    "Combat Trick": "#f97316",
    "Fixing": "#fbbf24",
    "Token Maker": "#34d399",
}


def format_mana(mana_cost: str) -> str:
    result = mana_cost
    for sym, html in MANA_SYMBOLS.items():
        result = result.replace(sym, html)
    return result


def format_colors(colors: list) -> str:
    if not colors:
        return '<span style="color:#ccc;">Colorless</span>'
    dots = []
    for c in colors:
        dots.append(f'<span class="color-pip" style="background:{COLOR_MAP.get(c,"#888")};" title="{COLOR_NAME.get(c,c)}"></span>')
    return " ".join(dots)


def format_tags(items: list, color_map: dict) -> str:
    if not items:
        return '<span style="color:#555;">—</span>'
    tags = []
    for item in items:
        c = color_map.get(item, "#555")
        tags.append(f'<span class="tag" style="background:{c}20;color:{c};border-color:{c}40;">{item}</span>')
    return " ".join(tags)


def build_html(cards: list) -> str:
    # Sort by color identity then CMC
    color_order = {"W": 0, "U": 1, "B": 2, "R": 3, "G": 4}

    def sort_key(c):
        ci = c["color_identity"]
        if not ci:
            return (6, c["cmc"], c["name"])
        if len(ci) == 1:
            return (color_order.get(ci[0], 5), c["cmc"], c["name"])
        return (5, c["cmc"], c["name"])

    cards_sorted = sorted(cards, key=sort_key)

    # Expand quantities
    rows = []
    idx = 1
    for card in cards_sorted:
        for copy in range(card["qty"]):
            rows.append((idx, card, copy + 1))
            idx += 1

    total = len(rows)

    # Stats
    color_counts = {}
    rarity_counts = {}
    cmc_counts = {}
    type_counts = {"Creature": 0, "Instant": 0, "Sorcery": 0, "Enchantment": 0, "Artifact": 0, "Land": 0, "Other": 0}

    for _, card, _ in rows:
        for c in card["colors"]:
            color_counts[c] = color_counts.get(c, 0) + 1
        rarity_counts[card["rarity"]] = rarity_counts.get(card["rarity"], 0) + 1
        cmc_counts[card["cmc"]] = cmc_counts.get(card["cmc"], 0) + 1
        tl = card["type_line"].lower()
        found = False
        for t in ["creature", "instant", "sorcery", "enchantment", "artifact", "land"]:
            if t in tl:
                type_counts[t.capitalize()] += 1
                found = True
                break
        if not found:
            type_counts["Other"] += 1

    # Build table rows
    table_rows = []
    for num, card, copy_num in rows:
        qty_label = f'<span class="qty-badge">{card["qty"]}x</span>' if card["qty"] > 1 and copy_num == 1 else f'<span class="qty-badge dim">{copy_num}/{card["qty"]}</span>' if card["qty"] > 1 else ""

        pt = f'{card["power"]}/{card["toughness"]}' if card["power"] else "—"
        rarity_c = RARITY_COLOR.get(card["rarity"], "#888")
        rarity_a = RARITY_ABBR.get(card["rarity"], "?")

        kw_str = ", ".join(card["keywords"]) if card["keywords"] else "—"

        # Truncate oracle text for table
        oracle = card["oracle_text"].replace("\n", " ⟐ ")
        if len(oracle) > 120:
            oracle_short = oracle[:117] + "..."
        else:
            oracle_short = oracle

        img_url = card["image_uri"]

        table_rows.append(f"""    <tr class="card-row" data-colors="{','.join(card['color_identity'])}" data-rarity="{card['rarity']}" data-cmc="{card['cmc']}">
      <td class="idx">{num}</td>
      <td class="card-name-cell">
        <div class="card-name-wrap">
          <img src="{img_url}" alt="{card['name']}" class="card-thumb" loading="lazy"
               onerror="this.style.display='none'">
          <div>
            <span class="card-name">{card['name']}</span> {qty_label}
            <div class="card-type">{card['type_line']}</div>
          </div>
        </div>
      </td>
      <td class="mana-cell">{format_mana(card['mana_cost'])}</td>
      <td class="cmc-cell">{card['cmc']}</td>
      <td class="color-cell">{format_colors(card['colors'])}</td>
      <td><span class="rarity-badge" style="background:{rarity_c};">{rarity_a}</span></td>
      <td class="pt-cell">{pt}</td>
      <td class="kw-cell">{kw_str}</td>
      <td class="mech-cell">{format_tags(card['tmt_mechanics'], MECH_COLOR)}</td>
      <td class="role-cell">{format_tags(card['roles'], ROLE_COLOR)}</td>
      <td class="oracle-cell" title="{card['oracle_text'].replace(chr(34), '&quot;')}">{oracle_short}</td>
    </tr>""")

    # Color stats bar
    color_bar = ""
    for c in ["W", "U", "B", "R", "G"]:
        cnt = color_counts.get(c, 0)
        pct = cnt / total * 100 if total else 0
        color_bar += f'<div class="stat-segment" style="width:{pct}%;background:{COLOR_MAP[c]};" title="{COLOR_NAME[c]}: {cnt}"></div>'

    colorless_cnt = total - sum(color_counts.values())

    # Rarity stats
    rarity_pills = ""
    for r in ["mythic", "rare", "uncommon", "common"]:
        cnt = rarity_counts.get(r, 0)
        rc = RARITY_COLOR.get(r, "#888")
        rarity_pills += f'<span class="stat-pill" style="border-color:{rc};color:{rc};">{RARITY_ABBR[r]}: {cnt}</span> '

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TMT Sealed Pool — 81 Cards</title>
<style>
  :root {{
    --bg: #0f0f1a;
    --surface: #1a1a2e;
    --surface2: #252542;
    --border: #2a2a4a;
    --text: #e8e8f0;
    --text-muted: #8888a8;
    --accent: #e94560;
    --gold: #f5c542;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:var(--bg); color:var(--text); }}

  .header {{ background:linear-gradient(135deg,#0f3460,#1a1a2e); border-bottom:3px solid var(--accent); padding:2rem; text-align:center; }}
  .header h1 {{ font-size:2.2rem; background:linear-gradient(90deg,var(--accent),var(--gold)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
  .header .sub {{ color:var(--text-muted); margin-top:0.3rem; }}

  .stats {{ display:flex; gap:1.5rem; flex-wrap:wrap; padding:1.5rem 2rem; max-width:1600px; margin:0 auto; }}
  .stat-card {{ background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:1rem 1.5rem; flex:1; min-width:180px; }}
  .stat-card .label {{ color:var(--text-muted); font-size:0.8rem; text-transform:uppercase; letter-spacing:1px; }}
  .stat-card .value {{ font-size:1.8rem; font-weight:700; color:var(--gold); margin:0.25rem 0; }}
  .stat-card .detail {{ color:var(--text-muted); font-size:0.85rem; }}

  .stat-bar {{ display:flex; height:8px; border-radius:4px; overflow:hidden; margin-top:0.5rem; }}
  .stat-segment {{ transition:width 0.3s; }}
  .stat-pill {{ display:inline-block; border:1px solid; border-radius:12px; padding:0.15rem 0.6rem; font-size:0.8rem; font-weight:600; margin-right:0.3rem; }}

  .filters {{ padding:0.75rem 2rem; max-width:1600px; margin:0 auto; display:flex; gap:0.5rem; flex-wrap:wrap; align-items:center; }}
  .filters label {{ color:var(--text-muted); font-size:0.85rem; margin-right:0.25rem; }}
  .filter-btn {{ background:var(--surface); border:1px solid var(--border); color:var(--text-muted); border-radius:6px; padding:0.3rem 0.7rem; cursor:pointer; font-size:0.8rem; transition:all 0.15s; }}
  .filter-btn:hover,.filter-btn.active {{ background:var(--accent); color:#fff; border-color:var(--accent); }}

  .table-wrap {{ overflow-x:auto; padding:0 1rem 2rem; max-width:1600px; margin:0 auto; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.85rem; }}
  thead th {{ background:var(--surface2); color:var(--gold); padding:0.6rem 0.5rem; text-align:left; position:sticky; top:0; z-index:2; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.5px; cursor:pointer; white-space:nowrap; border-bottom:2px solid var(--border); }}
  thead th:hover {{ color:var(--accent); }}
  tbody td {{ padding:0.5rem; border-bottom:1px solid var(--border); vertical-align:middle; }}
  .card-row:hover td {{ background:rgba(233,69,96,0.05); }}

  .idx {{ color:var(--text-muted); font-size:0.75rem; text-align:center; width:30px; }}
  .card-name-cell {{ min-width:220px; }}
  .card-name-wrap {{ display:flex; align-items:center; gap:0.5rem; }}
  .card-thumb {{ width:40px; height:56px; border-radius:4px; object-fit:cover; flex-shrink:0; box-shadow:0 2px 6px rgba(0,0,0,0.4); cursor:pointer; transition:transform 0.2s; }}
  .card-thumb:hover {{ transform:scale(3.5); z-index:100; position:relative; }}
  .card-name {{ font-weight:600; color:var(--text); font-size:0.9rem; }}
  .card-type {{ color:var(--text-muted); font-size:0.75rem; }}

  .qty-badge {{ background:var(--accent); color:#fff; font-size:0.65rem; padding:0.1rem 0.35rem; border-radius:8px; font-weight:700; margin-left:0.3rem; }}
  .qty-badge.dim {{ background:var(--surface2); color:var(--text-muted); }}

  .mana {{ display:inline-flex; align-items:center; justify-content:center; width:18px; height:18px; border-radius:50%; font-size:0.65rem; font-weight:700; margin:0 1px; }}
  .mana-w {{ background:#f9faf4; color:#333; }}
  .mana-u {{ background:#0e68ab; color:#fff; }}
  .mana-b {{ background:#150b00; color:#ccc; border:1px solid #444; }}
  .mana-r {{ background:#d3202a; color:#fff; }}
  .mana-g {{ background:#00733e; color:#fff; }}
  .mana-c {{ background:#888; color:#fff; }}
  .mana-n {{ background:#666; color:#fff; }}
  .mana-x {{ background:#555; color:#ddd; }}
  .mana-cell {{ white-space:nowrap; }}
  .cmc-cell {{ text-align:center; color:var(--text-muted); }}

  .color-pip {{ display:inline-block; width:12px; height:12px; border-radius:50%; border:1px solid rgba(255,255,255,0.2); }}
  .color-cell {{ white-space:nowrap; }}

  .rarity-badge {{ display:inline-block; width:22px; height:22px; border-radius:50%; text-align:center; line-height:22px; font-size:0.7rem; font-weight:700; color:#111; }}

  .pt-cell {{ text-align:center; font-weight:600; white-space:nowrap; }}
  .kw-cell {{ color:var(--text-muted); font-size:0.8rem; max-width:140px; }}

  .tag {{ display:inline-block; padding:0.1rem 0.45rem; border-radius:4px; font-size:0.7rem; font-weight:600; border:1px solid; margin:1px; white-space:nowrap; }}
  .mech-cell,.role-cell {{ min-width:100px; }}

  .oracle-cell {{ color:var(--text-muted); font-size:0.78rem; max-width:280px; line-height:1.3; }}

  .footer {{ text-align:center; color:var(--text-muted); font-size:0.8rem; padding:1.5rem; border-top:1px solid var(--border); }}

  @media(max-width:900px) {{
    .card-thumb {{ display:none; }}
    .oracle-cell {{ display:none; }}
    .kw-cell {{ display:none; }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>🐢 TMT Sealed Pool</h1>
  <div class="sub">{total} cards — Teenage Mutant Ninja Turtles Sealed</div>
</div>

<div class="stats">
  <div class="stat-card">
    <div class="label">Total Cards</div>
    <div class="value">{total}</div>
    <div class="detail">{len(cards)} unique</div>
  </div>
  <div class="stat-card">
    <div class="label">Colors</div>
    <div class="value" style="font-size:1.2rem;">
      {'  '.join(f'<span style="color:{COLOR_MAP[c]}">{COLOR_NAME[c][0]}:{color_counts.get(c,0)}</span>' for c in "WUBRG")}
    </div>
    <div class="stat-bar">{color_bar}</div>
  </div>
  <div class="stat-card">
    <div class="label">Rarities</div>
    <div class="value" style="font-size:1rem;">{rarity_pills}</div>
  </div>
  <div class="stat-card">
    <div class="label">Creatures</div>
    <div class="value">{type_counts['Creature']}</div>
    <div class="detail">of {total} total cards</div>
  </div>
</div>

<div class="filters">
  <label>Filter:</label>
  <button class="filter-btn active" onclick="filterCards('all')">All</button>
  <button class="filter-btn" onclick="filterCards('W')" style="border-color:#f9faf4;">White</button>
  <button class="filter-btn" onclick="filterCards('U')" style="border-color:#0e68ab;">Blue</button>
  <button class="filter-btn" onclick="filterCards('B')" style="border-color:#666;">Black</button>
  <button class="filter-btn" onclick="filterCards('R')" style="border-color:#d3202a;">Red</button>
  <button class="filter-btn" onclick="filterCards('G')" style="border-color:#00733e;">Green</button>
  <button class="filter-btn" onclick="filterCards('multi')">Multi</button>
  <button class="filter-btn" onclick="filterCards('colorless')">Colorless</button>
  <span style="margin-left:1rem;"></span>
  <label>Rarity:</label>
  <button class="filter-btn" onclick="filterRarity('mythic')" style="border-color:#e86420;">M</button>
  <button class="filter-btn" onclick="filterRarity('rare')" style="border-color:#dbb44e;">R</button>
  <button class="filter-btn" onclick="filterRarity('uncommon')" style="border-color:#8cc4c4;">U</button>
  <button class="filter-btn" onclick="filterRarity('common')" style="border-color:#8a8a8a;">C</button>
</div>

<div class="table-wrap">
<table id="poolTable">
  <thead>
    <tr>
      <th onclick="sortTable(0)">#</th>
      <th onclick="sortTable(1)">Card</th>
      <th onclick="sortTable(2)">Mana</th>
      <th onclick="sortTable(3)">CMC</th>
      <th onclick="sortTable(4)">Colors</th>
      <th onclick="sortTable(5)">Rar</th>
      <th onclick="sortTable(6)">P/T</th>
      <th onclick="sortTable(7)">Keywords</th>
      <th>TMT Mechanics</th>
      <th>Roles</th>
      <th>Oracle Text</th>
    </tr>
  </thead>
  <tbody>
{"".join(table_rows)}
  </tbody>
</table>
</div>

<div class="footer">
  Data from Scryfall API · Card images © Wizards of the Coast
</div>

<script>
function filterCards(color) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('.card-row').forEach(row => {{
    const colors = row.dataset.colors;
    if (color === 'all') {{ row.style.display = ''; }}
    else if (color === 'multi') {{ row.style.display = colors.includes(',') ? '' : 'none'; }}
    else if (color === 'colorless') {{ row.style.display = colors === '' ? '' : 'none'; }}
    else {{ row.style.display = colors.includes(color) ? '' : 'none'; }}
  }});
}}

function filterRarity(r) {{
  document.querySelectorAll('.card-row').forEach(row => {{
    row.style.display = row.dataset.rarity === r ? '' : 'none';
  }});
}}

let sortDir = {{}};
function sortTable(col) {{
  const table = document.getElementById('poolTable');
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.rows);
  sortDir[col] = !sortDir[col];
  rows.sort((a, b) => {{
    let aVal = a.cells[col].textContent.trim();
    let bVal = b.cells[col].textContent.trim();
    let aNum = parseFloat(aVal);
    let bNum = parseFloat(bVal);
    if (!isNaN(aNum) && !isNaN(bNum)) {{
      return sortDir[col] ? aNum - bNum : bNum - aNum;
    }}
    return sortDir[col] ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
  }});
  rows.forEach(r => tbody.appendChild(r));
}}
</script>

</body>
</html>"""
    return html


def main():
    with open("/home/morris/Projects/mtga-draft-helper/sealed_pool_data.json") as f:
        cards = json.load(f)

    html = build_html(cards)

    out_path = "/home/morris/Projects/mtga-draft-helper/TMT_Sealed_Pool.html"
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Written to {out_path}")


if __name__ == "__main__":
    main()
