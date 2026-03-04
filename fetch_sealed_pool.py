#!/usr/bin/env python3
"""Fetch all card data from Scryfall for the TMT sealed pool and output as JSON."""

import requests
import time
import json
import re
import sys

# TMT sealed pool - card name, set code, collector number, quantity
SEALED_POOL = [
    ("Buzz Bots", "TMT", "32", 1),
    ("Casey Jones, Jury-Rig Justiciar", "TMT", "87", 1),
    ("Zog, Triceraton Castaway", "TMT", "111", 1),
    ("Rock Soldiers", "TMT", "107", 1),
    ("Bot Bashing Time", "TMT", "85", 1),
    ("Null Group Biological Assets", "TMT", "98", 1),
    ("Casey Jones, Vigilante", "TMT", "88", 1),
    ("Wingnut, Bat on the Belfry", "TMT", "110", 1),
    ("Purple Dragon Punks", "TMT", "100", 3),
    ("Mouser Attack!", "TMT", "95", 2),
    ("Hard-Won Jitte", "TMT", "91", 1),
    ("Cool but Rude", "TMT", "89", 1),
    ("Negate", "TMT", "47", 2),
    ("Bespoke Bō", "TMT", "31", 1),
    ("Donatello's Technique", "TMT", "39", 1),
    ("Donatello, Way with Machines", "TMT", "38", 2),
    ("Mondo Gecko", "TMT", "46", 1),
    ("Retro-Mutation", "TMT", "51", 1),
    ("Utrom Scientists", "TMT", "56", 1),
    ("Donatello, Mutant Mechanic", "TMT", "36", 1),
    ("Return to the Sewers", "TMT", "52", 1),
    ("Stockman, Mad Fly-entist", "TMT", "54", 1),
    ("Kitsune, Dragon's Daughter", "TMT", "41", 1),
    ("Guac & Marshmallow Pizza", "TMT", "116", 1),
    ("Courier of Comestibles", "TMT", "112", 1),
    ("Frog Butler", "TMT", "114", 2),
    ("Tenderize", "TMT", "133", 1),
    ("Mona Lisa, Science Geek", "TMT", "123", 1),
    ("Novel Nunchaku", "TMT", "127", 1),
    ("Primordial Pachyderm", "TMT", "129", 1),
    ("Ragamuffin Raptor", "TMT", "130", 1),
    ("West Wind Avatar", "TMT", "137", 1),
    ("Squirrelanoids", "TMT", "81", 1),
    ("Paramecia Coloniex", "TMT", "70", 1),
    ("Rat King, Verminister", "TMT", "71", 1),
    ("Tunnel Rats", "TMT", "84", 1),
    ("Insectoid Exterminator", "TMT", "64", 3),
    ("Anchovy & Banana Pizza", "TMT", "57", 1),
    ("Foot Mystic", "TMT", "63", 2),
    ("Illegitimate Business", "TMT", "186", 2),
    ("Leonardo, Leader in Blue", "TMT", "16", 1),
    ("Action News Crew", "TMT", "1", 1),
    ("Lita, Little Orphan Amphibian", "TMT", "19", 1),
    ("Make Your Move", "TMT", "20", 2),
    ("Leonardo, Sewer Samurai", "TMT", "17", 1),
    ("The Last Ronin's Technique", "TMT", "12", 1),
    ("Grounded for Life", "TMT", "7", 1),
    ("Jennika, Bad Apple Big Sister", "TMT", "10", 1),
    ("Everything Pizza", "TMT", "173", 1),
    ("Escape Tunnel", "TMT", "184", 1),
    ("Chrome Dome", "TMT", "172", 1),
    ("Omni-Cheese Pizza", "TMT", "176", 2),
    ("Turtle Blimp", "TMT", "180", 1),
    ("Foot Elite", "TMT", "146", 1),
    ("Karai, Future of the Foot", "TMT", "151", 1),
    ("Foot Ninjas", "TMT", "147", 3),
    ("Krang & Shredder", "TMT", "153", 1),
    ("Nobody", "TMT", "161", 2),
    ("Tainted Treats", "TMT", "170", 1),
    ("Putrid Pals", "TMT", "165", 1),
    ("Raph & Mikey, Troublemakers", "TMT", "167", 1),
    ("EPF Point Squad", "TMT", "145", 1),
    ("The Neutrinos", "TMT", "160", 1),
    ("Slithering Cryptid", "TMT", "168", 1),
    ("Lessons from Life", "TMT", "155", 1),
    ("Punk Frogs", "TMT", "164", 1),
]

TMT_MECHANICS = {
    "Sneak": "sneak",
    "Disappear": "disappear",
    "Alliance": "alliance",
    "Mutagen": "mutagen",
}

def identify_mechanics(oracle_text: str, keywords: list) -> list:
    """Identify TMT-specific mechanics from oracle text and keywords."""
    mechs = []
    text_lower = (oracle_text or "").lower()
    kw_lower = [k.lower() for k in (keywords or [])]

    if "sneak" in text_lower or "sneak" in kw_lower:
        mechs.append("Sneak")
    if "disappear" in text_lower:
        mechs.append("Disappear")
    if "alliance" in text_lower:
        mechs.append("Alliance")
    if "mutagen" in text_lower or "mutagen token" in text_lower:
        mechs.append("Mutagen")
    # Artifact synergy markers
    if any(x in text_lower for x in ["artifact you control", "artifacts you control",
                                       "artifact creature", "noncreature artifact",
                                       "create a 1/1", "mouser", "artifact enters"]):
        mechs.append("Artifacts-matter")
    if "food" in text_lower and ("create" in text_lower or "sacrifice" in text_lower):
        mechs.append("Food")
    return mechs


def identify_roles(oracle_text: str, type_line: str, keywords: list) -> list:
    """Identify functional roles."""
    roles = []
    text_lower = (oracle_text or "").lower()
    type_lower = (type_line or "").lower()
    kw_lower = [k.lower() for k in (keywords or [])]

    # Removal
    if any(x in text_lower for x in ["destroy target", "exile target", "deals damage to",
                                       "target creature gets -", "fight"]):
        roles.append("Removal")
    # Evasion
    if any(x in kw_lower for x in ["flying", "menace", "trample", "skulk",
                                     "can't be blocked"]):
        roles.append("Evasion")
    if "can't be blocked" in text_lower:
        roles.append("Evasion")
    # Card advantage
    if any(x in text_lower for x in ["draw a card", "draw two", "draws a card",
                                       "return target", "return a"]):
        roles.append("Card Advantage")
    # Combat trick
    if "instant" in type_lower and any(x in text_lower for x in
            ["gets +", "target creature gets", "indestructible"]):
        roles.append("Combat Trick")
    # Fixing/Ramp
    if any(x in text_lower for x in ["add one mana of any", "search your library for a basic",
                                       "any color", "mana of any type"]):
        roles.append("Fixing")
    # Token maker
    if any(x in text_lower for x in ["create a", "create two", "create three"]):
        roles.append("Token Maker")

    return roles


def fetch_card(set_code: str, collector_number: str) -> dict:
    """Fetch a single card by set and collector number."""
    url = f"https://api.scryfall.com/cards/{set_code.lower()}/{collector_number}"
    resp = requests.get(url, headers={"User-Agent": "MTGADraftHelper/1.0"})
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"  WARNING: {resp.status_code} for {set_code}/{collector_number}", file=sys.stderr)
        return None


def main():
    all_cards = []
    unique_cards = len(SEALED_POOL)
    total_cards = sum(qty for _, _, _, qty in SEALED_POOL)

    print(f"Fetching {unique_cards} unique cards ({total_cards} total) from Scryfall...",
          file=sys.stderr)

    for i, (name, set_code, cn, qty) in enumerate(SEALED_POOL):
        print(f"  [{i+1}/{unique_cards}] {name} (#{cn}) x{qty}", file=sys.stderr)
        data = fetch_card(set_code, cn)
        if not data:
            # Fallback: search by name
            print(f"    Retrying by name search...", file=sys.stderr)
            time.sleep(0.12)
            search_url = f"https://api.scryfall.com/cards/search?q=!\"{name}\"+set:{set_code.lower()}"
            resp = requests.get(search_url, headers={"User-Agent": "MTGADraftHelper/1.0"})
            if resp.status_code == 200:
                results = resp.json().get("data", [])
                if results:
                    data = results[0]

        if data:
            oracle = data.get("oracle_text", "")
            keywords = data.get("keywords", [])
            mechs = identify_mechanics(oracle, keywords)
            roles = identify_roles(oracle, data.get("type_line", ""), keywords)

            card_entry = {
                "index": i + 1,
                "name": data.get("name", name),
                "qty": qty,
                "collector_number": cn,
                "mana_cost": data.get("mana_cost", ""),
                "cmc": int(data.get("cmc", 0)),
                "colors": data.get("colors", []),
                "color_identity": data.get("color_identity", []),
                "type_line": data.get("type_line", ""),
                "rarity": data.get("rarity", ""),
                "power": data.get("power", ""),
                "toughness": data.get("toughness", ""),
                "keywords": keywords,
                "oracle_text": oracle,
                "tmt_mechanics": mechs,
                "roles": roles,
                "image_uri": (data.get("image_uris") or {}).get("small", ""),
            }
            all_cards.append(card_entry)
        else:
            all_cards.append({
                "index": i + 1,
                "name": name,
                "qty": qty,
                "collector_number": cn,
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": [],
                "type_line": "",
                "rarity": "",
                "power": "",
                "toughness": "",
                "keywords": [],
                "oracle_text": "",
                "tmt_mechanics": [],
                "roles": [],
                "image_uri": "",
            })

        # Scryfall rate limit: ~10 req/sec
        time.sleep(0.12)

    print(f"\nDone! Fetched {len(all_cards)} cards.", file=sys.stderr)
    json.dump(all_cards, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
