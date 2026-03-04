#!/usr/bin/env python3
"""Build comprehensive TMT Draft Guide HTML from multiple data sources.

Data sources:
- Scryfall card database (images, oracle text, stats)
- 17Lands card_ratings API (GIH win rates, ALSA)
- 17Lands community tier list "Alex + Marc TMT tierlist" (letter grades)
- Multiple guide sources (archetype data, strategy tips)
"""

import json
import html as html_mod
import unicodedata

# ── Load data ──────────────────────────────────────────────────────────────
with open('/home/morris/Projects/mtga-draft-helper/tmt_scryfall_cards.json') as f:
    scryfall = json.load(f)

with open('/home/morris/Projects/mtga-draft-helper/tmt_17lands_ratings.json') as f:
    lands17 = json.load(f)

with open('/home/morris/Projects/mtga-draft-helper/tmt_17lands_tierlist.json') as f:
    tierlist_data = json.load(f)

# Fix known 17lands name corruptions (17lands replaces non-ASCII with ?)
NAME_FIXES = {
    'Bespoke B?': 'Bespoke Bō',
}

def normalize_name(name):
    """Normalize for fuzzy matching: strip diacritics and non-alpha noise."""
    # Apply known fixes first
    name = NAME_FIXES.get(name, name)
    nfkd = unicodedata.normalize('NFKD', name)
    stripped = ''.join(ch for ch in nfkd if unicodedata.category(ch) != 'Mn')
    return stripped.lower()

# Build lookups (keyed by original name AND normalized name for fallback)
lands_map = {}
lands_norm = {}  # normalized name -> data
for c in lands17:
    lands_map[c['name']] = c
    lands_norm[normalize_name(c['name'])] = c

# 17lands community tier list (Alex + Marc)
tier_map = {}  # card_name -> tier grade
tier_norm = {}  # normalized name -> tier grade
for c in tierlist_data['tmt_cards']:
    tier_map[c['name']] = c['tier']
    tier_norm[normalize_name(c['name'])] = c['tier']
for c in tierlist_data['source_material']:
    tier_map[c['name']] = c['tier']
    tier_norm[normalize_name(c['name'])] = c['tier']

# Build a map from normalized name -> canonical Scryfall name
scryfall_canon = {}
for sname in scryfall:
    scryfall_canon[normalize_name(sname)] = sname

def canonical_name(name):
    """Return the Scryfall canonical name if available, else original."""
    return scryfall_canon.get(normalize_name(name), name)

# Build tier buckets (using canonical Scryfall names)
tiers = {}
for c in tierlist_data['tmt_cards']:
    grade = c['tier']
    cname = canonical_name(c['name'])
    tiers.setdefault(grade, []).append(cname)

# ── ARCHETYPES ──────────────────────────────────────────────────────────────
archetypes = [
    {
        'name': 'UR Artifacts',
        'colors': ['U', 'R'],
        'color_hex': '#9b59b6',
        'icon': '⚙️',
        'short': 'Artifacts-matter aggro/tempo. Play cheap artifact creatures, buff them, generate value.',
        'strategy': 'Draft artifact creatures highly. Brilliance Unleashed is the payoff. Metalhead, Buzz Bots, Mouser Foundry are key. Manhole Missile is premium removal that also makes artifacts.',
        'signposts': ['Brilliance Unleashed', 'Metalhead'],
        'key_cards': ['Buzz Bots', 'Mouser Foundry', 'Manhole Missile', 'Mouser Mark III', 'Chrome Dome',
                      'Donatello, Turtle Techie', 'Ravenous Robots', 'Nobody', 'Does Machines', 'Sewer-veillance Cam'],
        'combos': [
            ('Brilliance Unleashed', 'Any artifact creature', 'Buff entire board when artifacts ETB'),
            ('Mouser Foundry', 'Sacrifice outlet', 'Generate artifact tokens repeatedly'),
            ('Metalhead', 'Artifact tokens', 'Copies artifact creatures for massive value'),
        ],
    },
    {
        'name': 'WB Sneak',
        'colors': ['W', 'B'],
        'color_hex': '#95a5a6',
        'icon': '🥷',
        'short': 'Evasion & disruption. Sneak creatures deal combat damage → trigger bonus effects.',
        'strategy': 'Draft Sneak creatures that get value from dealing damage. Combine evasion (flying, unblockable) with Sneak payoffs. Removal-heavy to clear path.',
        'signposts': ['Karai, Future of the Foot', 'Foot Ninjas'],
        'key_cards': ['Dimensional Exile', 'Oroku Saki, Shredder Rising', 'Turncoat Kunoichi',
                      'Stomped by the Foot', 'Grounded for Life', 'Leonardo, Big Brother',
                      "April O'Neil, Kunoichi Trainee", 'Anchovy & Banana Pizza',
                      'Mighty Mutanimals', 'Uneasy Alliance'],
        'combos': [
            ('Turncoat Kunoichi', 'Any Sneak creature', 'Repeated disruption on combat damage'),
            ('Karai, Future of the Foot', 'Foot Ninjas', 'Signpost combo: evasive + payoff'),
            ('Dimensional Exile', 'Any creature', 'Premium removal clears path for Sneak'),
        ],
    },
    {
        'name': 'BG Disappear',
        'colors': ['B', 'G'],
        'color_hex': '#27ae60',
        'icon': '💀',
        'short': 'Sacrifice & recursion. Cards Disappear (exile from grave) to fuel powerful effects.',
        'strategy': 'Self-mill and sacrifice to fill graveyard, then Disappear cards for value. Strong midrange/grindy plan. Courier of Comestibles is a top common.',
        'signposts': ['Slash, Reptile Rampager', 'Leatherhead, Swamp Stalker'],
        'key_cards': ['Frog Butler', 'Courier of Comestibles', 'Squirrelanoids',
                      'Tenderize', 'Primordial Pachyderm', 'Michelangelo, Game Master',
                      'Ice Cream Kitty', 'Ragamuffin Raptor', 'Zoo Escapees',
                      'Stomped by the Foot', 'Anchovy & Banana Pizza'],
        'combos': [
            ('Frog Butler', 'Sacrifice outlets', 'Recursive value engine from graveyard'),
            ('Courier of Comestibles', 'Disappear cards', 'Food tokens + Disappear synergy'),
            ('Slash, Reptile Rampager', 'Self-mill', 'Grows huge from Disappear count'),
        ],
    },
    {
        'name': 'RW Alliance',
        'colors': ['R', 'W'],
        'color_hex': '#e74c3c',
        'icon': '⚔️',
        'short': 'Go-wide aggro. Alliance triggers when creatures ETB. Tokens + anthems.',
        'strategy': 'Play creatures that trigger Alliance on ETB. Token generators are great. Mechanized Ninja Cavalry is a key common. Curve out aggressively.',
        'signposts': ['Groundchuck & Dirtbag', 'Mechanized Ninja Cavalry'],
        'key_cards': ['Mechanized Ninja Cavalry', 'Go Ninja Go', 'Mighty Mutanimals',
                      "April O'Neil, Kunoichi Trainee", 'Manhole Missile', 'Leonardo, Big Brother',
                      'Grounded for Life', 'Bot Bashing Time', 'Action News Crew',
                      'Mouser Foundry', 'Rock Soldiers'],
        'combos': [
            ('Mechanized Ninja Cavalry', 'Token makers', 'Multiple Alliance triggers per turn'),
            ('Groundchuck & Dirtbag', 'Go-wide board', 'Signpost gives team buffs on Alliance'),
            ('Go Ninja Go', 'Any creatures', 'Pump + Alliance synergy'),
        ],
    },
    {
        'name': 'GU Mutagen',
        'colors': ['G', 'U'],
        'color_hex': '#2ecc71',
        'icon': '🧬',
        'short': '+1/+1 counters & mutation. Mutagen creatures grow and gain abilities.',
        'strategy': 'Draft creatures that use +1/+1 counters and Mutagen. Build big threats over time. Tempo + size advantage. Mikey & Don, Party Planners is the top signpost.',
        'signposts': ['Mikey & Don, Party Planners', 'Slithering Cryptid'],
        'key_cards': ['Donatello, Turtle Techie', 'Michelangelo, Game Master',
                      'Frog Butler', 'Return to the Sewers', 'Buzz Bots',
                      'Primordial Pachyderm', 'Mind Transfer Protocol',
                      'Retro-Mutation', 'Courier of Comestibles', 'Slithering Cryptid'],
        'combos': [
            ('Mikey & Don, Party Planners', '+1/+1 counter cards', 'Signpost grows entire team'),
            ('Donatello, Turtle Techie', 'Artifacts', 'Draws cards + grows with counters'),
            ('Return to the Sewers', 'Any creature', 'Bounce + Mutagen counter'),
        ],
    },
]

# ── REMOVAL SPELLS ──────────────────────────────────────────────────────────
removal = [
    {'name': 'Dimensional Exile', 'color': 'W', 'cost': '1W', 'type': 'Enchantment', 'desc': 'Exile creature (Oblivion Ring effect)'},
    {'name': 'Grounded for Life', 'color': 'W', 'cost': '2W', 'type': 'Instant', 'desc': 'Tap + cant untap, -3/-0'},
    {'name': 'Stomped by the Foot', 'color': 'B', 'cost': '1B', 'type': 'Sorcery', 'desc': '-3/-3 until end of turn'},
    {'name': 'Anchovy & Banana Pizza', 'color': 'B', 'cost': '2B', 'type': 'Sorcery', 'desc': 'Destroy creature, lose 2 life'},
    {'name': 'Tainted Treats', 'color': 'B', 'cost': '1B', 'type': 'Instant', 'desc': 'Destroy creature that was dealt damage'},
    {'name': 'Manhole Missile', 'color': 'R', 'cost': '1R', 'type': 'Instant', 'desc': '3 damage to creature/pw, makes artifact token'},
    {'name': 'Bot Bashing Time', 'color': 'R', 'cost': 'R', 'type': 'Instant', 'desc': '2 damage (4 to artifacts)'},
    {'name': 'Tenderize', 'color': 'G', 'cost': '1G', 'type': 'Instant', 'desc': 'Fight spell'},
    {'name': 'Return to the Sewers', 'color': 'U', 'cost': '1U', 'type': 'Instant', 'desc': 'Bounce creature'},
    {'name': 'Mind Transfer Protocol', 'color': 'U', 'cost': '3U', 'type': 'Instant', 'desc': 'Gain control of creature'},
]

# ── HELPERS ──────────────────────────────────────────────────────────────
def get_img(card_name, size='normal'):
    """Get verified Scryfall image URL for a card."""
    sf = scryfall.get(card_name)
    if sf:
        return sf.get(f'image_{size}', sf.get('image_normal', ''))
    for name, data in scryfall.items():
        if card_name.lower() in name.lower() or name.lower() in card_name.lower():
            return data.get(f'image_{size}', data.get('image_normal', ''))
    return ''

def get_17l(card_name):
    """Get 17lands stats for a card."""
    c = lands_map.get(card_name)
    if not c:
        c = lands_norm.get(normalize_name(card_name))
    if c:
        gih = c.get('ever_drawn_win_rate')
        alsa = c.get('avg_seen')
        games = c.get('game_count') or 0
        return {'gih': gih, 'alsa': alsa, 'games': games}
    for name, data in lands_map.items():
        if card_name.lower() in name.lower() or name.lower() in card_name.lower():
            gih = data.get('ever_drawn_win_rate')
            alsa = data.get('avg_seen')
            games = data.get('game_count') or 0
            return {'gih': gih, 'alsa': alsa, 'games': games}
    return {'gih': None, 'alsa': None, 'games': 0}

def get_sf_data(card_name):
    """Get full Scryfall data."""
    sf = scryfall.get(card_name)
    if sf:
        return sf
    for name, data in scryfall.items():
        if card_name.lower() in name.lower() or name.lower() in card_name.lower():
            return data
    return {}

def get_tier(card_name):
    """Get community tier grade for a card."""
    t = tier_map.get(card_name)
    if not t:
        t = tier_norm.get(normalize_name(card_name))
    if t:
        return t
    for name, grade in tier_map.items():
        if card_name.lower() in name.lower() or name.lower() in card_name.lower():
            return grade
    return None

def grade_color(grade):
    """CSS color for tier grade."""
    colors = {
        'A+': '#ff4757', 'A': '#ee5a24', 'A-': '#f39c12',
        'B+': '#f1c40f', 'B': '#2ecc71', 'B-': '#1abc9c',
        'C+': '#3498db', 'C': '#95a5a6', 'C-': '#7f8c8d',
        'D+': '#636e72', 'D': '#4a4a4a', 'D-': '#3d3d3d', 'F': '#2d3436',
    }
    return colors.get(grade, '#95a5a6')

def get_diwr(card_name):
    """Get drawn improvement win rate (DIWR) for a card."""
    c = lands_map.get(card_name) or lands_norm.get(normalize_name(card_name))
    if c:
        drawn = c.get('ever_drawn_win_rate')
        not_drawn = c.get('never_drawn_win_rate')
        if drawn is not None and not_drawn is not None:
            return drawn - not_drawn
    return None

# ── DRAFT CONTEXT SYSTEM ──────────────────────────────────────────────────
import re

# Map each card to its effective color identity for archetype matching
# For lands: use produced mana colors from oracle text instead of empty colors array
MANA_SYMBOL_MAP = {'{W}': 'W', '{U}': 'U', '{B}': 'B', '{R}': 'R', '{G}': 'G'}

def get_card_colors(card_name):
    sf = get_sf_data(card_name)
    colors = set(sf.get('colors', []))
    # If colorless AND a land, derive colors from mana production in oracle text
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
    """Check if a card fits an archetype's color pair.
    - Colorless (empty): fits all archetypes
    - Dual-color lands: must exactly match the archetype colors (BG land → BG only)
    - Multi-color (2+) spells: must be a subset of archetype colors
    - Mono-color: subset (fits multiple archetypes)
    """
    if not card_colors:
        return True  # truly colorless fits all
    if land and len(card_colors) >= 2:
        return card_colors == arch_colors  # exact match for dual+ lands
    return card_colors <= arch_colors  # subset for spells

# Build archetype lookup: for each archetype, which cards fit?
arch_lookup = {}  # arch_name -> list of card names sorted by gih desc
for arch in archetypes:
    arch_colors = set(arch['colors'])
    fits = []
    for sname in scryfall:
        card_colors = get_card_colors(sname)
        if card_fits_archetype(card_colors, arch_colors, is_land(sname)):
            fits.append(sname)
    # Sort by GIH win rate descending
    def _gih(n):
        l = get_17l(n)
        return l['gih'] if l['gih'] is not None else 0
    fits.sort(key=_gih, reverse=True)
    arch_lookup[arch['name']] = fits

# Card → archetype(s) it fits in
card_archetypes = {}  # card_name -> list of arch dicts
for sname in scryfall:
    card_colors = get_card_colors(sname)
    land = is_land(sname)
    matching = []
    for arch in archetypes:
        arch_colors = set(arch['colors'])
        if card_fits_archetype(card_colors, arch_colors, land):
            matching.append(arch)
    card_archetypes[sname] = matching

# ── Enabler / Payoff detection ──
# Enablers: cards that produce something (tokens, counters, ETB, fill graveyard, artifacts)
# Payoffs: cards that benefit from those things
ROLES = {
    'makes_tokens':    re.compile(r'create[s]?\b.+\btoken', re.I),
    'wants_tokens':    re.compile(r'(whenever .* (creature|token) enters)|(for each creature)|(creature tokens you control)', re.I),
    'makes_artifacts': re.compile(r'(create[s]?\b.+\bartifact token)|(artifact creature token)|(\bArtifact\b.*\bCreature\b)', re.I),
    'wants_artifacts': re.compile(r'(whenever .* artifact enters)|(for each artifact)|(artifacts you control get)|(number of artifacts)', re.I),
    'adds_counters':   re.compile(r'put[s]?\b.+\+1/\+1 counter', re.I),
    'wants_counters':  re.compile(r'(whenever .* counter is placed)|(with .* counter.* on it get)|(remove .* counter)', re.I),
    'fills_grave':     re.compile(r'(mill)|(put .* card.* into .* graveyard)|(discard)', re.I),
    'wants_grave':     re.compile(r'(disappear)|(exile .* from .* graveyard)|(cards? in your graveyard)', re.I),
    'has_etb':         re.compile(r'when .* enters the battlefield', re.I),
    'wants_etb':       re.compile(r'(alliance)|(whenever .* creature enters)', re.I),
    'has_evasion':     re.compile(r'\b(flying|menace|unblockable|can\'t be blocked)\b', re.I),
    'wants_combat':    re.compile(r'(sneak)|(whenever .* deals combat damage)|(deals damage to .* player)', re.I),
    'makes_food':      re.compile(r'create[s]?\b.+\bfood\b', re.I),
    'wants_food':      re.compile(r'(sacrifice .* food)|(whenever .* food)|(food tokens you control)', re.I),
    'has_sacrifice':   re.compile(r'sacrifice (a|an|another)', re.I),
    'wants_dying':     re.compile(r'(whenever .* (creature )?dies)|(leaves the battlefield)', re.I),
}

# Define which roles synergize (enabler → payoff pairs)
SYNERGY_PAIRS = [
    ('makes_tokens',    'wants_tokens',    'Token makers → Token payoffs'),
    ('makes_tokens',    'wants_etb',       'Token ETBs → Alliance/ETB triggers'),
    ('makes_artifacts', 'wants_artifacts', 'Artifact producers → Artifact payoffs'),
    ('adds_counters',   'wants_counters',  '+1/+1 counter sources → Counter payoffs'),
    ('fills_grave',     'wants_grave',     'Graveyard fillers → Disappear/GY payoffs'),
    ('has_etb',         'wants_etb',       'ETB creatures → Alliance triggers'),
    ('has_evasion',     'wants_combat',    'Evasive creatures → Combat damage payoffs'),
    ('makes_food',      'wants_food',      'Food makers → Food payoffs'),
    ('has_sacrifice',   'wants_dying',     'Sacrifice outlets → Death triggers'),
    ('makes_food',      'has_sacrifice',   'Food tokens → Sacrifice fuel'),
    ('makes_tokens',    'has_sacrifice',   'Token makers → Sacrifice fuel'),
    ('makes_artifacts', 'has_sacrifice',   'Artifact tokens → Sacrifice fuel'),
]

# Pre-compute roles for all cards
card_roles = {}  # card_name -> set of role keys
role_to_cards = {}  # role_key -> list of card names
for sname in scryfall:
    sf = get_sf_data(sname)
    text = (sf.get('oracle_text', '') + ' ' + sf.get('type_line', '')).strip()
    roles = set()
    for role_key, regex in ROLES.items():
        if regex.search(text):
            roles.add(role_key)
    card_roles[sname] = roles
    for r in roles:
        role_to_cards.setdefault(r, []).append(sname)

# Build synergy connections: for each card, find cards that form enabler/payoff pairs
def get_card_synergies(card_name):
    """Return list of (reason, [partner_names sorted by GIH]) for a card.
    Partners are filtered to only cards that share at least one archetype
    with this card (i.e. could actually be in the same deck)."""
    my_roles = card_roles.get(card_name, set())
    if not my_roles:
        return []
    # Build set of all colors this card's archetypes span
    my_archs = card_archetypes.get(card_name, [])
    my_arch_names = {a['name'] for a in my_archs}

    def is_color_compatible(partner_name):
        """Can this partner be in the same deck as card_name?"""
        partner_archs = card_archetypes.get(partner_name, [])
        # Partner shares at least one archetype with us
        return any(a['name'] in my_arch_names for a in partner_archs)

    results = []
    seen_partners = set()
    for enabler_role, payoff_role, label in SYNERGY_PAIRS:
        partners = []
        if enabler_role in my_roles:
            for p in role_to_cards.get(payoff_role, []):
                if p != card_name and p not in seen_partners and is_color_compatible(p):
                    partners.append(p)
        if payoff_role in my_roles:
            for p in role_to_cards.get(enabler_role, []):
                if p != card_name and p not in seen_partners and is_color_compatible(p):
                    partners.append(p)
        if partners:
            def _gih(n):
                l = get_17l(n)
                return l['gih'] if l['gih'] is not None else 0
            partners.sort(key=_gih, reverse=True)
            results.append((label, partners[:10]))
            seen_partners.update(partners[:10])
    return results

# Human-readable role labels for display
ROLE_LABELS = {
    'makes_tokens': 'Token Maker', 'wants_tokens': 'Token Payoff',
    'makes_artifacts': 'Artifact Producer', 'wants_artifacts': 'Artifact Payoff',
    'adds_counters': 'Counter Source', 'wants_counters': 'Counter Payoff',
    'fills_grave': 'Graveyard Filler', 'wants_grave': 'Graveyard Payoff',
    'has_etb': 'ETB Effect', 'wants_etb': 'ETB/Alliance Trigger',
    'has_evasion': 'Evasion', 'wants_combat': 'Combat Damage Payoff',
    'makes_food': 'Food Maker', 'wants_food': 'Food Payoff',
    'has_sacrifice': 'Sacrifice Outlet', 'wants_dying': 'Death Trigger',
}

# Determine which cards deserve full draft context (synergy partners, top archetype cards)
# Only bombs, build-arounds, and high-performing cards — not random filler
CONTEXT_WORTHY_GRADES = {'S', 'A+', 'A', 'A-', 'B+', 'B'}  # top ~45 cards
# Hardcoded bomb/build-around names (bomb_categories is defined later in HTML section)
BOMB_CARD_NAMES = {
    # First-pick bombs
    'The Last Ronin', 'Sally Pride, Lioness Leader', 'Agent Bishop, Man in Black',
    'Krang & Shredder', 'North Wind Avatar',
    # Build-around rares
    'Brilliance Unleashed', 'Leatherhead, Swamp Stalker', 'Mikey & Don, Party Planners',
    'Triceraton Commander', "Leader's Talent", 'Turncoat Kunoichi', 'Krang, Master Mind',
    # Premium uncommons
    'Metalhead', 'Mighty Mutanimals', "April O'Neil, Hacktivist",
    'Raph & Mikey, Troublemakers', 'Rat King, Verminister',
    'Groundchuck & Dirtbag', 'Karai, Future of the Foot', 'Slash, Reptile Rampager',
    # Top commons
    'Courier of Comestibles', 'Frog Butler', 'Manhole Missile', 'Dimensional Exile',
    'Mechanized Ninja Cavalry', 'Stomped by the Foot', 'Ravenous Robots', 'Does Machines',
}
# Also include signpost uncommons and top key cards from archetypes
for arch in archetypes:
    for sp in arch['signposts']:
        BOMB_CARD_NAMES.add(sp)
    for kc in arch['key_cards'][:3]:
        BOMB_CARD_NAMES.add(kc)

def is_context_worthy(card_name):
    """Should this card get full synergy partner data?"""
    if card_name in BOMB_CARD_NAMES:
        return True
    grade = get_tier(card_name)
    if grade and any(grade.startswith(g) for g in CONTEXT_WORTHY_GRADES):
        return True
    # Rares/mythics with good GIH
    sf = get_sf_data(card_name)
    l17 = get_17l(card_name)
    if sf.get('rarity') in ('rare', 'mythic') and l17['gih'] is not None and l17['gih'] >= 0.54:
        return True
    return False

# Build draft context data — full synergies only for worthy cards
draft_context = {}  # card_name -> { archetypes, roles, synergies }
context_worthy_count = 0
for sname in scryfall:
    card_archs = card_archetypes.get(sname, [])
    roles = card_roles.get(sname, set())
    entry = {
        'archetypes': [{'name': a['name'], 'icon': a['icon'], 'colors': a['colors']} for a in card_archs],
        'roles': [ROLE_LABELS.get(r, r) for r in sorted(roles)],
    }
    if is_context_worthy(sname):
        syns = get_card_synergies(sname)
        entry['synergies'] = [{'label': label, 'partners': partners} for label, partners in syns]
        entry['worthy'] = True
        context_worthy_count += 1
    else:
        entry['synergies'] = []
    draft_context[sname] = entry

print(f'Context-worthy cards (full synergy data): {context_worthy_count}/195')


# Backward compat: synergy_data for data-tags display (now shows role labels)
synergy_data = {}
for sname in scryfall:
    roles = card_roles.get(sname, set())
    if roles:
        synergy_data[sname] = [ROLE_LABELS.get(r, r) for r in sorted(roles)]


def card_tile_html(card_name, grade=None, extra_class=''):
    """Generate a uniform card tile with hover preview. ALL tiles same size. Always shows GIH + ALSA.
    Embeds rich data for enhanced hover and synergy panel."""
    img = get_img(card_name, 'normal')
    sf = get_sf_data(card_name)
    l17 = get_17l(card_name)

    # Auto-detect grade from community tier list if not provided
    if grade is None:
        grade = get_tier(card_name)

    rarity = sf.get('rarity', '')[0:1].upper() if sf.get('rarity') else '?'
    rarity_full = {'C': 'Common', 'U': 'Uncommon', 'R': 'Rare', 'M': 'Mythic'}.get(rarity, 'Unknown')
    rarity_class = {'C': 'rar-c', 'U': 'rar-u', 'R': 'rar-r', 'M': 'rar-m'}.get(rarity, '')
    mana = sf.get('mana_cost', '')
    type_line = sf.get('type_line', '')
    oracle = sf.get('oracle_text', '')
    pt = ''
    if sf.get('power'):
        pt = f"{sf['power']}/{sf['toughness']}"

    gih_str = f"{l17['gih']:.0%}" if l17['gih'] is not None else '—'
    alsa_str = f"{l17['alsa']:.1f}" if l17['alsa'] is not None else '—'
    games_str = f"{l17['games']:,}" if l17['games'] else '—'

    diwr = get_diwr(card_name)
    diwr_str = f"{diwr:+.1%}" if diwr is not None else '—'

    grade_badge = ''
    if grade:
        grade_badge = f'<span class="grade" style="background:{grade_color(grade)}">{grade}</span>'

    # Always show GIH and ALSA under every card
    stats_html = f'<div class="stats">GIH:{gih_str} ALSA:{alsa_str}</div>'

    # Embed rich data for enhanced hover
    esc_name = html_mod.escape(card_name)
    esc_mana = html_mod.escape(mana)
    esc_type = html_mod.escape(type_line)
    esc_oracle = html_mod.escape(oracle).replace('\n', '&#10;')
    esc_pt = html_mod.escape(pt)
    tags_str = html_mod.escape(','.join(synergy_data.get(card_name, [])))

    data_attrs = (f'data-name="{esc_name}" data-img="{img}" '
                  f'data-mana="{esc_mana}" data-type="{esc_type}" '
                  f'data-oracle="{esc_oracle}" data-pt="{esc_pt}" '
                  f'data-rarity="{rarity_full}" data-grade="{grade or ""}" '
                  f'data-gih="{gih_str}" data-alsa="{alsa_str}" '
                  f'data-games="{games_str}" data-diwr="{diwr_str}" '
                  f'data-tags="{tags_str}"')

    if not img:
        return f'''<div class="card-tile {extra_class}" {data_attrs}>
            {grade_badge}
            <div class="card-noimg"><span class="{rarity_class}">{esc_name}</span></div>
            {stats_html}
        </div>'''

    return f'''<div class="card-tile {extra_class}" {data_attrs}>
        {grade_badge}
        <img src="{img}" alt="{esc_name}" loading="lazy">
        {stats_html}
    </div>'''


# ── BUILD HTML ──────────────────────────────────────────────────────────────
html_parts = []

html_parts.append('''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>TMT Draft Guide — Teenage Mutant Ninja Turtles</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0d1117; color:#c9d1d9; font-family:system-ui,-apple-system,sans-serif; font-size:15px; line-height:1.5; }

/* Full width layout */
.page { width:100%; padding:6px 12px; }
h1 { font-size:24px; text-align:center; color:#58a6ff; padding:8px 0 2px; }
h1 small { font-size:13px; color:#8b949e; font-weight:normal; display:block; }
h2 { font-size:19px; color:#f0883e; padding:8px 0 4px; border-bottom:1px solid #21262d; margin-bottom:6px; }
h3 { font-size:16px; color:#79c0ff; margin:4px 0 3px; }

/* ── UNIFORM CARD TILES ── All cards same width everywhere */
.card-tile {
    display:inline-block; position:relative; width:130px; margin:2px; cursor:pointer;
    border-radius:6px; overflow:hidden; background:#161b22; border:1px solid #21262d;
    vertical-align:top; transition:transform .15s, box-shadow .15s;
}
.card-tile:hover { transform:scale(1.05); box-shadow:0 4px 16px rgba(0,0,0,.5); z-index:10; }
.card-tile img { width:100%; display:block; border-radius:5px 5px 0 0; }
.card-noimg { padding:6px; font-size:10px; min-height:60px; display:flex; align-items:center; justify-content:center; text-align:center; }
.grade { position:absolute; top:2px; left:2px; font-size:12px; font-weight:bold; color:#fff;
    padding:2px 6px; border-radius:3px; z-index:2; text-shadow:0 1px 2px rgba(0,0,0,.9); }
.stats { font-size:11px; padding:3px 4px; background:#0d1117; color:#8b949e; text-align:center; white-space:nowrap; }

/* Rarity colors */
.rar-c { color:#c9d1d9; } .rar-u { color:#a8d8ea; } .rar-r { color:#f5c842; } .rar-m { color:#f5842c; }

/* ── ARCHETYPES ── */
.arch-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:4px; margin-bottom:6px; }
@media(max-width:1400px) { .arch-grid { grid-template-columns:repeat(3,1fr); } }
@media(max-width:700px) { .arch-grid { grid-template-columns:1fr; } }
.arch-box { background:#161b22; border:1px solid #21262d; border-radius:6px; padding:6px; }
.arch-box .arch-title { font-size:17px; font-weight:bold; margin-bottom:3px; }
.arch-box .arch-desc { font-size:13px; color:#8b949e; margin-bottom:4px; }
.arch-box .arch-strat { font-size:13px; color:#c9d1d9; margin-bottom:4px; display:none; }
.arch-box:hover .arch-strat { display:block; }
.arch-box .signpost-label { font-size:13px; color:#f0883e; font-weight:bold; margin-top:3px; }
.arch-cards { display:flex; flex-wrap:wrap; gap:2px; }
.combo-row { display:flex; align-items:center; gap:4px; font-size:12px; color:#8b949e; padding:2px 0; border-top:1px solid #21262d; margin-top:2px; }
.combo-row .combo-cards { display:flex; gap:2px; }
.combo-row .combo-desc { flex:1; }

/* ── TIER LIST ── */
.tier-section { margin-bottom:4px; display:flex; align-items:flex-start; flex-wrap:wrap; }
.tier-header { display:inline-flex; align-items:center; justify-content:center;
    font-size:16px; font-weight:bold; padding:5px 12px; border-radius:4px; color:#fff;
    min-width:44px; margin-right:4px; margin-top:2px; flex-shrink:0; }
.tier-cards { display:inline-flex; flex-wrap:wrap; flex:1; }

/* ── COLOR SECTIONS ── */
.color-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:4px; }
@media(max-width:1000px) { .color-grid { grid-template-columns:repeat(3,1fr); } }
.color-col { background:#161b22; border:1px solid #21262d; border-radius:4px; padding:4px; }
.color-col h3 { text-align:center; font-size:16px; margin-bottom:3px; }
.color-col .card-tile { display:inline-block; }

/* ── REMOVAL ── same card-tile style, just in a flex grid */
.removal-flex { display:flex; flex-wrap:wrap; gap:2px; }

/* ── ENHANCED HOVER PREVIEW ── */
#preview { display:none; position:fixed; z-index:3000; pointer-events:none;
    border-radius:12px; box-shadow:0 8px 32px rgba(0,0,0,.9); background:#161b22;
    border:1px solid #30363d; width:320px; max-height:92vh; overflow-y:auto; }
#preview.mobile-show { pointer-events:auto; }
#preview img { width:100%; display:block; border-radius:12px 12px 0 0; }
#preview .hover-info { padding:8px 10px; font-size:12px; line-height:1.4; }
#preview .hover-name { font-size:14px; font-weight:bold; color:#58a6ff; margin-bottom:2px; }
#preview .hover-type { color:#8b949e; margin-bottom:4px; }
#preview .hover-stats { display:grid; grid-template-columns:1fr 1fr; gap:2px 8px; font-size:11px; }
#preview .hover-stats .hs-label { color:#8b949e; }
#preview .hover-stats .hs-val { color:#f0883e; font-weight:bold; }
#preview .hover-tags { margin-top:4px; display:flex; flex-wrap:wrap; gap:3px; }
#preview .hover-tags span { font-size:10px; padding:1px 6px; border-radius:8px;
    background:#21262d; color:#79c0ff; border:1px solid #30363d; }
#preview-close { display:none; position:absolute; top:4px; right:4px; z-index:10;
    background:#21262d; color:#c9d1d9; border:1px solid #30363d; border-radius:50%;
    width:28px; height:28px; font-size:14px; cursor:pointer; line-height:26px; text-align:center; }
@media(max-width:768px) { #preview-close { display:block; top:4px; right:4px; } }
/* Mobile backdrop overlay */
#preview-backdrop { display:none; position:fixed; top:0; left:0; right:0; bottom:0;
    background:rgba(0,0,0,.5); z-index:2999; }
#preview-backdrop.active { display:block; }

/* ── SYNERGY SLIDE PANEL ── */
#synergy-panel { position:fixed; top:0; right:-420px; width:400px; height:100vh; z-index:2000;
    background:#0d1117; border-left:2px solid #58a6ff; box-shadow:-8px 0 32px rgba(0,0,0,.7);
    transition:right .3s ease; overflow-y:auto; padding:0; }
#synergy-panel.open { right:0; }
#synergy-panel .sp-header { position:sticky; top:0; background:#161b22; padding:10px 12px;
    border-bottom:1px solid #21262d; display:flex; align-items:center; justify-content:space-between; z-index:1; }
#synergy-panel .sp-header h3 { font-size:15px; color:#58a6ff; margin:0; }
#synergy-panel .sp-close { background:none; border:1px solid #30363d; color:#c9d1d9;
    padding:4px 10px; border-radius:4px; cursor:pointer; font-size:13px; }
#synergy-panel .sp-close:hover { background:#21262d; }
#synergy-panel .sp-card-img { width:200px; display:block; margin:10px auto; border-radius:8px; }
#synergy-panel .sp-section { padding:8px 12px; border-bottom:1px solid #21262d; }
#synergy-panel .sp-tag-title { font-size:13px; color:#f0883e; font-weight:bold; margin-bottom:4px; cursor:pointer; user-select:none; display:flex; align-items:center; gap:6px; }
#synergy-panel .sp-tag-title:hover { color:#ffa657; }
#synergy-panel .sp-tag-title .toggle-arrow { transition:transform 0.2s; display:inline-block; font-size:10px; }
#synergy-panel .sp-tag-title.collapsed .toggle-arrow { transform:rotate(-90deg); }
#synergy-panel .sp-cards-wrapper { overflow:hidden; transition:max-height 0.3s ease; }
#synergy-panel .sp-cards-wrapper.collapsed { max-height:0 !important; }
#synergy-panel .sp-tag-title .tag-badge { font-size:11px; padding:1px 6px; border-radius:8px;
    background:#21262d; color:#79c0ff; border:1px solid #30363d; margin-left:4px; }
#synergy-panel .sp-cards { display:flex; flex-wrap:wrap; gap:3px; }
#synergy-panel .sp-cards .card-tile { width:90px; }
#synergy-panel .sp-cards .card-tile .stats { font-size:9px; }
#synergy-panel .sp-none { color:#8b949e; font-size:12px; font-style:italic; padding:10px 12px; }

/* ── DRAFT SIGNALS ── */
.signals-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:6px; }
@media(max-width:900px) { .signals-grid { grid-template-columns:1fr; } }
.signal-box { background:#161b22; border:1px solid #21262d; border-radius:6px; padding:8px; }
.signal-box h3 { margin-bottom:4px; }
.signal-box .signal-desc { font-size:12px; color:#8b949e; margin-bottom:6px; }

/* Navigation */
nav { display:flex; gap:4px; justify-content:center; flex-wrap:wrap; padding:4px 0;
    position:sticky; top:0; background:#0d1117; z-index:100; border-bottom:1px solid #21262d; }
nav a { color:#58a6ff; text-decoration:none; font-size:14px; padding:4px 10px; background:#161b22;
    border:1px solid #21262d; border-radius:4px; }
nav a:hover { background:#21262d; }

/* ── MOBILE RESPONSIVE ── */
@media(max-width:600px) {
    .page { padding:4px 6px; }
    h1 { font-size:18px; } h2 { font-size:16px; } h3 { font-size:14px; }
    nav { gap:2px; padding:3px 0; }
    nav a { font-size:11px; padding:3px 6px; }
    nav input { width:100px !important; font-size:11px !important; }
    .card-tile { width:90px !important; margin:1px !important; }
    .card-tile img { border-radius:3px 3px 0 0; }
    .stats { font-size:9px !important; padding:2px 3px !important; }
    .grade { font-size:10px !important; padding:1px 4px !important; }
    .arch-grid { grid-template-columns:1fr !important; }
    .color-grid { grid-template-columns:repeat(2,1fr) !important; gap:3px !important; }
    .signals-grid { grid-template-columns:1fr !important; }
    .info-columns { grid-template-columns:1fr !important; }
    .stats-bar { font-size:11px; gap:4px; }
    .stats-bar span { padding:2px 5px; font-size:10px; }
    /* Bomb tiles slightly narrower on mobile */
    #bombs .card-tile { width:110px !important; }
    #bombs .card-tile div[style*="font-weight:bold"] { font-size:9px !important; }
}

/* ── MOBILE: full-screen card detail overlay ── */
#mobile-detail { display:none; position:fixed; top:0; left:0; right:0; bottom:0;
    z-index:4000; background:#0d1117; overflow-y:auto; -webkit-overflow-scrolling:touch; }
#mobile-detail.active { display:block; }
#mobile-detail .md-close { position:fixed; top:10px; right:10px; z-index:4001;
    background:#21262d; color:#c9d1d9; border:1px solid #30363d; border-radius:50%;
    width:36px; height:36px; font-size:18px; cursor:pointer; line-height:34px; text-align:center; }
#mobile-detail .md-header { display:flex; gap:10px; padding:12px; padding-top:50px; }
#mobile-detail .md-header img { width:140px; border-radius:8px; flex-shrink:0; }
#mobile-detail .md-info { flex:1; }
#mobile-detail .md-name { font-size:16px; font-weight:bold; color:#58a6ff; margin-bottom:4px; }
#mobile-detail .md-type { font-size:12px; color:#8b949e; margin-bottom:6px; }
#mobile-detail .md-oracle { font-size:12px; color:#c9d1d9; white-space:pre-wrap;
    border-left:2px solid #30363d; padding-left:6px; margin-bottom:8px; }
#mobile-detail .md-stats { display:grid; grid-template-columns:1fr 1fr 1fr; gap:4px; font-size:12px; }
#mobile-detail .md-stats .ms-label { color:#8b949e; font-size:10px; }
#mobile-detail .md-stats .ms-val { color:#f0883e; font-weight:bold; }
#mobile-detail .md-tags { display:flex; flex-wrap:wrap; gap:4px; padding:8px 12px; }
#mobile-detail .md-tags span { font-size:11px; padding:2px 8px; border-radius:10px;
    background:#21262d; color:#79c0ff; border:1px solid #30363d; }
#mobile-detail .md-syn-section { padding:8px 12px; border-top:1px solid #21262d; }
#mobile-detail .md-syn-title { font-size:14px; color:#f0883e; font-weight:bold; margin-bottom:6px;
    cursor:pointer; user-select:none; display:flex; align-items:center; gap:6px; }
#mobile-detail .md-syn-title:hover { color:#ffa657; }
#mobile-detail .md-syn-title .toggle-arrow { transition:transform 0.2s; font-size:10px; }
#mobile-detail .md-syn-title.collapsed .toggle-arrow { transform:rotate(-90deg); }
#mobile-detail .md-syn-cards-wrap { overflow:hidden; transition:max-height 0.3s ease; }
#mobile-detail .md-syn-cards-wrap.collapsed { max-height:0 !important; }
#mobile-detail .md-syn-cards { display:flex; flex-wrap:wrap; gap:4px; }
#mobile-detail .md-syn-cards .card-tile { width:80px; }
#mobile-detail .md-syn-cards .card-tile .stats { font-size:9px; }
#mobile-detail .md-divider { text-align:center; padding:12px; font-size:15px; color:#58a6ff;
    font-weight:bold; border-top:2px solid #21262d; margin-top:4px; }

/* Hide desktop-only elements on mobile */
@media(max-width:768px) {
    #preview { display:none !important; }
    #preview-backdrop { display:none !important; }
    #synergy-panel { width:100vw !important; right:-100vw !important; }
    #synergy-panel.open { right:0 !important; }
    #synergy-panel .sp-card-img { width:140px; }
    #synergy-panel .sp-cards .card-tile { width:70px !important; }
}

/* Stats bar */
.stats-bar { display:flex; gap:8px; justify-content:center; padding:6px; font-size:13px; color:#8b949e; flex-wrap:wrap; }
.stats-bar span { background:#161b22; padding:2px 8px; border-radius:3px; border:1px solid #21262d; }
.stats-bar .highlight { color:#f0883e; }

/* Info boxes */
.info-box { background:#161b22; border:1px solid #21262d; border-radius:6px; padding:10px 12px; margin:4px 0; font-size:14px; line-height:1.6; }
.info-box .info-title { color:#f0883e; font-weight:bold; font-size:15px; margin-bottom:4px; }
.info-columns { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:8px; }
</style>
</head>
<body>
<div class="page">
<h1>🐢 TMT Draft Guide — Teenage Mutant Ninja Turtles
<small>17Lands Community Tier List (Alex + Marc) + 17Lands Win Rates + Multiple Guide Sources</small></h1>
<nav>
    <a href="#tips">💡 Tips</a>
    <a href="#bombs">💣 Must-Pick</a>
    <a href="#signals">🧭 Signals</a>
    <a href="#archetypes">Archetypes</a>
    <a href="#tierlist">Tier List</a>
    <a href="#bycolor">By Color</a>
    <a href="#removal">Removal</a>
    <a href="#lands">Lands & Fixing</a>
    <span style="display:inline-flex;align-items:center;gap:3px;margin-left:8px;">
        <input type="text" id="card-search" placeholder="🔍 Search card..." style="padding:4px 8px;font-size:13px;background:#161b22;color:#c9d1d9;border:1px solid #21262d;border-radius:4px;width:160px;">
        <button onclick="searchNext()" style="padding:4px 8px;font-size:12px;background:#21262d;color:#58a6ff;border:1px solid #30363d;border-radius:4px;cursor:pointer;">Next ▼</button>
        <span id="search-count" style="font-size:11px;color:#8b949e;min-width:40px;"></span>
    </span>
</nav>
''')

# ── QUICK STATS BAR ──────────────────────────────────────────────────────────
valid_17l = [c for c in lands17 if c.get('ever_drawn_win_rate') is not None and (c.get('game_count') or 0) > 50]
valid_17l.sort(key=lambda x: x['ever_drawn_win_rate'], reverse=True)

html_parts.append('<div class="stats-bar">')
html_parts.append(f'<span>Cards: <b>{len(scryfall)}</b></span>')
html_parts.append(f'<span>17L tracked (50+ games): <b>{len(valid_17l)}</b></span>')
html_parts.append(f'<span>Community tier list: <b>{tierlist_data["name"]}</b> ({len(tierlist_data["tmt_cards"])} cards)</span>')
if valid_17l:
    best = valid_17l[0]
    html_parts.append(f'<span class="highlight">Top GIH WR: {best["name"]} ({best["ever_drawn_win_rate"]:.0%})</span>')
html_parts.append('</div>')

# ── DRAFT TIPS (at the top so drafters see format overview first) ──────────
html_parts.append('''<div id="tips"><h2>💡 Draft Tips — Format Overview</h2>
<div class="info-columns">
<div class="info-box">
    <div class="info-title">🎯 Mana Curve</div>
    1-drops: 1–2 • 2-drops: 4–5 • 3-drops: 4–5 • 4-drops: 3–4 • 5+: 2–3<br>
    Total: 16–17 creatures, 6–8 spells, 16–17 lands
</div>
<div class="info-box">
    <div class="info-title">⚙️ Format Key Mechanics</div>
    <b>Artifacts</b> — creatures that are artifacts count for BOTH artifact synergies AND creature synergies<br>
    <b>Disappear</b> — exile cards from your graveyard to fuel powerful effects (self-mill &amp; sacrifice fill the yard)<br>
    <b>Sneak</b> — bonus effects when dealing combat damage to a player (needs evasion or removal to clear blockers)<br>
    <b>Alliance</b> — triggers whenever a creature ETBs on your side (token makers give multiple triggers)<br>
    <b>Mutagen</b> — +1/+1 counters matter; creatures grow and gain abilities over time
</div>
<div class="info-box">
    <div class="info-title">🏆 Format Speed</div>
    Medium speed format. Aggressive decks (RW Alliance, UR Artifacts) can close games by turn 6–7.<br>
    BG Disappear grinds the longest. Respect early pressure — don't be too greedy with your curve.
</div>
<div class="info-box">
    <div class="info-title">📈 Draft Priorities</div>
    <b>P1P1:</b> Bombs &gt; Premium removal &gt; Best uncommon signpost<br>
    <b>Pack 1:</b> Stay open, grab the best card regardless of color<br>
    <b>Pack 2:</b> Commit to an archetype, prioritize synergy pieces<br>
    <b>Pack 3:</b> Fill curve gaps, grab fixing, snag last removal spells
</div>
</div>
</div>''')

# ── BOMBS & FIRST-PICK SIGNALS ──────────────────────────────────────────────
# The whole point: tell drafters WHAT to pick and WHY
bomb_categories = [
    {
        'label': '💣 FIRST-PICK BOMBS — Take these over everything',
        'color': '#ff4757',
        'desc': 'These win games by themselves. Take P1P1 regardless of color.',
        'cards': [
            ('The Last Ronin', 'Best card in the set. Wins the game if unanswered.'),
            ('Sally Pride, Lioness Leader', 'Insane value engine. Build around her with tokens/go-wide.'),
            ('Agent Bishop, Man in Black', 'Premium threat + removal. Fits any deck with white/black.'),
            ('Krang & Shredder', 'Two-card army. Game-ending bomb.'),
            ('North Wind Avatar', 'Evasive finisher with massive upside.'),
        ],
    },
    {
        'label': '🏆 BUILD-AROUND RARES — Commit to the archetype if you open these',
        'color': '#ee5a24',
        'desc': 'These define your draft. If you open one, build your deck around it.',
        'cards': [
            ('Brilliance Unleashed', 'SIGNAL: Go UR Artifacts. Every artifact ETB pumps your whole team.'),
            ('Leatherhead, Swamp Stalker', 'SIGNAL: Go BG Disappear. Grows huge from graveyard exile.'),
            ('Mikey & Don, Party Planners', 'SIGNAL: Go GU Mutagen. Grows your entire team with counters.'),
            ('Triceraton Commander', 'Enormous value. Worth splashing for.'),
            ("Leader's Talent", 'Premium enchantment. Wins games over time.'),
            ('Turncoat Kunoichi', 'SIGNAL: Go WB Sneak. Repeated disruption machine.'),
            ('Krang, Master Mind', 'Control finisher. Build a controlling deck around this.'),
        ],
    },
    {
        'label': '⭐ PREMIUM UNCOMMONS — These pull you into an archetype',
        'color': '#f1c40f',
        'desc': 'Seeing these late = the archetype is OPEN. Strong signals in pack 1.',
        'cards': [
            ('Metalhead', 'UR Artifacts payoff. Copies artifact creatures — insane value.'),
            ('Mighty Mutanimals', 'Goes in any green deck. Highest GIH win rate in the set.'),
            ("April O'Neil, Hacktivist", 'Premium card advantage. Any deck wants her.'),
            ('Raph & Mikey, Troublemakers', 'Strong gold uncommon for aggressive decks.'),
            ('Rat King, Verminister', 'BG value engine. Graveyard shenanigans.'),
            ('Groundchuck & Dirtbag', 'RW Alliance signpost. If this wheels, RW is wide open.'),
            ('Karai, Future of the Foot', 'WB Sneak signpost. Late = Sneak is open.'),
            ('Slash, Reptile Rampager', 'BG Disappear signpost. Grows massive from Disappear count.'),
        ],
    },
    {
        'label': '🔧 TOP COMMONS — The backbone of every good deck',
        'color': '#2ecc71',
        'desc': 'Draft these highly. Having multiples of these wins drafts.',
        'cards': [
            ('Courier of Comestibles', 'Best common. Food + Disappear synergy. Goes in any black/green deck.'),
            ('Frog Butler', 'Recursive value from graveyard. Great in BG and GU.'),
            ('Manhole Missile', '3 damage + artifact token. Premium red common.'),
            ('Dimensional Exile', 'Best white common. Oblivion Ring effect.'),
            ('Mechanized Ninja Cavalry', 'RW Alliance key common. Multiple triggers per turn.'),
            ('Stomped by the Foot', 'Cheap black removal. Always playable.'),
            ('Ravenous Robots', 'UR Artifacts key creature. Strong in any red deck.'),
            ('Does Machines', 'Artifact synergy common. Good in UR.'),
        ],
    },
]

html_parts.append('<div id="bombs"><h2>💣 Must-Pick Cards & Draft Signals</h2>')
html_parts.append('<p style="font-size:14px;color:#c9d1d9;margin-bottom:6px;">If you see these cards, here\'s exactly what to do:</p>')

for cat in bomb_categories:
    html_parts.append(f'<div style="margin-bottom:8px;">')
    html_parts.append(f'<h3 style="color:{cat["color"]};font-size:16px;margin-bottom:3px;">{cat["label"]}</h3>')
    html_parts.append(f'<p style="font-size:13px;color:#8b949e;margin-bottom:4px;">{cat["desc"]}</p>')
    html_parts.append(f'<div style="display:flex;flex-wrap:wrap;gap:2px;">')
    for card_name, advice in cat['cards']:
        # Build a tile with advice overlay + rich data attributes
        img = get_img(card_name, 'normal')
        sf = get_sf_data(card_name)
        l17 = get_17l(card_name)
        grade = get_tier(card_name)
        grade_badge = f'<span class="grade" style="background:{grade_color(grade)}">{grade}</span>' if grade else ''
        gih_str = f"{l17['gih']:.0%}" if l17['gih'] is not None else '—'
        alsa_str = f"{l17['alsa']:.1f}" if l17['alsa'] is not None else '—'
        games_str = f"{l17['games']:,}" if l17['games'] else '—'
        diwr = get_diwr(card_name)
        diwr_str = f"{diwr:+.1%}" if diwr is not None else '—'
        mana = html_mod.escape(sf.get('mana_cost', ''))
        type_line = html_mod.escape(sf.get('type_line', ''))
        oracle = html_mod.escape(sf.get('oracle_text', '')).replace('\n', '&#10;')
        pt = ''
        if sf.get('power'):
            pt = html_mod.escape(f"{sf['power']}/{sf['toughness']}")
        rarity_full = {'c':'Common','u':'Uncommon','r':'Rare','m':'Mythic'}.get(sf.get('rarity','')[0:1], 'Unknown')
        tags_str = html_mod.escape(','.join(synergy_data.get(card_name, [])))
        esc_name = html_mod.escape(card_name)

        html_parts.append(f'''<div class="card-tile" data-name="{esc_name}" data-img="{img}"
            data-mana="{mana}" data-type="{type_line}" data-oracle="{oracle}" data-pt="{pt}"
            data-rarity="{rarity_full}" data-grade="{grade or ''}" data-gih="{gih_str}"
            data-alsa="{alsa_str}" data-games="{games_str}" data-diwr="{diwr_str}"
            data-tags="{tags_str}" style="width:150px;">
            {grade_badge}
            <img src="{img}" alt="{esc_name}" loading="lazy">
            <div style="font-size:11px;padding:3px 4px;background:#0d1117;color:#f0883e;text-align:center;font-weight:bold;">{html_mod.escape(advice)}</div>
            <div class="stats">GIH:{gih_str} ALSA:{alsa_str}</div>
        </div>''')
    html_parts.append('</div></div>')

html_parts.append('</div>')

# ── DRAFT SIGNALS (good late picks vs contested premiums) ──────────────────
# Good late picks: decent GIH + high ALSA (underdrafted, open signal)
# Contested premiums: good GIH + low ALSA (overdrafted, don't chase)
signal_pool = [c for c in lands17
    if c.get('ever_drawn_win_rate') is not None
    and c.get('avg_seen') is not None
    and (c.get('game_count') or 0) > 100
    and c.get('rarity') in ('common', 'uncommon')]

# Sort by ALSA descending for late picks (high ALSA = seen late = available)
late_picks = sorted([c for c in signal_pool if c['ever_drawn_win_rate'] >= 0.55 and c['avg_seen'] >= 5.0],
                    key=lambda x: x['avg_seen'], reverse=True)[:12]

# Sort by ALSA ascending for contested (low ALSA = picked early = contested)
# Use looser thresholds: GIH>=54%, ALSA<=4.5 to catch more premium C/U that get snapped up
contested = sorted([c for c in signal_pool if c['ever_drawn_win_rate'] >= 0.54 and c['avg_seen'] <= 4.5],
                   key=lambda x: x['avg_seen'])[:12]

html_parts.append('<div id="signals"><h2>🧭 Draft Signals — Read the Table</h2>')
html_parts.append('<p style="font-size:13px;color:#8b949e;margin-bottom:6px;">Use ALSA (Average Last Seen At) to detect which colors are open vs overdrafted. These are C/U only — the ones that signal lanes.</p>')
html_parts.append('<div class="signals-grid">')

# Good late picks
html_parts.append('<div class="signal-box" style="border-top:3px solid #2ecc71;">')
html_parts.append('<h3 style="color:#2ecc71;">🟢 Good Late Picks — Underdrafted</h3>')
html_parts.append('<div class="signal-desc">High GIH win rate + high ALSA = strong cards going late. If you see these late in pack 1, that color is OPEN.</div>')
html_parts.append('<div style="display:flex;flex-wrap:wrap;gap:2px;">')
for c in late_picks:
    html_parts.append(card_tile_html(c['name']))
html_parts.append('</div></div>')

# Contested premiums
html_parts.append('<div class="signal-box" style="border-top:3px solid #e74c3c;">')
html_parts.append('<h3 style="color:#e74c3c;">🔴 Contested Premiums — Overdrafted</h3>')
html_parts.append('<div class="signal-desc">High GIH win rate + low ALSA = everyone wants these. Don\'t force a color just because you got one — these go early and dry up fast.</div>')
html_parts.append('<div style="display:flex;flex-wrap:wrap;gap:2px;">')
for c in contested:
    html_parts.append(card_tile_html(c['name']))
html_parts.append('</div></div>')

html_parts.append('</div></div>')

# ── ARCHETYPES ──────────────────────────────────────────────────────────────
html_parts.append('<div id="archetypes"><h2>⚔️ Archetypes</h2>')
html_parts.append('<div class="arch-grid">')

for arch in archetypes:
    c1, c2 = arch['colors']
    color_icons = {'W': '⚪', 'U': '🔵', 'B': '⚫', 'R': '🔴', 'G': '🟢'}
    ci = color_icons.get(c1, '') + color_icons.get(c2, '')

    html_parts.append(f'<div class="arch-box" style="border-top:3px solid {arch["color_hex"]}">')
    html_parts.append(f'<div class="arch-title">{arch["icon"]} {arch["name"]} {ci}</div>')
    html_parts.append(f'<div class="arch-desc">{arch["short"]}</div>')
    html_parts.append(f'<div class="arch-strat">{arch["strategy"]}</div>')

    # Signpost cards
    html_parts.append('<div class="signpost-label">📌 Signposts:</div>')
    html_parts.append('<div class="arch-cards">')
    for card in arch['signposts']:
        html_parts.append(card_tile_html(card))
    html_parts.append('</div>')

    # Key cards
    html_parts.append('<div class="signpost-label">🔑 Key Cards:</div>')
    html_parts.append('<div class="arch-cards">')
    for card in arch['key_cards'][:8]:
        html_parts.append(card_tile_html(card))
    html_parts.append('</div>')

    # Combos
    if arch['combos']:
        html_parts.append('<div class="signpost-label">💥 Combos (hover strategy):</div>')
        for combo in arch['combos'][:2]:
            html_parts.append(f'<div class="combo-row">')
            html_parts.append(f'<div class="combo-cards">')
            html_parts.append(card_tile_html(combo[0]))
            html_parts.append(f'</div>')
            html_parts.append(f'<div class="combo-desc">+ {combo[1]}: <em>{combo[2]}</em></div>')
            html_parts.append('</div>')

    html_parts.append('</div>')

html_parts.append('</div></div>')

# ── TIER LIST (from 17lands community tier list) ──────────────────────────
html_parts.append('<div id="tierlist"><h2>📊 Community Tier List — "' + html_mod.escape(tierlist_data['name']) + '"</h2>')
html_parts.append('<p style="font-size:14px;color:#8b949e;margin-bottom:4px;">B- and above = Very Good | C/D = Tentative | Below D = Skip</p>')

tier_order = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F']
for grade in tier_order:
    cards = tiers.get(grade, [])
    if not cards:
        continue

    # Determine opacity: good tiers full, tentative dimmer, bad dimmest
    if grade in ['A+', 'A', 'A-', 'B+', 'B', 'B-']:
        opacity = '1'
    elif grade in ['C+', 'C', 'C-']:
        opacity = '0.7'
    else:
        opacity = '0.45'

    html_parts.append(f'<div class="tier-section" style="opacity:{opacity}">')
    html_parts.append(f'<span class="tier-header" style="background:{grade_color(grade)}">{grade}</span>')
    html_parts.append(f'<span class="tier-cards">')
    for card in cards:
        html_parts.append(card_tile_html(card, grade=grade))
    html_parts.append('</span></div>')

html_parts.append('</div>')

# ── BY COLOR (community tier list, all cards sorted by tier grade) ────────────
TIER_RANK = {t: i for i, t in enumerate(['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F'])}

# Build color -> list of (card_name, tier) from tier list
color_tier_cards = {}
for c in tierlist_data['tmt_cards']:
    cname = canonical_name(c['name'])
    color_tier_cards.setdefault(c['color'], []).append((cname, c['tier']))
# Sort each color by tier rank (best first)
for color in color_tier_cards:
    color_tier_cards[color].sort(key=lambda x: TIER_RANK.get(x[1], 99))

html_parts.append('<div id="bycolor"><h2>🎨 Cards by Color — Community Tier List</h2>')
html_parts.append('<p style="font-size:13px;color:#8b949e;margin-bottom:6px;">All cards from the Alex + Marc tier list, sorted by grade within each color. Hover/tap for full stats.</p>')
html_parts.append('<div class="color-grid">')

color_names = [('W', '⚪ White'), ('U', '🔵 Blue'), ('B', '⚫ Black'), ('R', '🔴 Red'), ('G', '🟢 Green')]
for color_code, color_label in color_names:
    cards = color_tier_cards.get(color_code, [])
    html_parts.append(f'<div class="color-col">')
    html_parts.append(f'<h3>{color_label} <span style="font-size:12px;color:#8b949e;">({len(cards)})</span></h3>')
    for cname, tier in cards:
        html_parts.append(card_tile_html(cname, grade=tier))
    html_parts.append('</div>')

html_parts.append('</div>')

# Multicolor
multi_cards = color_tier_cards.get('M', [])
if multi_cards:
    html_parts.append('<h3 style="margin-top:8px;">🌈 Multicolor <span style="font-size:12px;color:#8b949e;">(' + str(len(multi_cards)) + ')</span></h3>')
    html_parts.append('<div style="display:flex;flex-wrap:wrap;gap:2px;">')
    for cname, tier in multi_cards:
        html_parts.append(card_tile_html(cname, grade=tier))
    html_parts.append('</div>')

# Colorless + Lands
other_cards = color_tier_cards.get('C', []) + color_tier_cards.get('L', [])
other_cards.sort(key=lambda x: TIER_RANK.get(x[1], 99))
if other_cards:
    html_parts.append('<h3 style="margin-top:8px;">⬜ Colorless & Lands <span style="font-size:12px;color:#8b949e;">(' + str(len(other_cards)) + ')</span></h3>')
    html_parts.append('<div style="display:flex;flex-wrap:wrap;gap:2px;">')
    for cname, tier in other_cards:
        html_parts.append(card_tile_html(cname, grade=tier))
    html_parts.append('</div>')

html_parts.append('</div>')

# ── REMOVAL (categorized by color) ────────────────────────────────────────
COLOR_ORDER = [('W', '⬜ White', '#f8f8f0'), ('U', '🔵 Blue', '#0e6faf'),
               ('B', '⚫ Black', '#a0a0a0'), ('R', '🔴 Red', '#d32029'), ('G', '🟢 Green', '#00733e')]
html_parts.append('<div id="removal"><h2>🗡️ Key Removal Spells</h2>')
for color_code, color_label, color_hex in COLOR_ORDER:
    color_cards = [r for r in removal if r['color'] == color_code]
    if not color_cards:
        continue
    html_parts.append(f'<h3 style="font-size:14px;color:{color_hex};margin:8px 0 4px;">{color_label}</h3>')
    html_parts.append('<div class="removal-flex">')
    for r in color_cards:
        html_parts.append(card_tile_html(r['name']))
    html_parts.append('</div>')
html_parts.append('</div>')

# (Tips section was moved to the top of the page)

# ── LANDS & FIXING ──────────────────────────────────────────────────────────
html_parts.append('<div id="lands"><h2>🏔️ Lands & Fixing</h2>')
html_parts.append('<div style="display:flex;flex-wrap:wrap;gap:2px;">')
land_names = ['Escape Tunnel', 'Mutant Town', 'TCRI Building', 'Foot Headquarters',
              'Illegitimate Business', 'Omni-Cheese Pizza', 'Everything Pizza']
for name in land_names:
    html_parts.append(card_tile_html(name))
html_parts.append('</div></div>')

# ── DRAFT CONTEXT DATA (embedded as JSON for panels) ──────────────────────
synergy_json = json.dumps({
    'cards': draft_context,       # card_name -> {archetypes, roles, synergies}
})

# ── HOVER PREVIEW + SYNERGY PANEL + SEARCH SCRIPT ────────────────────────
html_parts.append(f'''
<div id="preview-backdrop"></div>
<div id="preview">
    <button id="preview-close" onclick="hidePreview();lastTappedCard=null;">✕</button>
    <img src="" alt="preview">
    <div class="hover-info">
        <div class="hover-name"></div>
        <div class="hover-type"></div>
        <div class="hover-stats"></div>
        <div class="hover-tags"></div>
    </div>
</div>

<div id="synergy-panel">
    <div class="sp-header">
        <h3 id="sp-title">Draft Context</h3>
        <div style="display:flex;gap:6px;align-items:center;">
            <button class="sp-close" onclick="toggleAllSyn()" id="sp-expand-btn" style="font-size:11px;padding:3px 8px;">Expand All</button>
            <button class="sp-close" onclick="closeSynergy()">✕</button>
        </div>
    </div>
    <div id="sp-body"></div>
</div>

<div id="mobile-detail">
    <button class="md-close" onclick="closeMobileDetail()">✕</button>
    <div id="md-content"></div>
</div>

<script>
/* ── Synergy data ── */
const SYNERGY = {synergy_json};

/* ── Enhanced hover preview ── */
const preview = document.getElementById('preview');
const prevImg = preview.querySelector('img');
const prevName = preview.querySelector('.hover-name');
const prevType = preview.querySelector('.hover-type');
const prevStats = preview.querySelector('.hover-stats');
const prevTags = preview.querySelector('.hover-tags');
const isMobile = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
let lastTappedCard = null;

const backdrop = document.getElementById('preview-backdrop');

function populatePreview(tile) {{
    if (!tile || !tile.dataset.img) return;
    prevImg.src = tile.dataset.img;
    prevName.textContent = tile.dataset.name || '';
    const mana = tile.dataset.mana || '';
    const type = tile.dataset.type || '';
    const pt = tile.dataset.pt || '';
    prevType.textContent = [mana, type, pt].filter(Boolean).join(' · ');
    const rarity = tile.dataset.rarity || '';
    const grade = tile.dataset.grade || '';
    prevStats.innerHTML = `
        <span class="hs-label">GIH WR</span><span class="hs-val">${{tile.dataset.gih||'—'}}</span>
        <span class="hs-label">ALSA</span><span class="hs-val">${{tile.dataset.alsa||'—'}}</span>
        <span class="hs-label">DIWR</span><span class="hs-val">${{tile.dataset.diwr||'—'}}</span>
        <span class="hs-label">Games</span><span class="hs-val">${{tile.dataset.games||'—'}}</span>
        <span class="hs-label">Rarity</span><span class="hs-val">${{rarity}}</span>
        <span class="hs-label">Tier</span><span class="hs-val">${{grade||'—'}}</span>
    `;
    // Show archetype fit + roles in hover tags
    const hoverCtx = SYNERGY.cards[tile.dataset.name] || {{}};
    const archBadges = (hoverCtx.archetypes || []).map(a => `<span style="background:#1a3a2a;color:#58a6ff;border-color:#2ea043;">${{a.icon}} ${{a.name}}</span>`);
    const roleBadges = (hoverCtx.roles || []).map(r => `<span>${{r}}</span>`);
    prevTags.innerHTML = archBadges.concat(roleBadges).join('');
}}

function hidePreview() {{
    preview.style.display = 'none';
    preview.classList.remove('mobile-show');
    backdrop.classList.remove('active');
    lastTappedCard = null;
}}

/* ── Desktop: hover to preview, click to synergy ── */
if (!isMobile) {{
    document.addEventListener('mouseover', e => {{
        const tile = e.target.closest('.card-tile');
        if (tile && tile.dataset.img) {{
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
        if (x + 340 > window.innerWidth) x = e.clientX - 340;
        if (y < 5) y = 5;
        if (y + 500 > window.innerHeight) y = window.innerHeight - 510;
        preview.style.left = x + 'px';
        preview.style.top = y + 'px';
    }});
}}

/* ── Mobile: tap card = full-screen detail with stats + synergies ── */
const mobileDetail = document.getElementById('mobile-detail');
const mdContent = document.getElementById('md-content');

function buildMobilePartnerHtml(partners, exclude) {{
    let html = '';
    for (const p of partners) {{
        if (p === exclude) continue;
        const pt2 = document.querySelector(`.card-tile[data-name="${{CSS.escape(p)}}"]`);
        const pimg = pt2 ? pt2.dataset.img : '';
        const pgih = pt2 ? pt2.dataset.gih : '—';
        if (pimg) {{
            html += `<div class="card-tile syn-card" data-name="${{p}}" data-img="${{pimg}}"
                data-mana="${{pt2?.dataset.mana||''}}" data-type="${{pt2?.dataset.type||''}}"
                data-oracle="${{pt2?.dataset.oracle||''}}" data-pt="${{pt2?.dataset.pt||''}}"
                data-rarity="${{pt2?.dataset.rarity||''}}" data-grade="${{pt2?.dataset.grade||''}}"
                data-gih="${{pt2?.dataset.gih||''}}" data-alsa="${{pt2?.dataset.alsa||''}}"
                data-games="${{pt2?.dataset.games||''}}" data-diwr="${{pt2?.dataset.diwr||''}}"
                data-tags="${{pt2?.dataset.tags||''}}">
                <img src="${{pimg}}" alt="${{p}}" loading="lazy">
                <div class="stats">GIH:${{pgih}}</div>
            </div>`;
        }}
    }}
    return html;
}}

function openMobileDetail(tile) {{
    if (!tile || !tile.dataset.name) return;
    const name = tile.dataset.name;
    const img = tile.dataset.img || '';
    const mana = tile.dataset.mana || '';
    const type = tile.dataset.type || '';
    const pt = tile.dataset.pt || '';
    const oracle = (tile.dataset.oracle || '').replace(/&#10;/g, '\\n');
    const gih = tile.dataset.gih || '—';
    const alsa = tile.dataset.alsa || '—';
    const diwr = tile.dataset.diwr || '—';
    const games = tile.dataset.games || '—';
    const rarity = tile.dataset.rarity || '';
    const grade = tile.dataset.grade || '—';

    const ctx = SYNERGY.cards[name] || {{}};
    const archs = ctx.archetypes || [];
    const roles = ctx.roles || [];
    const syns = ctx.synergies || [];

    let html = '<div class="md-header">';
    if (img) html += `<img src="${{img}}" alt="${{name}}">`;
    html += '<div class="md-info">';
    html += `<div class="md-name">${{name}}</div>`;
    html += `<div class="md-type">${{[mana, type, pt].filter(Boolean).join(' · ')}}</div>`;
    if (oracle) html += `<div class="md-oracle">${{oracle}}</div>`;
    html += `<div class="md-stats">
        <div><div class="ms-label">GIH WR</div><div class="ms-val">${{gih}}</div></div>
        <div><div class="ms-label">ALSA</div><div class="ms-val">${{alsa}}</div></div>
        <div><div class="ms-label">DIWR</div><div class="ms-val">${{diwr}}</div></div>
        <div><div class="ms-label">Games</div><div class="ms-val">${{games}}</div></div>
        <div><div class="ms-label">Rarity</div><div class="ms-val">${{rarity}}</div></div>
        <div><div class="ms-label">Tier</div><div class="ms-val">${{grade}}</div></div>
    </div>`;
    html += '</div></div>';

    // Archetype fit badges
    if (archs.length) {{
        html += '<div class="md-tags">';
        for (const a of archs) {{
            html += `<span>${{a.icon}} ${{a.name}}</span>`;
        }}
        html += '</div>';
    }}

    // Role badges
    if (roles.length) {{
        html += '<div class="md-tags">';
        for (const r of roles) {{
            html += `<span style="background:#161b22;color:#8b949e;">${{r}}</span>`;
        }}
        html += '</div>';
    }}

    // Show synergy sections only for context-worthy cards (bombs, build-arounds, top cards)
    if (ctx.worthy) {{
        // Enabler / Payoff synergies
        if (syns.length) {{
            html += '<div class="md-divider">Synergy Partners</div>';
            for (const syn of syns) {{
                const secId = 'msyn-ep-' + syn.label.replace(/[^a-zA-Z0-9]/g,'');
                html += '<div class="md-syn-section">';
                html += `<div class="md-syn-title" onclick="toggleMobileSyn(this,'${{secId}}')"><span class="toggle-arrow">▼</span>${{syn.label}} <span style="font-size:11px;padding:1px 6px;border-radius:8px;background:#21262d;color:#79c0ff;border:1px solid #30363d;margin-left:4px;">${{syn.partners.length}}</span></div>`;
                html += `<div id="${{secId}}" class="md-syn-cards-wrap"><div class="md-syn-cards">`;
                html += buildMobilePartnerHtml(syn.partners.slice(0, 10), name);
                html += '</div></div></div>';
            }}
        }}
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

function toggleMobileSyn(titleEl, secId) {{
    const wrapper = document.getElementById(secId);
    if (!wrapper) return;
    titleEl.classList.toggle('collapsed');
    wrapper.classList.toggle('collapsed');
    if (!wrapper.classList.contains('collapsed')) {{
        wrapper.style.maxHeight = wrapper.scrollHeight + 'px';
    }}
}}

if (isMobile) {{
    // Tap any card tile → open full-screen detail
    document.addEventListener('click', e => {{
        if (e.target.closest('#mobile-detail')) {{
            // Inside the detail overlay — check if it's a synergy card tile
            const synCard = e.target.closest('.syn-card');
            if (synCard && synCard.dataset.name) {{
                e.preventDefault();
                e.stopPropagation();
                openMobileDetail(synCard);
            }}
            return;
        }}
        if (e.target.closest('#synergy-panel')) return;
        const tile = e.target.closest('.card-tile');
        if (tile && tile.dataset.name && tile.dataset.img) {{
            e.preventDefault();
            openMobileDetail(tile);
        }}
    }});
}}

/* ── Toggle synergy sections ── */
function toggleSyn(titleEl, secId) {{
    const wrapper = document.getElementById(secId);
    if (!wrapper) return;
    titleEl.classList.toggle('collapsed');
    wrapper.classList.toggle('collapsed');
    if (!wrapper.classList.contains('collapsed')) {{
        wrapper.style.maxHeight = wrapper.scrollHeight + 'px';
    }}
}}
function toggleAllSyn() {{
    const titles = document.querySelectorAll('#sp-body .sp-tag-title');
    const wrappers = document.querySelectorAll('#sp-body .sp-cards-wrapper');
    const btn = document.getElementById('sp-expand-btn');
    const allExpanded = [...wrappers].every(w => !w.classList.contains('collapsed'));
    titles.forEach(t => {{ if (allExpanded) t.classList.add('collapsed'); else t.classList.remove('collapsed'); }});
    wrappers.forEach(w => {{
        if (allExpanded) {{ w.classList.add('collapsed'); }}
        else {{ w.classList.remove('collapsed'); w.style.maxHeight = w.scrollHeight + 'px'; }}
    }});
    btn.textContent = allExpanded ? 'Expand All' : 'Collapse All';
}}

/* ── Draft Context slide panel ── */
function buildPartnerTilesHtml(partners, exclude) {{
    let html = '';
    for (const p of partners) {{
        if (p === exclude) continue;
        const pt = document.querySelector(`.card-tile[data-name="${{CSS.escape(p)}}"]`);
        const pimg = pt ? pt.dataset.img : '';
        const pgih = pt ? pt.dataset.gih : '—';
        if (pimg) {{
            html += `<div class="card-tile" data-name="${{p}}" data-img="${{pimg}}"
                data-mana="${{pt?.dataset.mana||''}}" data-type="${{pt?.dataset.type||''}}"
                data-oracle="${{pt?.dataset.oracle||''}}" data-pt="${{pt?.dataset.pt||''}}"
                data-rarity="${{pt?.dataset.rarity||''}}" data-grade="${{pt?.dataset.grade||''}}"
                data-gih="${{pt?.dataset.gih||''}}" data-alsa="${{pt?.dataset.alsa||''}}"
                data-games="${{pt?.dataset.games||''}}" data-diwr="${{pt?.dataset.diwr||''}}"
                data-tags="${{pt?.dataset.tags||''}}">
                <img src="${{pimg}}" alt="${{p}}" loading="lazy">
                <div class="stats">GIH:${{pgih}}</div>
            </div>`;
        }}
    }}
    return html;
}}

function openSynergy(cardName) {{
    const ctx = SYNERGY.cards[cardName] || {{}};
    // Only open panel for context-worthy cards (bombs, build-arounds, top cards)
    if (!ctx.worthy) return;

    const panel = document.getElementById('synergy-panel');
    const body = document.getElementById('sp-body');
    document.getElementById('sp-title').textContent = cardName + ' — Draft Context';

    const tile = document.querySelector(`.card-tile[data-name="${{CSS.escape(cardName)}}"]`);
    const img = tile ? tile.dataset.img : '';

    let html = '';
    if (img) html += `<img class="sp-card-img" src="${{img}}" alt="${{cardName}}">`;

    // 1) Archetype Fit
    const archs = ctx.archetypes || [];
    if (archs.length) {{
        html += '<div class="sp-section">';
        html += '<div class="sp-tag-title" style="cursor:default"><span style="font-size:10px;">📋</span> Archetype Fit</div>';
        html += '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px;">';
        for (const a of archs) {{
            html += `<span style="font-size:11px;padding:2px 8px;border-radius:10px;background:#21262d;color:#79c0ff;border:1px solid #30363d;">${{a.icon}} ${{a.name}}</span>`;
        }}
        html += '</div></div>';
    }}

    // 2) Roles
    const roles = ctx.roles || [];
    if (roles.length) {{
        html += '<div class="sp-section">';
        html += '<div class="sp-tag-title" style="cursor:default"><span style="font-size:10px;">🏷️</span> Card Roles</div>';
        html += '<div style="display:flex;flex-wrap:wrap;gap:3px;margin-top:4px;">';
        for (const r of roles) {{
            html += `<span style="font-size:10px;padding:1px 6px;border-radius:8px;background:#21262d;color:#c9d1d9;border:1px solid #30363d;">${{r}}</span>`;
        }}
        html += '</div></div>';
    }}

    // 3) Enabler / Payoff Synergies
    const syns = ctx.synergies || [];
    if (syns.length) {{
        for (const syn of syns) {{
            const secId = 'syn-ep-' + syn.label.replace(/[^a-zA-Z0-9]/g,'');
            html += '<div class="sp-section">';
            html += `<div class="sp-tag-title collapsed" onclick="toggleSyn(this,'${{secId}}')"><span class="toggle-arrow">▼</span>${{syn.label}} <span class="tag-badge">${{syn.partners.length}}</span></div>`;
            html += `<div id="${{secId}}" class="sp-cards-wrapper collapsed"><div class="sp-cards">`;
            html += buildPartnerTilesHtml(syn.partners.slice(0, 12), cardName);
            html += '</div></div></div>';
        }}
    }}

    if (!archs.length && !syns.length) {{
        html += '<div class="sp-none">No draft context detected for this card.</div>';
    }}

    body.innerHTML = html;
    panel.classList.add('open');
}}

function closeSynergy() {{
    document.getElementById('synergy-panel').classList.remove('open');
}}

// Desktop: Click on card → open synergy panel
if (!isMobile) {{
    document.addEventListener('click', e => {{
        const tile = e.target.closest('.card-tile');
        if (tile && tile.dataset.name) {{
            if (tile.closest('#synergy-panel')) return;
            openSynergy(tile.dataset.name);
        }}
    }});
}}

// Close panel when clicking/tapping outside
document.addEventListener('click', e => {{
    const panel = document.getElementById('synergy-panel');
    if (panel.classList.contains('open') && !e.target.closest('#synergy-panel') && !e.target.closest('.card-tile')) {{
        closeSynergy();
    }}
}});

// Close on Escape
document.addEventListener('keydown', e => {{
    if (e.key === 'Escape') closeSynergy();
}});

/* ── Card Search ── */
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
</script>
</div>
</body>
</html>''')

# ── WRITE OUTPUT ──────────────────────────────────────────────────────────
output = '\n'.join(html_parts)
output_path = '/home/morris/Projects/mtga-draft-helper/TMT_Draft_Guide.html'
with open(output_path, 'w') as f:
    f.write(output)

# Stats
img_count = output.count('data-img="https://')
tile_count = output.count('class="card-tile')
sally_count = output.count('Sally Pride')
print(f'Written {len(output):,} bytes to {output_path}')
print(f'Card tiles: {tile_count}')
print(f'Hover images: {img_count}')
print(f'Sally Pride mentions: {sally_count}')
print(f'Tier list source: {tierlist_data["name"]}')
