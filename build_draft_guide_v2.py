#!/usr/bin/env python3
"""Build TMT Draft Guide v2 — Editable card positions, 2-tab layout, localStorage persistence.

Data sources:
- Scryfall card database (images, oracle text, stats)
- 17Lands card_ratings API (GIH win rates, ALSA)
- Multiple guide sources (archetype data, strategy tips)

Output:
- TMT_Draft_Guide.html (single file, embeds card_config as JS object)
"""

import json
import html as html_mod
import unicodedata
import re

# ── Load data ──────────────────────────────────────────────────────────────
with open('/home/morris/Projects/tmt-draft-guide/tmt_scryfall_cards.json') as f:
    scryfall = json.load(f)

with open('/home/morris/Projects/tmt-draft-guide/tmt_17lands_ratings.json') as f:
    lands17 = json.load(f)

with open('/home/morris/Projects/tmt-draft-guide/tmt_17lands_tierlist.json') as f:
    tierlist_data = json.load(f)

# Fix known 17lands name corruptions
NAME_FIXES = {'Bespoke B?': 'Bespoke Bō'}

def normalize_name(name):
    name = NAME_FIXES.get(name, name)
    nfkd = unicodedata.normalize('NFKD', name)
    stripped = ''.join(ch for ch in nfkd if unicodedata.category(ch) != 'Mn')
    return stripped.lower()

# Build lookups
lands_map = {}
lands_norm = {}
for c in lands17:
    lands_map[c['name']] = c
    lands_norm[normalize_name(c['name'])] = c

tier_map = {}
tier_norm = {}
for c in tierlist_data['tmt_cards']:
    tier_map[c['name']] = c['tier']
    tier_norm[normalize_name(c['name'])] = c['tier']
for c in tierlist_data['source_material']:
    tier_map[c['name']] = c['tier']
    tier_norm[normalize_name(c['name'])] = c['tier']

scryfall_canon = {}
for sname in scryfall:
    scryfall_canon[normalize_name(sname)] = sname

def canonical_name(name):
    return scryfall_canon.get(normalize_name(name), name)

# ── Helpers ──────────────────────────────────────────────────────────────
def get_img(card_name, size='normal'):
    sf = scryfall.get(card_name)
    if sf:
        return sf.get(f'image_{size}', sf.get('image_normal', ''))
    for name, data in scryfall.items():
        if card_name.lower() in name.lower() or name.lower() in card_name.lower():
            return data.get(f'image_{size}', data.get('image_normal', ''))
    return ''

def get_17l(card_name):
    c = lands_map.get(card_name) or lands_norm.get(normalize_name(card_name))
    if c:
        return {'gih': c.get('ever_drawn_win_rate'), 'alsa': c.get('avg_seen'), 'games': c.get('game_count') or 0}
    for name, data in lands_map.items():
        if card_name.lower() in name.lower() or name.lower() in card_name.lower():
            return {'gih': data.get('ever_drawn_win_rate'), 'alsa': data.get('avg_seen'), 'games': data.get('game_count') or 0}
    return {'gih': None, 'alsa': None, 'games': 0}

def get_sf_data(card_name):
    sf = scryfall.get(card_name)
    if sf:
        return sf
    for name, data in scryfall.items():
        if card_name.lower() in name.lower() or name.lower() in card_name.lower():
            return data
    return {}

def get_tier(card_name):
    t = tier_map.get(card_name) or tier_norm.get(normalize_name(card_name))
    if t: return t
    for name, grade in tier_map.items():
        if card_name.lower() in name.lower() or name.lower() in card_name.lower():
            return grade
    return None

def grade_color(grade):
    colors = {
        'A+': '#ff4757', 'A': '#ee5a24', 'A-': '#f39c12',
        'B+': '#f1c40f', 'B': '#2ecc71', 'B-': '#1abc9c',
        'C+': '#3498db', 'C': '#95a5a6', 'C-': '#7f8c8d',
        'D+': '#636e72', 'D': '#4a4a4a', 'D-': '#3d3d3d', 'F': '#2d3436',
    }
    return colors.get(grade, '#95a5a6')

def get_diwr(card_name):
    c = lands_map.get(card_name) or lands_norm.get(normalize_name(card_name))
    if c:
        drawn = c.get('ever_drawn_win_rate')
        not_drawn = c.get('never_drawn_win_rate')
        if drawn is not None and not_drawn is not None:
            return drawn - not_drawn
    return None

TIER_RANK = {t: i for i, t in enumerate(['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F'])}

# ── Color / Archetype logic ──────────────────────────────────────────────
MANA_SYMBOL_MAP = {'{W}': 'W', '{U}': 'U', '{B}': 'B', '{R}': 'R', '{G}': 'G'}

def get_card_colors(card_name):
    sf = get_sf_data(card_name)
    colors = set(sf.get('colors', []))
    if not colors and 'Land' in sf.get('type_line', ''):
        oracle = sf.get('oracle_text', '')
        for symbol, color in MANA_SYMBOL_MAP.items():
            if f'Add {symbol}' in oracle or f'add {symbol}' in oracle:
                colors.add(color)
    return colors

def is_land(card_name):
    sf = get_sf_data(card_name)
    return 'Land' in sf.get('type_line', '')

def card_fits_archetype(card_colors, arch_colors, land=False):
    if not card_colors:
        return True
    if land and len(card_colors) >= 2:
        return card_colors == arch_colors
    return card_colors <= arch_colors

# ── ARCHETYPES ──────────────────────────────────────────────────────────
ARCHETYPES = [
    {
        'id': 'ur_artifacts', 'name': 'UR Artifacts', 'colors': ['U', 'R'],
        'color_hex': '#9b59b6', 'icon': '⚙️',
        'short': 'Artifacts-matter aggro/tempo. Play cheap artifact creatures, buff them, generate value.',
        'strategy': 'Draft artifact creatures highly. Brilliance Unleashed is the payoff. Metalhead, Buzz Bots, Mouser Foundry are key. Manhole Missile is premium removal that also makes artifacts.',
        'signposts': ['Brilliance Unleashed', 'Metalhead'],
        'payoffs': ['Brilliance Unleashed', 'Metalhead', 'Does Machines', 'Chrome Dome', 'Mouser Mark III'],
        'enablers': ['Buzz Bots', 'Mouser Foundry', 'Manhole Missile', 'Ravenous Robots', 'Sewer-veillance Cam', 'Nobody'],
        'removal': ['Manhole Missile', 'Bot Bashing Time', 'Return to the Sewers', 'Mind Transfer Protocol'],
        'role_players': ['Donatello, Turtle Techie', 'Pepperoni Shuriken'],
        'key_synergies': [
            ('Brilliance Unleashed', 'Any artifact creature', 'Buff entire board when artifacts ETB'),
            ('Mouser Foundry', 'Sacrifice outlet', 'Generate artifact tokens repeatedly'),
            ('Metalhead', 'Artifact tokens', 'Copies artifact creatures for massive value'),
        ],
    },
    {
        'id': 'wb_sneak', 'name': 'WB Sneak', 'colors': ['W', 'B'],
        'color_hex': '#95a5a6', 'icon': '🥷',
        'short': 'Evasion & disruption. Sneak creatures deal combat damage → trigger bonus effects.',
        'strategy': 'Draft Sneak creatures that get value from dealing damage. Combine evasion (flying, unblockable) with Sneak payoffs. Removal-heavy to clear path.',
        'signposts': ['Karai, Future of the Foot', 'Foot Ninjas'],
        'payoffs': ['Turncoat Kunoichi', 'Karai, Future of the Foot', 'Oroku Saki, Shredder Rising', "April O'Neil, Kunoichi Trainee"],
        'enablers': ['Foot Ninjas', 'Leonardo, Big Brother', 'Dimensional Exile', 'Grounded for Life'],
        'removal': ['Dimensional Exile', 'Stomped by the Foot', 'Anchovy & Banana Pizza', 'Grounded for Life', 'Tainted Treats'],
        'role_players': ['Mighty Mutanimals', 'Uneasy Alliance'],
        'key_synergies': [
            ('Turncoat Kunoichi', 'Any Sneak creature', 'Repeated disruption on combat damage'),
            ('Karai, Future of the Foot', 'Foot Ninjas', 'Signpost combo: evasive + payoff'),
            ('Dimensional Exile', 'Any creature', 'Premium removal clears path for Sneak'),
        ],
    },
    {
        'id': 'bg_disappear', 'name': 'BG Disappear', 'colors': ['B', 'G'],
        'color_hex': '#27ae60', 'icon': '💀',
        'short': 'Sacrifice & recursion. Cards Disappear (exile from grave) to fuel powerful effects.',
        'strategy': 'Self-mill and sacrifice to fill graveyard, then Disappear cards for value. Strong midrange/grindy plan. Courier of Comestibles is a top common.',
        'signposts': ['Slash, Reptile Rampager', 'Leatherhead, Swamp Stalker'],
        'payoffs': ['Slash, Reptile Rampager', 'Leatherhead, Swamp Stalker', 'Squirrelanoids', 'Ragamuffin Raptor'],
        'enablers': ['Frog Butler', 'Courier of Comestibles', 'Ice Cream Kitty', 'Tenderize'],
        'removal': ['Stomped by the Foot', 'Anchovy & Banana Pizza', 'Tenderize', 'Tainted Treats'],
        'role_players': ['Primordial Pachyderm', 'Michelangelo, Game Master', 'Zoo Escapees'],
        'key_synergies': [
            ('Frog Butler', 'Sacrifice outlets', 'Recursive value engine from graveyard'),
            ('Courier of Comestibles', 'Disappear cards', 'Food tokens + Disappear synergy'),
            ('Slash, Reptile Rampager', 'Self-mill', 'Grows huge from Disappear count'),
        ],
    },
    {
        'id': 'rw_alliance', 'name': 'RW Alliance', 'colors': ['R', 'W'],
        'color_hex': '#e74c3c', 'icon': '⚔️',
        'short': 'Go-wide aggro. Alliance triggers when creatures ETB. Tokens + anthems.',
        'strategy': 'Play creatures that trigger Alliance on ETB. Token generators are great. Mechanized Ninja Cavalry is a key common. Curve out aggressively.',
        'signposts': ['Groundchuck & Dirtbag', 'Mechanized Ninja Cavalry'],
        'payoffs': ['Groundchuck & Dirtbag', 'Mechanized Ninja Cavalry', "April O'Neil, Kunoichi Trainee", 'Action News Crew'],
        'enablers': ['Go Ninja Go', 'Mouser Foundry', 'Rock Soldiers', 'Manhole Missile'],
        'removal': ['Manhole Missile', 'Bot Bashing Time', 'Dimensional Exile', 'Grounded for Life'],
        'role_players': ['Mighty Mutanimals', 'Leonardo, Big Brother', 'Raph & Mikey, Troublemakers'],
        'key_synergies': [
            ('Mechanized Ninja Cavalry', 'Token makers', 'Multiple Alliance triggers per turn'),
            ('Groundchuck & Dirtbag', 'Go-wide board', 'Signpost gives team buffs on Alliance'),
            ('Go Ninja Go', 'Any creatures', 'Pump + Alliance synergy'),
        ],
    },
    {
        'id': 'gu_mutagen', 'name': 'GU Mutagen', 'colors': ['G', 'U'],
        'color_hex': '#2ecc71', 'icon': '🧬',
        'short': '+1/+1 counters & mutation. Mutagen creatures grow and gain abilities.',
        'strategy': 'Draft creatures that use +1/+1 counters and Mutagen. Build big threats over time. Tempo + size advantage. Mikey & Don, Party Planners is the top signpost.',
        'signposts': ['Mikey & Don, Party Planners', 'Slithering Cryptid'],
        'payoffs': ['Mikey & Don, Party Planners', 'Donatello, Turtle Techie', 'Slithering Cryptid'],
        'enablers': ['Return to the Sewers', 'Buzz Bots', 'Retro-Mutation', 'Frog Butler'],
        'removal': ['Return to the Sewers', 'Mind Transfer Protocol', 'Tenderize'],
        'role_players': ['Primordial Pachyderm', 'Michelangelo, Game Master', 'Courier of Comestibles'],
        'key_synergies': [
            ('Mikey & Don, Party Planners', '+1/+1 counter cards', 'Signpost grows entire team'),
            ('Donatello, Turtle Techie', 'Artifacts', 'Draws cards + grows with counters'),
            ('Return to the Sewers', 'Any creature', 'Bounce + Mutagen counter'),
        ],
    },
]

REMOVAL = [
    {'name': 'Dimensional Exile', 'color': 'W', 'type': 'unconditional'},
    {'name': 'Grounded for Life', 'color': 'W', 'type': 'conditional'},
    {'name': 'Stomped by the Foot', 'color': 'B', 'type': 'unconditional'},
    {'name': 'Anchovy & Banana Pizza', 'color': 'B', 'type': 'unconditional'},
    {'name': 'Tainted Treats', 'color': 'B', 'type': 'conditional'},
    {'name': 'Manhole Missile', 'color': 'R', 'type': 'conditional'},
    {'name': 'Bot Bashing Time', 'color': 'R', 'type': 'conditional'},
    {'name': 'Tenderize', 'color': 'G', 'type': 'conditional'},
    {'name': 'Return to the Sewers', 'color': 'U', 'type': 'bounce'},
    {'name': 'Mind Transfer Protocol', 'color': 'U', 'type': 'unconditional'},
]

# ── Auto-tagging via oracle text heuristics ──────────────────────────────
TAG_PATTERNS = {
    'token-maker':       re.compile(r'create[s]?\b.+\btoken', re.I),
    'evasion':           re.compile(r'\b(flying|menace|unblockable|can\'t be blocked|fear|intimidate)\b', re.I),
    'card-advantage':    re.compile(r'\b(draw[s]? (a|two|three|\d+) card|scry|look at the top)\b', re.I),
    'ramp-fixing':       re.compile(r'(add \{[WUBRG]\}|search .* (basic|land))|(mana of any)', re.I),
    'self-mill':         re.compile(r'(mill)|(put .* card.* into .* graveyard)', re.I),
    'counter-magic':     re.compile(r'counter target (spell|ability)', re.I),
    'combat-trick':      re.compile(r'(target creature gets [\+\-]|until end of turn.*[\+\-])', re.I),
    'sweeper':           re.compile(r'(destroy all|deals? \d+ damage to each|each creature gets)', re.I),
}

SPEED_PATTERNS = {
    'aggro': re.compile(r'\b(haste|first strike|alliance|whenever .* creature enters)\b', re.I),
    'control': re.compile(r'\b(counter target|gain control|destroy all|flying|defender)\b', re.I),
}

# ── Build card_config ──────────────────────────────────────────────────────

# Bomb/signal card definitions with comments
BOMB_CARDS = {
    'The Last Ronin': 'Best card in the set. Wins the game if unanswered.',
    'Sally Pride, Lioness Leader': 'Insane value engine. Build around her with tokens/go-wide.',
    'Agent Bishop, Man in Black': 'Premium threat + removal. Fits any deck with white/black.',
    'Krang & Shredder': 'Two-card army. Game-ending bomb.',
    'North Wind Avatar': 'Evasive finisher with massive upside.',
}
BUILD_AROUND_CARDS = {
    'Brilliance Unleashed': 'SIGNAL: Go UR Artifacts. Every artifact ETB pumps your whole team.',
    'Leatherhead, Swamp Stalker': 'SIGNAL: Go BG Disappear. Grows huge from graveyard exile.',
    'Mikey & Don, Party Planners': 'SIGNAL: Go GU Mutagen. Grows your entire team with counters.',
    'Triceraton Commander': 'Enormous value. Worth splashing for.',
    "Leader's Talent": 'Premium enchantment. Wins games over time.',
    'Turncoat Kunoichi': 'SIGNAL: Go WB Sneak. Repeated disruption machine.',
    'Krang, Master Mind': 'Control finisher. Build a controlling deck around this.',
}
SIGNAL_CARDS = {
    'Metalhead': 'UR Artifacts payoff. Copies artifact creatures — insane value.',
    'Mighty Mutanimals': 'Goes in any green deck. Highest GIH win rate in the set.',
    "April O'Neil, Hacktivist": 'Premium card advantage. Any deck wants her.',
    'Raph & Mikey, Troublemakers': 'Strong gold uncommon for aggressive decks.',
    'Rat King, Verminister': 'BG value engine. Graveyard shenanigans.',
    'Groundchuck & Dirtbag': 'RW Alliance signpost. If this wheels, RW is wide open.',
    'Karai, Future of the Foot': 'WB Sneak signpost. Late = Sneak is open.',
    'Slash, Reptile Rampager': 'BG Disappear signpost. Grows massive from Disappear count.',
}
TOP_COMMON_CARDS = {
    'Courier of Comestibles': 'Best common. Food + Disappear synergy. Goes in any black/green deck.',
    'Frog Butler': 'Recursive value from graveyard. Great in BG and GU.',
    'Manhole Missile': '3 damage + artifact token. Premium red common.',
    'Dimensional Exile': 'Best white common. Oblivion Ring effect.',
    'Mechanized Ninja Cavalry': 'RW Alliance key common. Multiple triggers per turn.',
    'Stomped by the Foot': 'Cheap black removal. Always playable.',
    'Ravenous Robots': 'UR Artifacts key creature. Strong in any red deck.',
    'Does Machines': 'Artifact synergy common. Good in UR.',
}

# Removal lookup
REMOVAL_MAP = {r['name']: r['type'] for r in REMOVAL}

print("Building card_config...")
card_config = {}
for sname in scryfall:
    sf = get_sf_data(sname)
    l17 = get_17l(sname)
    tier = get_tier(sname)
    colors = sorted(get_card_colors(sname))
    land = is_land(sname)

    # Auto-detect sections
    sections = []
    if sname in BOMB_CARDS:
        sections.append('bombs')
    if sname in BUILD_AROUND_CARDS:
        sections.append('build_arounds')
    if sname in SIGNAL_CARDS:
        sections.append('signals')
    if sname in TOP_COMMON_CARDS:
        sections.append('top_commons')

    # Archetype membership
    arch_membership = {}
    for arch in ARCHETYPES:
        arch_colors = set(arch['colors'])
        if not card_fits_archetype(set(colors) if colors else set(), arch_colors, land):
            continue
        roles_in_arch = []
        if sname in arch['signposts']:
            roles_in_arch.append('signpost')
        if sname in arch.get('payoffs', []):
            roles_in_arch.append('payoff')
        if sname in arch.get('enablers', []):
            roles_in_arch.append('enabler')
        if sname in arch.get('removal', []):
            roles_in_arch.append('removal')
        if sname in arch.get('role_players', []):
            roles_in_arch.append('role_player')
        # Check key_synergies
        for syn in arch.get('key_synergies', []):
            if sname == syn[0]:
                roles_in_arch.append('key_synergy')
                break
        if roles_in_arch:
            arch_membership[arch['id']] = roles_in_arch
            sections.append(f"{arch['id']}_{roles_in_arch[0]}")

    # Auto-tag roles
    role_tags = []
    if sname in BOMB_CARDS:
        role_tags.append('bomb')
    if sname in BUILD_AROUND_CARDS:
        role_tags.append('build-around')
    # Check if it's a payoff or enabler in any archetype
    is_payoff = any('payoff' in v for v in arch_membership.values())
    is_enabler = any('enabler' in v for v in arch_membership.values())
    if is_payoff and 'bomb' not in role_tags and 'build-around' not in role_tags:
        role_tags.append('payoff')
    if is_enabler:
        role_tags.append('enabler')
    if sname in SIGNAL_CARDS or any('signpost' in v for v in arch_membership.values()):
        if 'bomb' not in role_tags and 'build-around' not in role_tags:
            role_tags.append('role-player')  # signposts are role-players at minimum
    if not role_tags:
        # Check tier for filler vs role-player
        if tier and TIER_RANK.get(tier, 99) <= TIER_RANK.get('C+', 99):
            role_tags.append('role-player')
        else:
            role_tags.append('filler')

    # Auto-tag types from oracle text
    type_tags = []
    oracle = sf.get('oracle_text', '') + ' ' + sf.get('type_line', '')
    for tag_name, pattern in TAG_PATTERNS.items():
        if pattern.search(oracle):
            type_tags.append(tag_name)
    # Removal type
    if sname in REMOVAL_MAP:
        rm_type = REMOVAL_MAP[sname]
        if rm_type not in type_tags:
            type_tags.append(f'{rm_type}-removal' if rm_type != 'bounce' else 'bounce')

    # Speed tags
    speed_tags = []
    for speed, pattern in SPEED_PATTERNS.items():
        if pattern.search(oracle):
            speed_tags.append(speed)
    if not speed_tags:
        speed_tags.append('midrange')

    # Comment — pre-populate from our curated data
    comment = ''
    if sname in BOMB_CARDS:
        comment = BOMB_CARDS[sname]
    elif sname in BUILD_AROUND_CARDS:
        comment = BUILD_AROUND_CARDS[sname]
    elif sname in SIGNAL_CARDS:
        comment = SIGNAL_CARDS[sname]
    elif sname in TOP_COMMON_CARDS:
        comment = TOP_COMMON_CARDS[sname]

    # Tier list color code
    tl_color = None
    for c in tierlist_data['tmt_cards']:
        if canonical_name(c['name']) == sname:
            tl_color = c['color']
            break

    card_config[sname] = {
        'tier': tier,
        'tier_color': tl_color,
        'gih_wr': round(l17['gih'], 4) if l17['gih'] is not None else None,
        'alsa': round(l17['alsa'], 2) if l17['alsa'] is not None else None,
        'diwr': round(get_diwr(sname), 4) if get_diwr(sname) is not None else None,
        'games': l17['games'],
        'rarity': sf.get('rarity', ''),
        'colors': colors,
        'mana_cost': sf.get('mana_cost', ''),
        'type_line': sf.get('type_line', ''),
        'cmc': sf.get('cmc', 0),
        'power': sf.get('power', ''),
        'toughness': sf.get('toughness', ''),
        'oracle_text': sf.get('oracle_text', ''),
        'img': get_img(sname, 'normal'),
        'sections': list(set(sections)),
        'archetypes': arch_membership,
        'tags': {
            'roles': role_tags,
            'types': type_tags,
            'speed': speed_tags,
        },
        'removal_type': REMOVAL_MAP.get(sname),
        'comment': comment,
        'user_modified': False,
    }

# Print stats
section_counts = {}
for c in card_config.values():
    for s in c['sections']:
        section_counts[s] = section_counts.get(s, 0) + 1
print(f"Cards in config: {len(card_config)}")
for s, cnt in sorted(section_counts.items()):
    print(f"  {s}: {cnt}")

# ── BUILD HTML ──────────────────────────────────────────────────────────────
archetypes_json = json.dumps(ARCHETYPES, ensure_ascii=False)

# Draft signals computation — add to card_config sections so they're editable
signal_pool = [c for c in lands17
    if c.get('ever_drawn_win_rate') is not None
    and c.get('avg_seen') is not None
    and (c.get('game_count') or 0) > 100
    and c.get('rarity') in ('common', 'uncommon')]

late_picks = sorted([c for c in signal_pool if c['ever_drawn_win_rate'] >= 0.55 and c['avg_seen'] >= 5.0],
                    key=lambda x: x['avg_seen'], reverse=True)[:12]
for c in late_picks:
    cname = canonical_name(c['name'])
    if cname in card_config and 'late_pick' not in card_config[cname]['sections']:
        card_config[cname]['sections'].append('late_pick')

contested = sorted([c for c in signal_pool if c['ever_drawn_win_rate'] >= 0.54 and c['avg_seen'] <= 4.5],
                   key=lambda x: x['avg_seen'])[:12]
for c in contested:
    cname = canonical_name(c['name'])
    if cname in card_config and 'contested' not in card_config[cname]['sections']:
        card_config[cname]['sections'].append('contested')

# Re-serialize config with the new sections
config_json = json.dumps(card_config, ensure_ascii=False)

# Grade color map for JS
grade_colors_json = json.dumps({
    'A+': '#ff4757', 'A': '#ee5a24', 'A-': '#f39c12',
    'B+': '#f1c40f', 'B': '#2ecc71', 'B-': '#1abc9c',
    'C+': '#3498db', 'C': '#95a5a6', 'C-': '#7f8c8d',
    'D+': '#636e72', 'D': '#4a4a4a', 'D-': '#3d3d3d', 'F': '#2d3436',
})

tier_rank_json = json.dumps(TIER_RANK)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>TMT Draft Guide v2</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#0d1117; color:#c9d1d9; font-family:system-ui,-apple-system,sans-serif; font-size:15px; line-height:1.5; }}
.page {{ width:100%; padding:6px 12px; }}

/* ── Header ── */
h1 {{ font-size:22px; text-align:center; color:#58a6ff; padding:8px 0 2px; }}
h1 small {{ font-size:12px; color:#8b949e; font-weight:normal; display:block; }}
h2 {{ font-size:18px; color:#f0883e; padding:8px 0 4px; border-bottom:1px solid #21262d; margin-bottom:6px; }}
h3 {{ font-size:15px; color:#79c0ff; margin:4px 0 3px; }}

/* ── Top Nav ── */
.top-nav {{ display:flex; gap:4px; justify-content:center; flex-wrap:wrap; padding:4px 0;
    position:sticky; top:0; background:#0d1117; z-index:100; border-bottom:1px solid #21262d; align-items:center; }}
.tab-btn {{ padding:5px 14px; font-size:13px; background:#161b22; color:#8b949e; border:1px solid #21262d;
    border-radius:4px; cursor:pointer; transition:all .15s; }}
.tab-btn:hover {{ background:#21262d; color:#c9d1d9; }}
.tab-btn.active {{ background:#1f6feb; color:#fff; border-color:#1f6feb; }}
.edit-toggle {{ padding:5px 10px; font-size:12px; background:#21262d; color:#f0883e; border:1px solid #f0883e;
    border-radius:4px; cursor:pointer; margin-left:8px; }}
.edit-toggle.active {{ background:#f0883e; color:#0d1117; }}
.nav-search {{ display:inline-flex; align-items:center; gap:3px; margin-left:8px; }}
.nav-search input {{ padding:4px 8px; font-size:12px; background:#161b22; color:#c9d1d9;
    border:1px solid #21262d; border-radius:4px; width:140px; }}
.nav-search button {{ padding:4px 8px; font-size:11px; background:#21262d; color:#58a6ff;
    border:1px solid #30363d; border-radius:4px; cursor:pointer; }}
.persistence-btns {{ display:flex; gap:3px; margin-left:8px; }}
.persistence-btns button {{ padding:3px 8px; font-size:11px; background:#161b22; color:#8b949e;
    border:1px solid #21262d; border-radius:3px; cursor:pointer; }}
.persistence-btns button:hover {{ background:#21262d; color:#c9d1d9; }}

/* ── Tabs ── */
.tab-content {{ display:none; }}
.tab-content.active {{ display:block; }}

/* ── Card Tiles ── */
.card-tile {{ display:inline-block; position:relative; width:130px; margin:2px; cursor:pointer;
    border-radius:6px; overflow:hidden; background:#161b22; border:1px solid #21262d;
    vertical-align:top; transition:transform .15s, box-shadow .15s; }}
.card-tile:hover {{ transform:scale(1.05); box-shadow:0 4px 16px rgba(0,0,0,.5); z-index:10; }}
.card-tile.editing {{ border:2px solid #f0883e; }}
.card-tile img {{ width:100%; display:block; border-radius:5px 5px 0 0; }}
.card-noimg {{ padding:6px; font-size:10px; min-height:60px; display:flex; align-items:center;
    justify-content:center; text-align:center; }}
.grade {{ position:absolute; top:2px; left:2px; font-size:11px; font-weight:bold; color:#fff;
    padding:2px 5px; border-radius:3px; z-index:2; text-shadow:0 1px 2px rgba(0,0,0,.9); }}
.card-stats {{ font-size:10px; padding:3px 4px; background:#0d1117; color:#8b949e;
    text-align:center; white-space:nowrap; }}
.card-comment {{ font-size:10px; padding:2px 4px; background:#0d1117; color:#f0883e;
    text-align:center; font-weight:bold; overflow:hidden; text-overflow:ellipsis;
    white-space:nowrap; max-height:18px; }}

/* Rarity colors */
.rar-c {{ color:#c9d1d9; }} .rar-u {{ color:#a8d8ea; }} .rar-r {{ color:#f5c842; }} .rar-m {{ color:#f5842c; }}

/* ── Draft Guide sections ── */
.section-header {{ display:flex; align-items:center; gap:8px; margin-bottom:4px; }}
.section-header h3 {{ margin:0; }}
.card-row {{ display:flex; flex-wrap:wrap; gap:2px; }}
.sub-label {{ font-size:12px; font-weight:600; margin:6px 0 2px 0; text-transform:uppercase; letter-spacing:0.5px; }}
.sub-label:first-child {{ margin-top:0; }}

/* Must-picks + Signals layout */
.two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px; }}
@media(max-width:900px) {{ .two-col {{ grid-template-columns:1fr; }} }}
.picks-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px; }}
@media(max-width:900px) {{ .picks-grid {{ grid-template-columns:1fr; }} }}
.col-box {{ background:#161b22; border:1px solid #21262d; border-radius:6px; padding:8px; }}

/* ── Archetypes ── */
.arch-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(350px,1fr)); gap:6px; margin-bottom:6px; }}
@media(max-width:700px) {{ .arch-grid {{ grid-template-columns:1fr; }} }}
.arch-box {{ background:#161b22; border:1px solid #21262d; border-radius:6px; padding:8px; }}
.arch-title {{ font-size:16px; font-weight:bold; margin-bottom:3px; }}
.arch-desc {{ font-size:13px; color:#8b949e; margin-bottom:4px; }}
.arch-strat {{ font-size:13px; color:#c9d1d9; margin-bottom:6px; }}
.arch-cat-label {{ font-size:12px; color:#f0883e; font-weight:bold; margin:4px 0 2px; }}
.synergy-row {{ display:flex; align-items:center; gap:4px; font-size:11px; color:#8b949e;
    padding:2px 0; border-top:1px solid #21262d; margin-top:2px; }}

/* ── Card Browser filters ── */
.filter-bar {{ display:flex; flex-wrap:wrap; gap:4px; padding:6px 0; align-items:center; }}
.filter-group {{ display:flex; gap:2px; align-items:center; }}
.filter-group label {{ font-size:11px; color:#8b949e; margin-right:4px; }}
.pill {{ padding:3px 8px; font-size:11px; background:#161b22; color:#8b949e; border:1px solid #21262d;
    border-radius:12px; cursor:pointer; transition:all .15s; user-select:none; }}
.pill:hover {{ background:#21262d; color:#c9d1d9; }}
.pill.active {{ background:#1f6feb; color:#fff; border-color:#1f6feb; }}
.view-pill {{ padding:4px 12px; font-size:12px; font-weight:600; background:#161b22; color:#8b949e; border:1px solid #30363d;
    border-radius:6px; cursor:pointer; transition:all .15s; user-select:none; }}
.view-pill:hover {{ background:#21262d; color:#c9d1d9; border-color:#484f58; }}
.view-pill.active {{ background:#f0883e; color:#000; border-color:#f0883e; }}
.sort-select {{ padding:3px 8px; font-size:11px; background:#161b22; color:#c9d1d9;
    border:1px solid #21262d; border-radius:4px; }}
.browser-grid {{ display:flex; flex-wrap:wrap; gap:2px; margin-top:6px; }}
.browser-count {{ font-size:12px; color:#8b949e; margin:4px 0; }}
.browser-table-wrap {{ overflow-x:auto; overflow-y:auto; max-height:calc(100vh - 180px); margin-top:6px; border:1px solid #21262d; border-radius:6px; }}
.browser-table {{ width:100%; border-collapse:separate; border-spacing:0; font-size:12px; }}
.browser-table th {{ position:sticky; top:0; z-index:2; background:#0d1117; text-align:left; padding:8px 8px;
    border-bottom:2px solid #30363d; color:#8b949e; font-weight:600; cursor:pointer; white-space:nowrap; font-size:11px; }}
.browser-table th:hover {{ color:#f0883e; }}
.browser-table td {{ padding:4px 8px; border-bottom:1px solid #21262d; color:#c9d1d9; vertical-align:middle; }}
.browser-table tr:hover td {{ background:#161b22; }}
.browser-table .tbl-img {{ width:32px; height:auto; border-radius:2px; vertical-align:middle; }}
.browser-table .tbl-name {{ font-weight:600; white-space:nowrap; cursor:pointer; }}
.browser-table .tbl-name:hover {{ color:#58a6ff; }}
.browser-table .tbl-grade {{ display:inline-block; padding:1px 5px; border-radius:3px; font-size:10px; font-weight:bold; }}
.browser-table .tbl-tag {{ display:inline-block; padding:1px 4px; border-radius:3px; font-size:10px;
    background:#21262d; color:#8b949e; margin:0 1px; }}

/* ── Edit Panel ── */
#edit-panel {{ position:fixed; top:0; right:-420px; width:400px; height:100vh; z-index:2000;
    background:#0d1117; border-left:2px solid #f0883e; box-shadow:-8px 0 32px rgba(0,0,0,.7);
    transition:right .3s ease; overflow-y:auto; }}
#edit-panel.open {{ right:0; }}
#edit-panel .ep-header {{ position:sticky; top:0; background:#161b22; padding:10px 12px;
    border-bottom:1px solid #21262d; display:flex; align-items:center; justify-content:space-between; z-index:1; }}
#edit-panel .ep-header h3 {{ font-size:14px; color:#f0883e; margin:0; }}
#edit-panel .ep-close {{ background:none; border:1px solid #30363d; color:#c9d1d9;
    padding:4px 10px; border-radius:4px; cursor:pointer; font-size:13px; }}
#edit-panel .ep-body {{ padding:10px 12px; }}
#edit-panel .ep-card-img {{ width:180px; display:block; margin:0 auto 8px; border-radius:8px; }}
#edit-panel .ep-section {{ margin-bottom:10px; }}
#edit-panel .ep-section-title {{ font-size:12px; color:#58a6ff; font-weight:bold; margin-bottom:4px;
    text-transform:uppercase; letter-spacing:.5px; }}
.tag-chips {{ display:flex; flex-wrap:wrap; gap:3px; }}
.tag-chip {{ padding:3px 8px; font-size:11px; border-radius:10px; cursor:pointer; transition:all .15s;
    user-select:none; border:1px solid #30363d; }}
.tag-chip.on {{ background:#1f6feb; color:#fff; border-color:#1f6feb; }}
.tag-chip.off {{ background:#161b22; color:#58595e; }}
.tag-chip:hover {{ opacity:.85; }}
.tag-chip.role {{ border-color:#f0883e; }}
.tag-chip.role.on {{ background:#f0883e; color:#0d1117; border-color:#f0883e; }}
.tag-chip.type {{ border-color:#3498db; }}
.tag-chip.type.on {{ background:#3498db; color:#fff; border-color:#3498db; }}
.tag-chip.speed {{ border-color:#2ecc71; }}
.tag-chip.speed.on {{ background:#2ecc71; color:#0d1117; border-color:#2ecc71; }}
.tag-chip.section {{ border-color:#9b59b6; }}
.tag-chip.section.on {{ background:#9b59b6; color:#fff; border-color:#9b59b6; }}
.tag-chip.arch {{ border-color:#e67e22; }}
.tag-chip.arch.on {{ background:#e67e22; color:#fff; border-color:#e67e22; }}
#edit-panel textarea {{ width:100%; min-height:60px; background:#161b22; color:#c9d1d9;
    border:1px solid #21262d; border-radius:4px; padding:6px; font-size:12px; resize:vertical;
    font-family:inherit; }}
#edit-panel .ep-save {{ display:block; width:100%; padding:8px; margin-top:8px; background:#1f6feb;
    color:#fff; border:none; border-radius:4px; cursor:pointer; font-size:13px; font-weight:bold; }}
#edit-panel .ep-save:hover {{ background:#388bfd; }}

/* ── Hover Preview ── */
#preview {{ display:none; position:fixed; z-index:3000; pointer-events:none;
    border-radius:10px; box-shadow:0 8px 32px rgba(0,0,0,.9); background:#161b22;
    border:1px solid #30363d; width:300px; max-height:90vh; overflow-y:auto; }}
#preview img {{ width:100%; display:block; border-radius:10px 10px 0 0; }}
#preview .hover-info {{ padding:6px 8px; font-size:11px; line-height:1.3; }}
#preview .hover-name {{ font-size:13px; font-weight:bold; color:#58a6ff; margin-bottom:2px; }}
#preview .hover-type {{ color:#8b949e; margin-bottom:3px; font-size:11px; }}
#preview .hover-stats {{ display:grid; grid-template-columns:1fr 1fr; gap:1px 6px; font-size:10px; }}
#preview .hover-stats .hs-label {{ color:#8b949e; }}
#preview .hover-stats .hs-val {{ color:#f0883e; font-weight:bold; }}
#preview .hover-tags {{ margin-top:3px; display:flex; flex-wrap:wrap; gap:2px; }}
#preview .hover-tags span {{ font-size:9px; padding:1px 5px; border-radius:6px;
    background:#21262d; color:#79c0ff; border:1px solid #30363d; }}

/* ── Mobile Detail ── */
#mobile-detail {{ display:none; position:fixed; top:0; left:0; right:0; bottom:0;
    z-index:4000; background:#0d1117; overflow-y:auto; -webkit-overflow-scrolling:touch; }}
#mobile-detail.active {{ display:block; }}
#mobile-detail .md-close {{ position:fixed; top:10px; right:10px; z-index:4001;
    background:#21262d; color:#c9d1d9; border:1px solid #30363d; border-radius:50%;
    width:36px; height:36px; font-size:18px; cursor:pointer; line-height:34px; text-align:center; }}
#mobile-detail .md-header {{ display:flex; gap:10px; padding:12px; padding-top:50px; }}
#mobile-detail .md-header img {{ width:140px; border-radius:8px; flex-shrink:0; }}
#mobile-detail .md-info {{ flex:1; }}
#mobile-detail .md-name {{ font-size:16px; font-weight:bold; color:#58a6ff; margin-bottom:4px; }}
#mobile-detail .md-type {{ font-size:12px; color:#8b949e; margin-bottom:4px; }}
#mobile-detail .md-stats {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:3px; font-size:12px; }}
#mobile-detail .md-stats .ms-label {{ color:#8b949e; font-size:10px; }}
#mobile-detail .md-stats .ms-val {{ color:#f0883e; font-weight:bold; }}
#mobile-detail .md-tags {{ display:flex; flex-wrap:wrap; gap:3px; padding:8px 12px; }}
#mobile-detail .md-tags span {{ font-size:11px; padding:2px 8px; border-radius:10px;
    background:#21262d; color:#79c0ff; border:1px solid #30363d; }}
#mobile-detail .md-comment {{ padding:6px 12px; font-size:12px; color:#f0883e;
    background:#161b22; margin:4px 12px; border-radius:4px; font-style:italic; }}

/* Info boxes */
.info-box {{ background:#161b22; border:1px solid #21262d; border-radius:6px; padding:8px 10px; margin:3px 0; font-size:13px; line-height:1.5; position:relative; }}
.info-box .info-title {{ color:#f0883e; font-weight:bold; font-size:14px; margin-bottom:3px; }}
.info-columns {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:6px; }}
.info-box.editable {{ cursor:pointer; border-color:#30363d; }}
.info-box.editable:hover {{ border-color:#f0883e; }}
.info-box .tip-edit-icon {{ position:absolute; top:6px; right:8px; font-size:11px; color:#484f58; display:none; }}
.info-box.editable .tip-edit-icon {{ display:inline; }}
.info-box.editable:hover .tip-edit-icon {{ color:#f0883e; }}
.tip-edit-input {{ width:100%; background:#0d1117; border:1px solid #30363d; border-radius:4px; color:#c9d1d9; padding:4px 6px; font-family:inherit; font-size:13px; margin-bottom:4px; }}
.tip-edit-input.title-input {{ font-size:14px; font-weight:bold; color:#f0883e; }}
.tip-edit-textarea {{ width:100%; min-height:80px; background:#0d1117; border:1px solid #30363d; border-radius:4px; color:#c9d1d9; padding:6px; font-family:inherit; font-size:13px; resize:vertical; }}
.tip-edit-actions {{ display:flex; gap:4px; margin-top:4px; justify-content:flex-end; }}
.tip-edit-actions button {{ padding:3px 10px; border:none; border-radius:4px; font-size:11px; cursor:pointer; }}
.tip-edit-actions .tip-save {{ background:#238636; color:#fff; }}
.tip-edit-actions .tip-save:hover {{ background:#2ea043; }}
.tip-edit-actions .tip-cancel {{ background:#21262d; color:#c9d1d9; }}
.tip-edit-actions .tip-cancel:hover {{ background:#30363d; }}
.tip-add-btn {{ background:transparent; border:2px dashed #30363d; border-radius:6px; padding:12px; color:#484f58; font-size:13px; cursor:pointer; display:none; text-align:center; }}
.tip-add-btn:hover {{ border-color:#f0883e; color:#f0883e; }}
.tip-del-btn {{ position:absolute; top:4px; right:24px; font-size:12px; color:#484f58; cursor:pointer; display:none; background:none; border:none; padding:2px; }}
.info-box.editable .tip-del-btn {{ display:inline; }}
.info-box.editable .tip-del-btn:hover {{ color:#e74c3c; }}

/* Stats bar */
.stats-bar {{ display:flex; gap:6px; justify-content:center; padding:4px; font-size:12px; color:#8b949e; flex-wrap:wrap; }}
.stats-bar span {{ background:#161b22; padding:2px 6px; border-radius:3px; border:1px solid #21262d; }}
.stats-bar .highlight {{ color:#f0883e; }}

/* ── Mobile Responsive ── */
@media(max-width:600px) {{
    .page {{ padding:4px 6px; }}
    h1 {{ font-size:16px; }} h2 {{ font-size:15px; }} h3 {{ font-size:13px; }}
    .top-nav {{ gap:2px; padding:3px 0; }}
    .tab-btn {{ font-size:11px; padding:3px 8px; }}
    .nav-search input {{ width:90px !important; font-size:10px !important; }}
    .card-tile {{ width:90px !important; margin:1px !important; }}
    .card-stats {{ font-size:9px !important; padding:2px 3px !important; }}
    .grade {{ font-size:9px !important; padding:1px 3px !important; }}
    .arch-grid {{ grid-template-columns:1fr !important; }}
    .two-col {{ grid-template-columns:1fr !important; }}
    .picks-grid {{ grid-template-columns:1fr !important; }}
    .info-columns {{ grid-template-columns:1fr !important; }}
    .persistence-btns {{ display:none; }}
    #edit-panel {{ width:100vw !important; right:-100vw !important; }}
    #edit-panel.open {{ right:0 !important; }}
    #preview {{ display:none !important; }}
}}
</style>
</head>
<body>
<div class="page">
<h1>TMT Draft Guide
<small>17Lands Win Rates · Editable Card Positions</small></h1>

<div class="top-nav">
    <button class="tab-btn active" onclick="switchTab('guide')">Draft Guide</button>
    <button class="tab-btn" onclick="switchTab('browser')">Card Browser</button>
    <button class="edit-toggle" id="edit-mode-btn" onclick="toggleEditMode()">Edit Mode</button>
    <div class="nav-search">
        <input type="text" id="card-search" placeholder="Search card...">
        <button onclick="searchNext()">Next</button>
        <span id="search-count" style="font-size:10px;color:#8b949e;min-width:30px;"></span>
    </div>
    <div class="persistence-btns">
        <button onclick="exportConfig()">Export</button>
        <button onclick="document.getElementById('import-file').click()">Import</button>
        <button onclick="resetConfig()">Reset</button>
        <input type="file" id="import-file" accept=".json" style="display:none" onchange="importConfig(event)">
    </div>
</div>

<!-- ═══ DRAFT GUIDE TAB ═══ -->
<div class="tab-content active" id="tab-guide">

<div class="stats-bar">
    <span>Cards: <b>{len(scryfall)}</b></span>
    <span>17L tracked: <b>{len([c for c in lands17 if (c.get("game_count") or 0) > 50])}</b></span>
</div>

<!-- Tips (rendered by JS for editability) -->
<div id="tips"><h2>Draft Tips</h2>
<div class="info-columns" id="tips-container"></div>
</div>

<!-- Must-Picks + Signals -->
<h2>Must-Pick Cards &amp; Draft Signals</h2>
<div class="picks-grid">
    <div class="col-box" style="border-top:3px solid #ff4757;">
        <h3 style="color:#ff4757;">Bombs &amp; Build-Arounds</h3>
        <p style="font-size:12px;color:#8b949e;margin-bottom:4px;">Take these over everything. Format-defining rares and mythics.</p>
        <div id="must-pick-cards"></div>
    </div>
    <div class="col-box" style="border-top:3px solid #2ecc71;">
        <h3 style="color:#2ecc71;">Archetype Signals</h3>
        <p style="font-size:12px;color:#8b949e;margin-bottom:4px;">Premium uncommons that pull you into an archetype. Seeing these late = the archetype is open.</p>
        <div id="signal-cards" class="card-row"></div>
    </div>
    <div class="col-box" style="border-top:3px solid #3498db;">
        <h3 style="color:#3498db;">Underdrafted — Free Wins</h3>
        <p style="font-size:12px;color:#8b949e;margin-bottom:4px;">High GIH win rate but going late. Seeing these in pack 1 means the color is open.</p>
        <div id="late-pick-cards" class="card-row"></div>
    </div>
    <div class="col-box" style="border-top:3px solid #e74c3c;">
        <h3 style="color:#e74c3c;">Overdrafted — Don't Force</h3>
        <p style="font-size:12px;color:#8b949e;margin-bottom:4px;">Everyone wants these — high GIH but low ALSA. Don't force a color just because you got one.</p>
        <div id="contested-cards" class="card-row"></div>
    </div>
    <div class="col-box" style="border-top:3px solid #f39c12; grid-column: 1 / -1;">
        <h3 style="color:#f39c12;">Top Commons</h3>
        <p style="font-size:12px;color:#8b949e;margin-bottom:4px;">The backbone of every deck. Best commons by GIH win rate.</p>
        <div id="top-commons-cards" class="card-row"></div>
    </div>
</div>

<!-- Archetypes -->
<h2>Archetypes</h2>
<div id="archetypes-container" class="arch-grid"></div>

<!-- Removal -->
<h2>Key Removal</h2>
<div id="removal-container" class="card-row"></div>

</div>

<!-- ═══ CARD BROWSER TAB ═══ -->
<div class="tab-content" id="tab-browser">
<h2>Card Browser — All Cards</h2>

<div class="filter-bar">
    <div class="filter-group">
        <label>Color:</label>
        <span class="pill active" data-filter="color" data-val="all">All</span>
        <span class="pill" data-filter="color" data-val="W">W</span>
        <span class="pill" data-filter="color" data-val="U">U</span>
        <span class="pill" data-filter="color" data-val="B">B</span>
        <span class="pill" data-filter="color" data-val="R">R</span>
        <span class="pill" data-filter="color" data-val="G">G</span>
        <span class="pill" data-filter="color" data-val="M">Multi</span>
        <span class="pill" data-filter="color" data-val="C">C/L</span>
    </div>
    <div class="filter-group">
        <label>Rarity:</label>
        <span class="pill" data-filter="rarity" data-val="mythic">M</span>
        <span class="pill" data-filter="rarity" data-val="rare">R</span>
        <span class="pill" data-filter="rarity" data-val="uncommon">U</span>
        <span class="pill" data-filter="rarity" data-val="common">C</span>
    </div>
    <div class="filter-group">
        <label>Role:</label>
        <span class="pill" data-filter="role" data-val="bomb">Bomb</span>
        <span class="pill" data-filter="role" data-val="build-around">Build-around</span>
        <span class="pill" data-filter="role" data-val="payoff">Payoff</span>
        <span class="pill" data-filter="role" data-val="enabler">Enabler</span>
        <span class="pill" data-filter="role" data-val="role-player">Role Player</span>
    </div>
    <div class="filter-group">
        <label>Type:</label>
        <span class="pill" data-filter="type" data-val="unconditional-removal">Removal</span>
        <span class="pill" data-filter="type" data-val="evasion">Evasion</span>
        <span class="pill" data-filter="type" data-val="card-advantage">Card Adv</span>
        <span class="pill" data-filter="type" data-val="token-maker">Tokens</span>
    </div>
    <div class="filter-group">
        <label>Sort:</label>
        <select class="sort-select" id="browser-sort" onchange="renderBrowser()">
            <option value="tier">Tier Grade</option>
            <option value="gih">GIH WR</option>
            <option value="alsa">ALSA</option>
            <option value="name">Name</option>
            <option value="cmc">CMC</option>
        </select>
    </div>
    <div class="filter-group">
        <label>View:</label>
        <span class="view-pill active" data-view="grid" onclick="setView('grid')">&#9638; Grid</span>
        <span class="view-pill" data-view="table" onclick="setView('table')">&#9776; Table</span>
    </div>
</div>
<div class="browser-count" id="browser-count"></div>
<div class="browser-grid" id="browser-grid"></div>
<div class="browser-table-wrap" id="browser-table-wrap" style="display:none;"><table class="browser-table" id="browser-table"></table></div>
</div>

<!-- ═══ EDIT PANEL ═══ -->
<div id="edit-panel">
    <div class="ep-header">
        <h3 id="ep-title">Edit Card</h3>
        <button class="ep-close" onclick="closeEditPanel()">✕</button>
    </div>
    <div class="ep-body" id="ep-body"></div>
</div>

<!-- ═══ HOVER PREVIEW ═══ -->
<div id="preview">
    <img src="" alt="preview">
    <div class="hover-info">
        <div class="hover-name"></div>
        <div class="hover-type"></div>
        <div class="hover-stats"></div>
        <div class="hover-tags"></div>
    </div>
</div>

<!-- ═══ MOBILE DETAIL ═══ -->
<div id="mobile-detail">
    <button class="md-close" onclick="closeMobileDetail()">✕</button>
    <div id="md-content"></div>
</div>

</div>

<script>
/* ═══════════════════════════════════════════════════════════════════════════
   TMT Draft Guide v2 — Client-side rendering from card_config
   ═══════════════════════════════════════════════════════════════════════════ */

// ── Embedded data ──
const DEFAULT_CONFIG = {config_json};
const ARCHETYPES = {archetypes_json};
const GRADE_COLORS = {grade_colors_json};
const TIER_RANK = {tier_rank_json};

// ── State ──
let DB = null;  // active card config
let editMode = false;
let editingCard = null;
const isMobile = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

// ── Tips Data ──
const DEFAULT_TIPS = [
    {{ title: 'Mana Curve', body: '1-drops: 1-2 · 2-drops: 4-5 · 3-drops: 4-5 · 4-drops: 3-4 · 5+: 2-3\\nTotal: 16-17 creatures, 6-8 spells, 16-17 lands' }},
    {{ title: 'Key Mechanics', body: '<b>Artifacts</b> — count for both artifact + creature synergies\\n<b>Disappear</b> — exile from graveyard for effects (self-mill fills yard)\\n<b>Sneak</b> — bonus on combat damage (needs evasion/removal)\\n<b>Alliance</b> — triggers on creature ETB (tokens = multiple triggers)\\n<b>Mutagen</b> — +1/+1 counters matter; creatures grow over time' }},
    {{ title: 'Format Speed', body: 'Medium speed. RW Alliance and UR Artifacts close by turn 6-7.\\nBG Disappear grinds longest. Don\\'t be too greedy with your curve.' }},
    {{ title: 'Draft Priorities', body: '<b>P1P1:</b> Bombs > Premium removal > Best uncommon signpost\\n<b>Pack 1:</b> Stay open, grab the best card regardless of color\\n<b>Pack 2:</b> Commit to an archetype, prioritize synergy pieces\\n<b>Pack 3:</b> Fill curve gaps, grab fixing, snag last removal' }}
];
let TIPS = null;

// ── Persistence ──
const STORAGE_KEY = 'tmt_draft_config_v2';
const TIPS_STORAGE_KEY = 'tmt_tips_v1';

function loadConfig() {{
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {{
        try {{
            DB = JSON.parse(saved);
            console.log('Loaded card config from localStorage');
        }} catch(e) {{ console.warn('Bad localStorage, using defaults'); DB = JSON.parse(JSON.stringify(DEFAULT_CONFIG)); }}
    }} else {{
        DB = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
    }}
    const savedTips = localStorage.getItem(TIPS_STORAGE_KEY);
    if (savedTips) {{
        try {{
            TIPS = JSON.parse(savedTips);
            console.log('Loaded tips from localStorage');
        }} catch(e) {{ TIPS = JSON.parse(JSON.stringify(DEFAULT_TIPS)); }}
    }} else {{
        TIPS = JSON.parse(JSON.stringify(DEFAULT_TIPS));
    }}
}}

function saveConfig() {{
    localStorage.setItem(STORAGE_KEY, JSON.stringify(DB));
}}

function saveTips() {{
    localStorage.setItem(TIPS_STORAGE_KEY, JSON.stringify(TIPS));
}}

function exportConfig() {{
    const exportData = {{ cards: DB, tips: TIPS }};
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {{type: 'application/json'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'tmt_draft_config.json';
    a.click();
}}

function importConfig(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {{
        try {{
            const data = JSON.parse(reader.result);
            // Support both old format (flat card object) and new format ({{cards, tips}})
            if (data.cards && typeof data.cards === 'object') {{
                DB = data.cards;
                if (data.tips && Array.isArray(data.tips)) TIPS = data.tips;
            }} else {{
                DB = data; // old format — just cards
            }}
            saveConfig();
            saveTips();
            renderAll();
            alert('Config imported successfully!');
        }} catch(err) {{
            alert('Invalid JSON file');
        }}
    }};
    reader.readAsText(file);
    e.target.value = '';
}}

function resetConfig() {{
    if (!confirm('Reset all edits to defaults? (Cards + Tips)')) return;
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(TIPS_STORAGE_KEY);
    DB = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
    TIPS = JSON.parse(JSON.stringify(DEFAULT_TIPS));
    renderAll();
}}

// ── Tab switching ──
function switchTab(tab) {{
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + tab).classList.add('active');
    event.target.classList.add('active');
    if (tab === 'browser') renderBrowser();
}}

// ── Edit mode ──
function toggleEditMode() {{
    editMode = !editMode;
    const btn = document.getElementById('edit-mode-btn');
    btn.classList.toggle('active', editMode);
    btn.textContent = editMode ? 'Edit Mode ON' : 'Edit Mode';
    if (!editMode) {{ closeEditPanel(); editingTipIdx = null; }}
    renderTips();
}}

// ── Card tile HTML ──
function cardTile(name) {{
    const c = DB[name];
    if (!c || !c.img) return '';
    const gc = GRADE_COLORS[c.tier] || '#95a5a6';
    const gih = c.gih_wr != null ? (c.gih_wr * 100).toFixed(0) + '%' : '—';
    const alsa = c.alsa != null ? c.alsa.toFixed(1) : '—';
    const gradeBadge = c.tier ? `<span class="grade" style="background:${{gc}}">${{c.tier}}</span>` : '';
    const commentHtml = c.comment ? `<div class="card-comment" title="${{esc(c.comment)}}">${{esc(c.comment)}}</div>` : '';
    return `<div class="card-tile" data-name="${{esc(name)}}">
        ${{gradeBadge}}
        <img src="${{c.img}}" alt="${{esc(name)}}" loading="lazy">
        ${{commentHtml}}
        <div class="card-stats">GIH:${{gih}} ALSA:${{alsa}}</div>
    </div>`;
}}

function esc(s) {{ return s.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}

// ── Render Draft Guide ──
function renderGuide() {{
    // Bombs & Build-arounds — separated with labels
    const bombs = Object.entries(DB)
        .filter(([n,c]) => c.sections.includes('bombs'))
        .sort((a,b) => (TIER_RANK[a[1].tier]??99) - (TIER_RANK[b[1].tier]??99));
    const buildArounds = Object.entries(DB)
        .filter(([n,c]) => c.sections.includes('build_arounds') && !c.sections.includes('bombs'))
        .sort((a,b) => (TIER_RANK[a[1].tier]??99) - (TIER_RANK[b[1].tier]??99));
    let mustPickHtml = '';
    if (bombs.length) {{
        mustPickHtml += `<div class="sub-label" style="color:#ff4757;">Bombs</div><div class="card-row">${{bombs.map(([n]) => cardTile(n)).join('')}}</div>`;
    }}
    if (buildArounds.length) {{
        mustPickHtml += `<div class="sub-label" style="color:#f39c12;">Build-Arounds</div><div class="card-row">${{buildArounds.map(([n]) => cardTile(n)).join('')}}</div>`;
    }}
    document.getElementById('must-pick-cards').innerHTML = mustPickHtml;

    // Archetype signals
    const signals = Object.entries(DB)
        .filter(([n,c]) => c.sections.includes('signals'))
        .sort((a,b) => (TIER_RANK[a[1].tier]??99) - (TIER_RANK[b[1].tier]??99));
    document.getElementById('signal-cards').innerHTML = signals.map(([n]) => cardTile(n)).join('');

    // Underdrafted (late picks) — from sections
    const latePicks = Object.entries(DB)
        .filter(([n,c]) => c.sections.includes('late_pick'))
        .sort((a,b) => (b[1].alsa??0) - (a[1].alsa??0));
    document.getElementById('late-pick-cards').innerHTML = latePicks.map(([n]) => cardTile(n)).join('');

    // Overdrafted (contested) — from sections
    const contested = Object.entries(DB)
        .filter(([n,c]) => c.sections.includes('contested'))
        .sort((a,b) => (a[1].alsa??99) - (b[1].alsa??99));
    document.getElementById('contested-cards').innerHTML = contested.map(([n]) => cardTile(n)).join('');

    // Top commons
    const topCommons = Object.entries(DB)
        .filter(([n,c]) => c.sections.includes('top_commons'))
        .sort((a,b) => (b[1].gih_wr??0) - (a[1].gih_wr??0));
    document.getElementById('top-commons-cards').innerHTML = topCommons.map(([n]) => cardTile(n)).join('');

    // Archetypes
    renderArchetypes();

    // Removal
    const removalCards = Object.entries(DB)
        .filter(([n,c]) => c.removal_type != null)
        .sort((a,b) => {{
            const colorOrder = 'WUBRG';
            const ca = (a[1].colors[0] || 'Z'), cb = (b[1].colors[0] || 'Z');
            return colorOrder.indexOf(ca) - colorOrder.indexOf(cb);
        }});
    document.getElementById('removal-container').innerHTML = removalCards.map(([n]) => cardTile(n)).join('');
}}

function renderArchetypes() {{
    const container = document.getElementById('archetypes-container');
    let html = '';
    for (const arch of ARCHETYPES) {{
        const colorIcons = {{'W':'⚪','U':'🔵','B':'⚫','R':'🔴','G':'🟢'}};
        const ci = arch.colors.map(c => colorIcons[c]||'').join('');

        html += `<div class="arch-box" style="border-top:3px solid ${{arch.color_hex}}">`;
        html += `<div class="arch-title">${{arch.icon}} ${{arch.name}} ${{ci}}</div>`;
        html += `<div class="arch-desc">${{arch.short}}</div>`;
        html += `<div class="arch-strat">${{arch.strategy}}</div>`;

        // Render each category
        const categories = [
            ['signpost', 'Signposts', 'signposts'],
            ['payoff', 'Payoffs', 'payoffs'],
            ['enabler', 'Enablers', 'enablers'],
            ['removal', 'Removal', 'removal'],
            ['role_player', 'Role Players', 'role_players'],
        ];
        for (const [catId, catLabel, catKey] of categories) {{
            // Get cards from config that have this archetype+category
            const catCards = Object.entries(DB)
                .filter(([n,c]) => c.archetypes[arch.id] && c.archetypes[arch.id].includes(catId))
                .sort((a,b) => (TIER_RANK[a[1].tier]??99) - (TIER_RANK[b[1].tier]??99));
            if (catCards.length === 0) continue;
            html += `<div class="arch-cat-label">${{catLabel}} (${{catCards.length}})</div>`;
            html += `<div class="card-row">${{catCards.map(([n]) => cardTile(n)).join('')}}</div>`;
        }}

        // Key Synergies
        if (arch.key_synergies && arch.key_synergies.length) {{
            html += '<div class="arch-cat-label">Key Synergies</div>';
            for (const [card, partner, desc] of arch.key_synergies) {{
                html += `<div class="synergy-row">`;
                html += cardTile(card);
                html += `<span style="font-size:11px;color:#8b949e;padding:0 4px;">+ ${{esc(partner)}}: <em>${{esc(desc)}}</em></span>`;
                html += '</div>';
            }}
        }}
        html += '</div>';
    }}
    container.innerHTML = html;
}}

// ── View Toggle ──
let currentView = 'grid';
let tableSortCol = null;
let tableSortAsc = true;

function setView(mode) {{
    currentView = mode;
    document.querySelectorAll('[data-view]').forEach(p => p.classList.toggle('active', p.dataset.view === mode));
    document.getElementById('browser-grid').style.display = mode === 'grid' ? '' : 'none';
    document.getElementById('browser-table-wrap').style.display = mode === 'table' ? '' : 'none';
    renderBrowser();
}}

function sortTable(col) {{
    if (tableSortCol === col) {{ tableSortAsc = !tableSortAsc; }}
    else {{ tableSortCol = col; tableSortAsc = true; }}
    renderBrowser();
}}

// ── Render Card Browser ──
function renderBrowser() {{
    const grid = document.getElementById('browser-grid');
    const tableEl = document.getElementById('browser-table');
    const countEl = document.getElementById('browser-count');

    // Get active filters
    const activeFilters = {{}};
    document.querySelectorAll('#tab-browser .pill.active').forEach(p => {{
        const f = p.dataset.filter;
        const v = p.dataset.val;
        if (f === undefined || v === undefined) return;
        if (v === 'all') return;
        if (!activeFilters[f]) activeFilters[f] = [];
        activeFilters[f].push(v);
    }});

    const sortBy = document.getElementById('browser-sort').value;

    // Filter cards
    let cards = Object.entries(DB).filter(([name, c]) => {{
        // Color filter — multi-aware
        if (activeFilters.color) {{
            const fc = activeFilters.color;
            const wantMulti = fc.includes('M');
            const wantColorless = fc.includes('C');
            const wantColors = fc.filter(f => f !== 'M' && f !== 'C');
            const isMulti = c.colors.length >= 2;
            const isColorless = c.colors.length === 0 || c.type_line.includes('Land');
            let match = false;

            if (isColorless) {{
                // Colorless/lands match only if C is selected
                match = wantColorless;
            }} else if (isMulti) {{
                if (wantMulti && wantColors.length > 0) {{
                    // Multi + colors selected: multi card must contain at least one selected color
                    match = wantColors.some(f => c.colors.includes(f));
                }} else if (wantMulti) {{
                    // Multi alone: show all multi cards
                    match = true;
                }} else {{
                    // No multi selected: multi cards don't match single-color filters
                    match = false;
                }}
            }} else {{
                // Mono-colored card: matches if its color is selected
                match = wantColors.includes(c.colors[0]);
                // Also match if Multi is selected with this color (already handled above for multi cards)
            }}
            if (!match) return false;
        }}
        // Rarity filter
        if (activeFilters.rarity && !activeFilters.rarity.includes(c.rarity)) return false;
        // Role filter
        if (activeFilters.role && !activeFilters.role.some(r => c.tags.roles.includes(r))) return false;
        // Type filter
        if (activeFilters.type) {{
            const hasType = activeFilters.type.some(t => {{
                if (t === 'unconditional-removal') return c.removal_type != null;
                return c.tags.types.includes(t);
            }});
            if (!hasType) return false;
        }}
        return true;
    }});

    // Sort
    cards.sort((a, b) => {{
        const [an, ac] = a, [bn, bc] = b;
        if (sortBy === 'tier') return (TIER_RANK[ac.tier]??99) - (TIER_RANK[bc.tier]??99);
        if (sortBy === 'gih') return (bc.gih_wr??0) - (ac.gih_wr??0);
        if (sortBy === 'alsa') return (ac.alsa??99) - (bc.alsa??99);
        if (sortBy === 'name') return an.localeCompare(bn);
        if (sortBy === 'cmc') return (ac.cmc??0) - (bc.cmc??0);
        return 0;
    }});

    countEl.textContent = `Showing ${{cards.length}} of ${{Object.keys(DB).length}} cards`;

    if (currentView === 'grid') {{
        grid.innerHTML = cards.map(([n]) => cardTile(n)).join('');
    }}

    if (currentView === 'table') {{
        // Apply table-specific sort if user clicked a column header
        if (tableSortCol) {{
            cards.sort((a, b) => {{
                const [an, ac] = a, [bn, bc] = b;
                let va, vb;
                switch (tableSortCol) {{
                    case 'name': va = an; vb = bn; return tableSortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
                    case 'tier': va = TIER_RANK[ac.tier]??99; vb = TIER_RANK[bc.tier]??99; break;
                    case 'gih': va = ac.gih_wr??0; vb = bc.gih_wr??0; break;
                    case 'alsa': va = ac.alsa??99; vb = bc.alsa??99; break;
                    case 'diwr': va = ac.diwr??0; vb = bc.diwr??0; break;
                    case 'games': va = ac.games??0; vb = bc.games??0; break;
                    case 'cmc': va = ac.cmc??0; vb = bc.cmc??0; break;
                    case 'rarity': {{ const ro = {{mythic:0,rare:1,uncommon:2,common:3}}; va = ro[ac.rarity]??4; vb = ro[bc.rarity]??4; break; }}
                    default: return 0;
                }}
                return tableSortAsc ? va - vb : vb - va;
            }});
        }}

        const arrow = (col) => tableSortCol === col ? (tableSortAsc ? ' ▲' : ' ▼') : '';
        let thtml = '<thead><tr>';
        thtml += `<th onclick="sortTable('name')" style="min-width:140px;">Card${{arrow('name')}}</th>`;
        thtml += `<th onclick="sortTable('tier')">Tier${{arrow('tier')}}</th>`;
        thtml += `<th onclick="sortTable('gih')">GIH WR${{arrow('gih')}}</th>`;
        thtml += `<th onclick="sortTable('alsa')">ALSA${{arrow('alsa')}}</th>`;
        thtml += `<th onclick="sortTable('diwr')">DIWR${{arrow('diwr')}}</th>`;
        thtml += `<th onclick="sortTable('games')">Games${{arrow('games')}}</th>`;
        thtml += `<th onclick="sortTable('rarity')">Rarity${{arrow('rarity')}}</th>`;
        thtml += `<th onclick="sortTable('cmc')">CMC${{arrow('cmc')}}</th>`;
        thtml += '<th>Colors</th>';
        thtml += '<th>Mana</th>';
        thtml += '<th>Type</th>';
        thtml += '<th>Roles</th>';
        thtml += '<th>Tags</th>';
        thtml += '<th>Speed</th>';
        thtml += '<th>Sections</th>';
        thtml += '</tr></thead><tbody>';

        for (const [name, c] of cards) {{
            const gih = c.gih_wr != null ? (c.gih_wr * 100).toFixed(1) + '%' : '—';
            const alsa = c.alsa != null ? c.alsa.toFixed(1) : '—';
            const diwr = c.diwr != null ? (c.diwr > 0 ? '+' : '') + (c.diwr * 100).toFixed(1) + '%' : '—';
            const games = c.games != null ? c.games.toLocaleString() : '—';
            const gradeColor = GRADE_COLORS[c.tier] || '#555';
            const rarChar = {{mythic:'M',rare:'R',uncommon:'U',common:'C'}}[c.rarity] || '?';
            const rarColor = {{mythic:'#f0883e',rare:'#f1e05a',uncommon:'#7ee8fa',common:'#8b949e'}}[c.rarity] || '#999';
            const colorPips = c.colors.length ? c.colors.join('') : (c.type_line.includes('Land') ? 'Land' : 'C');
            const roles = (c.tags.roles || []).map(r => `<span class="tbl-tag">${{esc(r)}}</span>`).join('');
            const types = (c.tags.types || []).map(t => `<span class="tbl-tag">${{esc(t)}}</span>`).join('');
            const speeds = (c.tags.speed || []).map(s => `<span class="tbl-tag">${{esc(s)}}</span>`).join('');
            const sections = (c.sections || []).map(s => `<span class="tbl-tag" style="background:#1a3a2a;color:#2ecc71;">${{esc(s)}}</span>`).join('');
            const clickAttr = editMode ? `onclick="openEditPanel('${{esc(name)}}')" style="cursor:pointer;"` : '';

            thtml += `<tr ${{clickAttr}}>`;
            thtml += `<td><span class="tbl-name" ${{clickAttr}}>${{esc(name)}}</span></td>`;
            thtml += `<td><span class="tbl-grade" style="background:${{gradeColor}};color:#000;">${{c.tier || '—'}}</span></td>`;
            thtml += `<td style="color:#f0883e;font-weight:600;">${{gih}}</td>`;
            thtml += `<td>${{alsa}}</td>`;
            thtml += `<td style="color:${{(c.diwr??0) > 0 ? '#2ecc71' : (c.diwr??0) < 0 ? '#e74c3c' : '#8b949e'}};">${{diwr}}</td>`;
            thtml += `<td style="color:#8b949e;">${{games}}</td>`;
            thtml += `<td><span style="color:${{rarColor}};font-weight:600;">${{rarChar}}</span></td>`;
            thtml += `<td>${{c.cmc ?? '—'}}</td>`;
            thtml += `<td style="font-weight:600;">${{colorPips}}</td>`;
            thtml += `<td style="font-size:11px;color:#8b949e;">${{esc(c.mana_cost || '')}}</td>`;
            thtml += `<td style="font-size:11px;color:#8b949e;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${{esc(c.type_line || '')}}</td>`;
            thtml += `<td>${{roles}}</td>`;
            thtml += `<td>${{types}}</td>`;
            thtml += `<td>${{speeds}}</td>`;
            thtml += `<td>${{sections}}</td>`;
            thtml += '</tr>';
        }}
        thtml += '</tbody>';
        tableEl.innerHTML = thtml;
    }}
}}

// ── Filter pill clicks ──
document.querySelectorAll('#tab-browser .pill[data-filter]').forEach(pill => {{
    pill.addEventListener('click', () => {{
        const group = pill.dataset.filter;
        const val = pill.dataset.val;

        if (val === 'all') {{
            // Deactivate all in group, activate "all"
            document.querySelectorAll(`#tab-browser .pill[data-filter="${{group}}"]`).forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
        }} else {{
            // Deactivate "all" pill in this group
            const allPill = document.querySelector(`#tab-browser .pill[data-filter="${{group}}"][data-val="all"]`);
            if (allPill) allPill.classList.remove('active');
            pill.classList.toggle('active');
            // If none active, reactivate "all"
            const anyActive = document.querySelector(`#tab-browser .pill[data-filter="${{group}}"].active`);
            if (!anyActive && allPill) allPill.classList.add('active');
        }}
        renderBrowser();
    }});
}});

// ── Edit Panel ──
function openEditPanel(name) {{
    if (!editMode) return;
    editingCard = name;
    const c = DB[name];
    if (!c) return;

    const panel = document.getElementById('edit-panel');
    const body = document.getElementById('ep-body');
    document.getElementById('ep-title').textContent = name;

    let html = '';
    if (c.img) html += `<img class="ep-card-img" src="${{c.img}}" alt="${{esc(name)}}">`;

    // Stats summary
    const gih = c.gih_wr != null ? (c.gih_wr*100).toFixed(1)+'%' : '—';
    const alsa = c.alsa != null ? c.alsa.toFixed(1) : '—';
    const diwr = c.diwr != null ? (c.diwr > 0 ? '+' : '') + (c.diwr*100).toFixed(1)+'%' : '—';
    html += `<div style="text-align:center;font-size:11px;color:#8b949e;margin-bottom:8px;">
        Tier: <b style="color:${{GRADE_COLORS[c.tier]||'#999'}}">${{c.tier||'—'}}</b> ·
        GIH: <b style="color:#f0883e">${{gih}}</b> ·
        ALSA: <b>${{alsa}}</b> ·
        DIWR: <b>${{diwr}}</b> ·
        ${{c.rarity}} · ${{c.games?.toLocaleString()||0}} games
    </div>`;

    // Sections
    html += '<div class="ep-section"><div class="ep-section-title">Sections</div><div class="tag-chips">';
    const allSections = ['bombs','build_arounds','signals','top_commons','late_pick','contested'];
    for (const s of allSections) {{
        const on = c.sections.includes(s);
        const label = s.replace(/_/g,' ');
        html += `<span class="tag-chip section ${{on?'on':'off'}}" data-group="section" data-val="${{s}}" onclick="toggleTag(this)">${{label}}</span>`;
    }}
    html += '</div></div>';

    // Archetype Roles
    html += '<div class="ep-section"><div class="ep-section-title">Archetype Roles</div>';
    const archCategories = ['signpost','payoff','enabler','removal','role_player','key_synergy'];
    for (const arch of ARCHETYPES) {{
        const myRoles = c.archetypes[arch.id] || [];
        html += `<div style="margin-bottom:4px;"><span style="font-size:11px;color:#79c0ff;">${{arch.icon}} ${{arch.name}}</span><div class="tag-chips" style="margin-top:2px;">`;
        for (const cat of archCategories) {{
            const on = myRoles.includes(cat);
            html += `<span class="tag-chip arch ${{on?'on':'off'}}" data-group="arch" data-arch="${{arch.id}}" data-val="${{cat}}" onclick="toggleArchTag(this)">${{cat.replace(/_/g,' ')}}</span>`;
        }}
        html += '</div></div>';
    }}
    html += '</div>';

    // Role tags
    html += '<div class="ep-section"><div class="ep-section-title">Role Tags</div><div class="tag-chips">';
    const roleTags = ['bomb','build-around','payoff','enabler','role-player','filler'];
    for (const t of roleTags) {{
        const on = c.tags.roles.includes(t);
        html += `<span class="tag-chip role ${{on?'on':'off'}}" data-group="roles" data-val="${{t}}" onclick="toggleTag(this)">${{t}}</span>`;
    }}
    html += '</div></div>';

    // Type tags
    html += '<div class="ep-section"><div class="ep-section-title">Type Tags</div><div class="tag-chips">';
    const typeTags = ['unconditional-removal','conditional-removal','combat-trick','bounce','evasion',
        'card-advantage','ramp-fixing','token-maker','sweeper','self-mill','counter-magic'];
    for (const t of typeTags) {{
        const on = c.tags.types.includes(t);
        html += `<span class="tag-chip type ${{on?'on':'off'}}" data-group="types" data-val="${{t}}" onclick="toggleTag(this)">${{t}}</span>`;
    }}
    html += '</div></div>';

    // Speed tags
    html += '<div class="ep-section"><div class="ep-section-title">Speed</div><div class="tag-chips">';
    const speedTags = ['aggro','midrange','control'];
    for (const t of speedTags) {{
        const on = c.tags.speed.includes(t);
        html += `<span class="tag-chip speed ${{on?'on':'off'}}" data-group="speed" data-val="${{t}}" onclick="toggleTag(this)">${{t}}</span>`;
    }}
    html += '</div></div>';

    // Comment
    html += `<div class="ep-section"><div class="ep-section-title">Comment</div>
        <textarea id="ep-comment">${{esc(c.comment||'')}}</textarea></div>`;

    // Save
    html += '<button class="ep-save" onclick="saveEdit()">Save Changes</button>';

    body.innerHTML = html;
    panel.classList.add('open');
}}

function closeEditPanel() {{
    document.getElementById('edit-panel').classList.remove('open');
    editingCard = null;
}}

function toggleTag(el) {{
    el.classList.toggle('on');
    el.classList.toggle('off');
}}

function toggleArchTag(el) {{
    el.classList.toggle('on');
    el.classList.toggle('off');
}}

function saveEdit() {{
    if (!editingCard || !DB[editingCard]) return;
    const c = DB[editingCard];

    // Sections
    c.sections = [];
    document.querySelectorAll('#ep-body .tag-chip[data-group="section"].on').forEach(el => {{
        c.sections.push(el.dataset.val);
    }});

    // Archetypes
    c.archetypes = {{}};
    for (const arch of ARCHETYPES) {{
        const roles = [];
        document.querySelectorAll(`#ep-body .tag-chip[data-arch="${{arch.id}}"].on`).forEach(el => {{
            roles.push(el.dataset.val);
        }});
        if (roles.length) c.archetypes[arch.id] = roles;
        // Also add to sections
        if (roles.length) c.sections.push(`${{arch.id}}_${{roles[0]}}`);
    }}

    // Tags
    c.tags.roles = [];
    document.querySelectorAll('#ep-body .tag-chip[data-group="roles"].on').forEach(el => {{
        c.tags.roles.push(el.dataset.val);
    }});
    c.tags.types = [];
    document.querySelectorAll('#ep-body .tag-chip[data-group="types"].on').forEach(el => {{
        c.tags.types.push(el.dataset.val);
    }});
    c.tags.speed = [];
    document.querySelectorAll('#ep-body .tag-chip[data-group="speed"].on').forEach(el => {{
        c.tags.speed.push(el.dataset.val);
    }});

    // Comment
    c.comment = document.getElementById('ep-comment').value;
    c.user_modified = true;

    saveConfig();
    renderAll();
    closeEditPanel();
}}

// ── Hover Preview (Desktop) ──
const preview = document.getElementById('preview');
const prevImg = preview.querySelector('img');
const prevName = preview.querySelector('.hover-name');
const prevType = preview.querySelector('.hover-type');
const prevStats = preview.querySelector('.hover-stats');
const prevTags = preview.querySelector('.hover-tags');

function populatePreview(tile) {{
    const name = tile.dataset.name;
    const c = DB[name];
    if (!c) return;
    prevImg.src = c.img;
    prevName.textContent = name;
    prevType.textContent = [c.mana_cost, c.type_line, c.power ? c.power+'/'+c.toughness : ''].filter(Boolean).join(' · ');
    const gih = c.gih_wr != null ? (c.gih_wr*100).toFixed(0)+'%' : '—';
    const alsa = c.alsa != null ? c.alsa.toFixed(1) : '—';
    const diwr = c.diwr != null ? (c.diwr > 0 ? '+' : '') + (c.diwr*100).toFixed(1)+'%' : '—';
    prevStats.innerHTML = `
        <span class="hs-label">GIH WR</span><span class="hs-val">${{gih}}</span>
        <span class="hs-label">ALSA</span><span class="hs-val">${{alsa}}</span>
        <span class="hs-label">DIWR</span><span class="hs-val">${{diwr}}</span>
        <span class="hs-label">Games</span><span class="hs-val">${{c.games?.toLocaleString()||'—'}}</span>
        <span class="hs-label">Rarity</span><span class="hs-val">${{c.rarity}}</span>
        <span class="hs-label">Tier</span><span class="hs-val">${{c.tier||'—'}}</span>
    `;
    // Tags
    const roleBadges = (c.tags.roles||[]).map(r => `<span style="background:#1a3a2a;border-color:#2ea043;">${{r}}</span>`);
    const typeBadges = (c.tags.types||[]).map(t => `<span>${{t}}</span>`);
    prevTags.innerHTML = roleBadges.concat(typeBadges).join('');
}}

function hidePreview() {{
    preview.style.display = 'none';
}}

if (!isMobile) {{
    document.addEventListener('mouseover', e => {{
        const tile = e.target.closest('.card-tile');
        if (tile && tile.dataset.name && DB[tile.dataset.name]) {{
            populatePreview(tile);
            preview.style.display = 'block';
        }}
    }});
    document.addEventListener('mouseout', e => {{
        if (e.target.closest('.card-tile')) hidePreview();
    }});
    document.addEventListener('mousemove', e => {{
        if (preview.style.display !== 'block') return;
        let x = e.clientX + 15, y = e.clientY - 200;
        if (x + 320 > window.innerWidth) x = e.clientX - 320;
        if (y < 5) y = 5;
        if (y + 480 > window.innerHeight) y = window.innerHeight - 490;
        preview.style.left = x + 'px';
        preview.style.top = y + 'px';
    }});
}}

// ── Mobile Detail ──
const mobileDetail = document.getElementById('mobile-detail');
const mdContent = document.getElementById('md-content');

function openMobileDetail(name) {{
    const c = DB[name];
    if (!c) return;
    const gih = c.gih_wr != null ? (c.gih_wr*100).toFixed(1)+'%' : '—';
    const alsa = c.alsa != null ? c.alsa.toFixed(1) : '—';
    const diwr = c.diwr != null ? (c.diwr > 0 ? '+' : '') + (c.diwr*100).toFixed(1)+'%' : '—';

    let html = '<div class="md-header">';
    if (c.img) html += `<img src="${{c.img}}" alt="${{esc(name)}}">`;
    html += '<div class="md-info">';
    html += `<div class="md-name">${{esc(name)}}</div>`;
    html += `<div class="md-type">${{[c.mana_cost, c.type_line].filter(Boolean).join(' · ')}}</div>`;
    html += `<div class="md-stats">
        <div><div class="ms-label">GIH WR</div><div class="ms-val">${{gih}}</div></div>
        <div><div class="ms-label">ALSA</div><div class="ms-val">${{alsa}}</div></div>
        <div><div class="ms-label">DIWR</div><div class="ms-val">${{diwr}}</div></div>
        <div><div class="ms-label">Games</div><div class="ms-val">${{c.games?.toLocaleString()||'—'}}</div></div>
        <div><div class="ms-label">Rarity</div><div class="ms-val">${{c.rarity}}</div></div>
        <div><div class="ms-label">Tier</div><div class="ms-val">${{c.tier||'—'}}</div></div>
    </div>`;
    html += '</div></div>';

    if (c.comment) {{
        html += `<div class="md-comment">${{esc(c.comment)}}</div>`;
    }}

    // Tags
    const allTags = [...(c.tags.roles||[]), ...(c.tags.types||[]), ...(c.tags.speed||[])];
    if (allTags.length) {{
        html += '<div class="md-tags">';
        for (const t of allTags) html += `<span>${{t}}</span>`;
        html += '</div>';
    }}

    // Archetype badges
    const archNames = Object.keys(c.archetypes||{{}});
    if (archNames.length) {{
        html += '<div class="md-tags">';
        for (const aId of archNames) {{
            const arch = ARCHETYPES.find(a => a.id === aId);
            if (arch) html += `<span style="background:#1a3a2a;border-color:#2ea043;">${{arch.icon}} ${{arch.name}}: ${{(c.archetypes[aId]||[]).join(', ')}}</span>`;
        }}
        html += '</div>';
    }}

    mdContent.innerHTML = html;
    mobileDetail.classList.add('active');
    mobileDetail.scrollTop = 0;
    document.body.style.overflow = 'hidden';
}}

function closeMobileDetail() {{
    mobileDetail.classList.remove('active');
    document.body.style.overflow = '';
}}

// ── Click handler ──
document.addEventListener('click', e => {{
    // Close edit panel on click outside
    const editPanel = document.getElementById('edit-panel');
    if (editPanel.classList.contains('open') && !e.target.closest('#edit-panel') && !e.target.closest('.card-tile')) {{
        closeEditPanel();
    }}

    const tile = e.target.closest('.card-tile');
    if (!tile || !tile.dataset.name) return;

    // Inside mobile detail overlay — open that card
    if (e.target.closest('#mobile-detail')) {{
        e.preventDefault();
        openMobileDetail(tile.dataset.name);
        return;
    }}
    // Inside edit panel — ignore
    if (e.target.closest('#edit-panel')) return;

    if (isMobile) {{
        e.preventDefault();
        if (editMode) {{
            openEditPanel(tile.dataset.name);
        }} else {{
            openMobileDetail(tile.dataset.name);
        }}
    }} else {{
        if (editMode) {{
            openEditPanel(tile.dataset.name);
        }}
        // else: hover preview handles it
    }}
}});

// Escape key
document.addEventListener('keydown', e => {{
    if (e.key === 'Escape') {{
        closeEditPanel();
        closeMobileDetail();
        hidePreview();
    }}
}});

// ── Search ──
let searchMatches = [];
let searchIdx = -1;
const searchInput = document.getElementById('card-search');
const searchCount = document.getElementById('search-count');

function clearHighlights() {{
    document.querySelectorAll('.search-highlight').forEach(el => {{
        el.style.outline = '';
        el.style.outlineOffset = '';
        el.classList.remove('search-highlight');
    }});
}}

function doSearch() {{
    clearHighlights();
    const q = searchInput.value.trim().toLowerCase();
    searchMatches = [];
    searchIdx = -1;
    if (!q) {{ searchCount.textContent = ''; return; }}
    document.querySelectorAll('.card-tile[data-name]').forEach(tile => {{
        if (tile.dataset.name.toLowerCase().includes(q)) {{
            searchMatches.push(tile);
            tile.style.outline = '2px solid #58a6ff';
            tile.style.outlineOffset = '1px';
            tile.classList.add('search-highlight');
        }}
    }});
    searchCount.textContent = searchMatches.length ? searchMatches.length + ' found' : 'none';
}}

function searchNext() {{
    if (!searchMatches.length) {{ doSearch(); if (!searchMatches.length) return; }}
    searchIdx = (searchIdx + 1) % searchMatches.length;
    const tile = searchMatches[searchIdx];
    tile.scrollIntoView({{behavior:'smooth', block:'center'}});
    tile.style.outline = '3px solid #f0883e';
    setTimeout(() => {{ tile.style.outline = '2px solid #58a6ff'; }}, 800);
    searchCount.textContent = (searchIdx+1) + '/' + searchMatches.length;
}}

searchInput.addEventListener('input', doSearch);
searchInput.addEventListener('keydown', e => {{ if (e.key === 'Enter') {{ e.preventDefault(); searchNext(); }} }});

// ── Tips Rendering & Editing ──
let editingTipIdx = null;

function renderTips() {{
    const container = document.getElementById('tips-container');
    if (!container) return;
    let html = '';
    TIPS.forEach((tip, i) => {{
        const editableClass = editMode ? ' editable' : '';
        const clickAttr = editMode ? ` onclick="startEditTip(${{i}})"` : '';
        html += `<div class="info-box${{editableClass}}" id="tip-box-${{i}}"${{clickAttr}}>`;
        if (editMode) {{
            html += `<span class="tip-edit-icon">✏️</span>`;
            html += `<button class="tip-del-btn" onclick="event.stopPropagation();deleteTip(${{i}})" title="Delete tip">✕</button>`;
        }}
        html += `<div class="info-title">${{tip.title}}</div>`;
        html += tip.body.replace(/\\n/g, '<br>');
        html += '</div>';
    }});
    if (editMode) {{
        html += `<div class="tip-add-btn" style="display:block;" onclick="addTip()">+ Add Tip</div>`;
    }}
    container.innerHTML = html;
}}

function startEditTip(idx) {{
    if (!editMode) return;
    editingTipIdx = idx;
    const tip = TIPS[idx];
    const box = document.getElementById('tip-box-' + idx);
    if (!box) return;
    // Convert HTML body to plain-ish text for editing (keep <b> tags, convert <br> to newlines)
    const bodyText = tip.body.replace(/\\n/g, '\\n');
    box.classList.remove('editable');
    box.onclick = null;
    box.innerHTML = `
        <input class="tip-edit-input title-input" id="tip-edit-title" value="${{esc(tip.title)}}" placeholder="Title">
        <textarea class="tip-edit-textarea" id="tip-edit-body" placeholder="Tip text (supports &lt;b&gt; for bold, use Enter for line breaks)">${{bodyText}}</textarea>
        <div class="tip-edit-actions">
            <button class="tip-cancel" onclick="event.stopPropagation();cancelEditTip()">Cancel</button>
            <button class="tip-save" onclick="event.stopPropagation();saveEditTip()">Save</button>
        </div>
    `;
    document.getElementById('tip-edit-title').focus();
}}

function saveEditTip() {{
    if (editingTipIdx == null) return;
    const title = document.getElementById('tip-edit-title').value.trim();
    const body = document.getElementById('tip-edit-body').value.replace(/\\r\\n/g, '\\n');
    if (!title) {{ alert('Title is required'); return; }}
    TIPS[editingTipIdx] = {{ title, body }};
    editingTipIdx = null;
    saveTips();
    renderTips();
}}

function cancelEditTip() {{
    editingTipIdx = null;
    renderTips();
}}

function addTip() {{
    TIPS.push({{ title: 'New Tip', body: 'Click to edit this tip.' }});
    saveTips();
    renderTips();
    // Auto-open edit for the new tip
    startEditTip(TIPS.length - 1);
}}

function deleteTip(idx) {{
    if (!confirm('Delete this tip?')) return;
    TIPS.splice(idx, 1);
    saveTips();
    renderTips();
}}

// ── Render All ──
function renderAll() {{
    renderGuide();
    renderTips();
    if (document.getElementById('tab-browser').classList.contains('active')) {{
        renderBrowser();
    }}
}}

// ── Initialize ──
loadConfig();
renderAll();

</script>
</body>
</html>'''

# ── Write output ──────────────────────────────────────────────────────────
output_path = '/home/morris/Projects/tmt-draft-guide/TMT_Draft_Guide.html'
with open(output_path, 'w') as f:
    f.write(html)

print(f'\nWritten {len(html):,} bytes to {output_path}')
print(f'Cards in DB: {len(card_config)}')
# Also save config as standalone JSON
config_path = '/home/morris/Projects/tmt-draft-guide/card_config.json'
with open(config_path, 'w') as f:
    json.dump(card_config, f, indent=2, ensure_ascii=False)
print(f'Config saved to {config_path}')
