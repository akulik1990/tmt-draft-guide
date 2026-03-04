# TMT Draft Guide — Full Redesign Plan

## Overview
Transform the static generated draft guide into an **editable tool** with data-driven card positions, a 2-tab layout, better archetype categories, and persistent storage via localStorage + JSON export/import.

---

## Phase 1: Data Layer — `card_config.json`

Create a JSON config that stores ALL card positions/tags. The build script generates the **initial** config from current computed data, then the page reads it at runtime.

**Schema per card:**
```json
{
  "Brilliance Unleashed": {
    "tier": "A+",
    "gih_wr": 62.3,
    "alsa": 1.8,
    "diwr": 5.1,
    "rarity": "R",
    "colors": ["U", "R"],
    "img": "https://cards.scryfall.io/normal/...",
    "scryfall": { "type_line": "...", "mana_cost": "...", "oracle_text": "..." },
    "sections": ["bombs", "ur_artifacts_payoff"],
    "archetypes": {
      "ur_artifacts": ["payoff", "signpost"],
      "rw_alliance": []
    },
    "tags": {
      "roles": ["bomb"],
      "types": ["card-advantage"],
      "speed": ["midrange"]
    },
    "removal_type": null,
    "comment": "Build-around mythic. Buffs all artifact creatures on ETB.",
    "user_modified": false
  }
}
```

**`sections` values:** `bombs`, `build_arounds`, `signals`, `top_commons`, `{arch_id}_{category}`

**Archetype categories (per card per archetype):** `signpost`, `payoff`, `enabler`, `removal`, `role_player`, `key_synergy`

**Tag taxonomy:**
- Roles: bomb, build-around, payoff, enabler, role-player, filler
- Types: unconditional-removal, conditional-removal, combat-trick, bounce, evasion, card-advantage, ramp-fixing, token-maker, sweeper, self-mill, counter-spell
- Speed: aggro, midrange, control

---

## Phase 2: Build Script Rewrite

Rewrite `build_draft_guide.py` to:

1. **Generate `card_config.json`** with auto-tagged initial data (heuristic-based from oracle text + current hardcoded lists)
2. **Generate `TMT_Draft_Guide.html`** that reads `card_config.json` at load time (embedded as `const CARD_DB = {...}`) instead of computing positions
3. Page layout becomes **2 tabs**:
   - **Draft Guide** tab (default)
   - **Card Browser** tab

---

## Phase 3: Draft Guide Tab Layout

```
┌─────────────────────────────────────────────┐
│  [Draft Guide]  [Card Browser]  [Edit Mode] │
├─────────────────────────────────────────────┤
│  📋 GENERAL TIPS (collapsible)              │
├──────────────────────┬──────────────────────┤
│  🏆 MUST-PICK CARDS  │  📡 DRAFT SIGNALS    │
│  (bombs + build-     │  (late premium uncom  │
│   arounds, sorted    │   mons = open archety │
│   by tier)           │   pe, contested cards │
│                      │   with low ALSA)      │
├──────────────────────┴──────────────────────┤
│  ARCHETYPES (5 sections, each with:)        │
│  ┌─ Signposts ─┬─ Payoffs ─┬─ Enablers ──┐ │
│  ├─ Removal ───┼─ Role Players ──────────┤  │
│  └─ Key Synergies (pairs shown together) ┘  │
└─────────────────────────────────────────────┘
```

**Must-Pick Cards (left):** All cards with section=`bombs` or `build_arounds`, sorted by tier grade. Richer tiles with tier badge + one-line comment.

**Draft Signals (right):** Cards that signal an open archetype. Premium uncommons with high GIH + late ALSA. Grouped by archetype. Each shows "seeing this P1P4+ = archetype is open".

---

## Phase 4: Card Browser Tab

Full filterable/sortable view of ALL 195 cards.

**Filters (top bar, pill-style toggles):**
- Color: W U B R G M C L (toggle pills)
- Rarity: C U R M
- Role tags: bomb, build-around, payoff, enabler, role-player, filler
- Type tags: removal, evasion, card-advantage, token-maker, etc.
- Archetype: UR, WB, BG, RW, GU
- Text search

**Sort options:** Tier Grade (default), GIH WR, ALSA, Name, CMC

**Card grid:** Same tile component as Draft Guide, all 195+ cards shown with filters applied.

---

## Phase 5: Edit Mode + Right Panel

Toggle "Edit Mode" button in nav → enables editing.

**When Edit Mode is ON and you click a card:**
Right panel slides in (400px wide on desktop, full-screen on mobile) showing:

1. **Card image** (large) + stats (GIH, ALSA, DIWR, tier, rarity)
2. **Sections** — pill chips showing which sections this card appears in. Click X to remove, click "+ Add to section" dropdown to add.
3. **Archetype Roles** — for each archetype the card is in, show category chips (signpost/payoff/enabler/etc). Clickable to add/remove.
4. **Tags** — three groups (Roles, Types, Speed) shown as colored pill chips. Tap to toggle on/off. Visual: green=active, gray=inactive.
5. **Comment** — editable textarea, pre-populated from guide data.
6. **"Save" button** → updates localStorage immediately.

---

## Phase 6: Persistence

- **localStorage** — all edits auto-save to `tmt_draft_config` key
- **Export** button → downloads current config as `card_config.json`
- **Import** button → file picker to load a saved config
- **Reset** button → clears localStorage, reverts to built-in defaults (the embedded JSON)
- On page load: check localStorage first, fall back to embedded defaults

---

## Implementation Sequence

1. Generate `card_config.json` from current data (auto-tag with heuristics)
2. Rewrite HTML generation: embed config, 2-tab layout, new Draft Guide structure
3. Build Card Browser tab with filters/sorting
4. Build Edit Mode + right panel editor
5. Add localStorage persistence + export/import
6. Test on desktop + mobile
7. Deploy

**Estimated: ~1500 lines of Python changes + substantial JS rewrite. Single build script still generates single HTML file.**

---

## Design Decisions (defaults — will proceed unless you say otherwise)

1. **Auto-tag first pass** using oracle text heuristics, then you refine via Edit Mode
2. **Mobile Edit Mode** = simplified (fewer controls, stacked layout) but functional
3. **No undo/redo** — just current state + Reset to defaults
4. **Draft Guide = default tab**
5. **Removal subtypes**: unconditional, conditional, combat-trick, bounce, sweeper
6. **Archetype Traps** = skip for now, can add later via Edit Mode tags
