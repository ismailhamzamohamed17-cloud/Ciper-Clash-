from __future__ import annotations

import html
import random
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple, cast

import streamlit as st


Coord = Tuple[int, int]
Payload = Dict[str, str]
GameState = Dict[str, Any]

APP_NAME = "Cipher Clash"
MAX_ROUNDS = 24
MAP_WIDTH = 13
MAP_HEIGHT = 9

# A deliberately simple, readable top-down floor plan. # = wall, letters = rooms, . = corridor.
FACILITY_MAP: List[str] = [
    "#############",
    "#GGG#OOO#VVV#",
    "#GGG#...#VVV#",
    "#GGG.....VVV#",
    "#.....#.....#",
    "#CCC#...#HHH#",
    "#CCC#...#HHH#",
    "#CCC#...#HHH#",
    "#############",
]

ROOMS: Dict[str, Dict[str, str]] = {
    "G": {"name": "Glasshouse", "short": "GLASS", "color": "#4be0ae"},
    "O": {"name": "Observatory", "short": "ORBIT", "color": "#ffd166"},
    "V": {"name": "Velvet Room", "short": "VELVET", "color": "#ff786f"},
    "C": {"name": "Control", "short": "CONTROL", "color": "#a98cff"},
    "H": {"name": "Archive Hall", "short": "ARCHIVE", "color": "#61b8ff"},
    ".": {"name": "Connector", "short": "LINK", "color": "#7e8da1"},
}

DIRECTIONS: Dict[str, Coord] = {
    "north": (0, -1),
    "south": (0, 1),
    "west": (-1, 0),
    "east": (1, 0),
}

PLAYER_START: Coord = (2, 1)
RIVAL_START: Coord = (10, 1)
EXTRACTION: Coord = (6, 7)
SEARCH_SPOTS: List[Coord] = [
    (2, 2),
    (2, 3),
    (6, 1),
    (6, 2),
    (10, 2),
    (10, 3),
    (2, 5),
    (2, 6),
    (10, 5),
    (10, 6),
    (6, 5),
    (6, 6),
]

PAYLOADS: List[Payload] = [
    {"kind": "dossier", "label": "Prism dossier", "icon": "✦", "detail": "The encrypted file. Carry it to the extraction lift."},
    {"kind": "wire", "label": "Wire clip", "icon": "⌁", "detail": "Rig one floor trap to stun Rook."},
    {"kind": "smoke", "label": "Smoke capsule", "icon": "◌", "detail": "Blink two squares away from danger."},
    {"kind": "scanner", "label": "Signal scanner", "icon": "⌁", "detail": "Gain one remote scan and briefly reveal Rook."},
    {"kind": "decoy", "label": "Holo decoy", "icon": "◇", "detail": "Freeze Rook for one turn with a false body heat signature."},
    {"kind": "intel", "label": "Transit intel", "icon": "▱", "detail": "Boost your score and scramble Rook's alert."},
    {"kind": "empty", "label": "Cold cache", "icon": "·", "detail": "Dust, ozone, and nothing useful."},
    {"kind": "empty", "label": "False lead", "icon": "·", "detail": "A convincing detail planted to waste your time."},
    {"kind": "empty", "label": "Dead channel", "icon": "·", "detail": "No signal. Keep moving."},
    {"kind": "empty", "label": "Empty drawer", "icon": "·", "detail": "Someone got here before you."},
    {"kind": "empty", "label": "Cold cache", "icon": "·", "detail": "Nothing but a clean fingerprint."},
    {"kind": "empty", "label": "False lead", "icon": "·", "detail": "The room is lying to you."},
]


def escape(value: object) -> str:
    """Escape dynamic text before placing it in a custom HTML surface."""
    return html.escape(str(value), quote=True)


def tile_at(location: Coord) -> str:
    x, y = location
    if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT):
        return "#"
    return FACILITY_MAP[y][x]


def is_walkable(location: Coord) -> bool:
    return tile_at(location) != "#"


def room_name(location: Coord) -> str:
    return ROOMS.get(tile_at(location), {"name": "Unknown"})["name"]


def room_short(location: Coord) -> str:
    return ROOMS.get(tile_at(location), {"short": "UNKNOWN"})["short"]


def neighbors(location: Coord) -> List[Coord]:
    x, y = location
    result: List[Coord] = []
    for dx, dy in DIRECTIONS.values():
        destination = (x + dx, y + dy)
        if is_walkable(destination):
            result.append(destination)
    return result


def shortest_path(start: Coord, target: Coord) -> List[Coord]:
    """Return a shortest path excluding start and including target."""
    if start == target:
        return []
    queue: deque[Tuple[Coord, List[Coord]]] = deque([(start, [])])
    visited: Set[Coord] = {start}
    while queue:
        current, path = queue.popleft()
        for destination in neighbors(current):
            if destination in visited:
                continue
            next_path = [*path, destination]
            if destination == target:
                return next_path
            visited.add(destination)
            queue.append((destination, next_path))
    return []


def grid_distance(first: Coord, second: Coord) -> int:
    path = shortest_path(first, second)
    return len(path) if path else (0 if first == second else 99)


def format_location(location: Coord) -> str:
    return f"{room_name(location)} · {location[0] + 1},{location[1] + 1}"


def create_game() -> GameState:
    payloads: List[Payload] = [dict(payload) for payload in PAYLOADS]
    random.shuffle(payloads)
    hidden: Dict[Coord, Payload] = {
        location: payload for location, payload in zip(SEARCH_SPOTS, payloads)
    }
    dossier_location = next(
        location for location, payload in hidden.items() if payload["kind"] == "dossier"
    )
    return {
        "round": 1,
        "score": 0,
        "integrity": 3,
        "scans": 2,
        "player": PLAYER_START,
        "rival": RIVAL_START,
        "dossier_location": dossier_location,
        "hidden": hidden,
        "searched": set(),
        "rival_searched": set(),
        "inventory": [],
        "traps": {},
        "clues": [],
        "feed": [
            {"message": "Arena live. Find the Prism dossier and reach the extraction lift.", "tone": "system"},
            {"message": "You move first. Rook moves after every action.", "tone": "player"},
        ],
        "last_action": "Your move. Pick a direction or search the tile you occupy.",
        "player_history": [PLAYER_START],
        "rival_history": [RIVAL_START],
        "rival_last_seen": RIVAL_START,
        "player_last_seen": PLAYER_START,
        "rival_visible_until": 0,
        "rival_stunned": 0,
        "carrying": False,
        "game_over": False,
        "result": None,
    }


def ensure_game() -> GameState:
    if "game" not in st.session_state:
        st.session_state.game = create_game()
    return cast(GameState, st.session_state.game)


def add_feed(game: GameState, message: str, tone: str = "neutral") -> None:
    feed: List[Dict[str, str]] = game["feed"]
    game["feed"] = [{"message": message, "tone": tone}, *feed][:10]


def flash(game: GameState, message: str, tone: str = "neutral") -> None:
    game["last_action"] = message
    add_feed(game, message, tone)


def has_item(game: GameState, label: str) -> bool:
    return label in cast(List[str], game["inventory"])


def end_game(game: GameState, title: str, detail: str, won: bool) -> None:
    game["game_over"] = True
    game["result"] = {"title": title, "detail": detail, "won": won}
    flash(game, detail, "success" if won else "danger")


def update_visibility(game: GameState) -> None:
    player = cast(Coord, game["player"])
    rival = cast(Coord, game["rival"])
    if grid_distance(player, rival) <= 4 or game["round"] <= int(game["rival_visible_until"]):
        game["rival_last_seen"] = rival
        game["player_last_seen"] = player


def check_extraction(game: GameState) -> bool:
    if bool(game["carrying"]) and cast(Coord, game["player"]) == EXTRACTION:
        game["score"] += 100
        end_game(
            game,
            "Clean extraction",
            "The Prism dossier is out of the facility. Rook is left chasing a reflection.",
            True,
        )
        return True
    return False


def resolve_contact(game: GameState) -> None:
    """Make contact costly, but leave the player a route to recover."""
    game["integrity"] -= 1
    game["score"] = max(0, int(game["score"]) - 10)
    game["rival_stunned"] = 1
    flash(game, "ROOK CONTACT. Integrity -1. You forced him back through the corridor.", "danger")
    if int(game["integrity"]) <= 0:
        end_game(game, "Burned in the arena", "Rook boxed every exit. The operation is compromised.", False)
        return
    rival = cast(Coord, game["rival"])
    player = cast(Coord, game["player"])
    escape_tiles = [tile for tile in neighbors(rival) if tile != player]
    if escape_tiles:
        game["rival"] = max(escape_tiles, key=lambda tile: grid_distance(tile, player))


def resolve_rival_turn(game: GameState) -> None:
    """Give Rook one readable but dangerous AI move after the player's action."""
    if game["game_over"]:
        return
    if int(game["rival_stunned"]) > 0:
        game["rival_stunned"] = int(game["rival_stunned"]) - 1
        add_feed(game, "Rook is frozen by the false heat signature.", "success")
        return

    rival = cast(Coord, game["rival"])
    player = cast(Coord, game["player"])
    target = player if bool(game["carrying"]) else cast(Coord, game["dossier_location"])
    path = shortest_path(rival, target)
    candidates = neighbors(rival)
    if path:
        preferred = path[0]
        alternatives = [tile for tile in candidates if grid_distance(tile, target) == grid_distance(preferred, target)]
        destination = random.choice(alternatives or [preferred])
    elif candidates:
        destination = random.choice(candidates)
    else:
        destination = rival

    if destination in game["traps"]:
        game["traps"].pop(destination, None)
        game["rival"] = destination
        game["rival_stunned"] = 2
        game["score"] += 15
        flash(game, f"Rook hit your tripwire in {room_name(destination)}. He is stunned for two turns.", "success")
        return

    game["rival"] = destination
    game["rival_history"].append(destination)
    if grid_distance(cast(Coord, game["player"]), destination) <= 4:
        game["rival_last_seen"] = destination
        game["player_last_seen"] = cast(Coord, game["player"])
        add_feed(game, f"Rook signal: {room_short(destination)} / tile {destination[0] + 1},{destination[1] + 1}.", "rival")
    else:
        add_feed(game, f"Rook moved toward the dossier through {room_name(destination)}.", "rival")

    if destination == cast(Coord, game["player"]):
        resolve_contact(game)
        return
    if destination == cast(Coord, game["dossier_location"]) and not bool(game["carrying"]):
        end_game(
            game,
            "Rook secured the dossier",
            "He reached the hidden cache first. Reset the arena and change your route.",
            False,
        )


def finish_turn(game: GameState) -> None:
    if game["game_over"]:
        return
    resolve_rival_turn(game)
    if game["game_over"]:
        return
    update_visibility(game)
    game["round"] = int(game["round"]) + 1
    if check_extraction(game):
        return
    if int(game["round"]) > MAX_ROUNDS:
        end_game(
            game,
            "The arena sealed",
            "The extraction window closed before you could get the dossier out.",
            False,
        )


def move_player(game: GameState, direction: str) -> None:
    if game["game_over"]:
        return
    delta = DIRECTIONS[direction]
    current = cast(Coord, game["player"])
    destination = (current[0] + delta[0], current[1] + delta[1])
    if not is_walkable(destination):
        flash(game, "Wall ahead. Choose another route through the facility.", "warning")
        return
    game["player"] = destination
    game["player_history"].append(destination)
    game["score"] += 1
    update_visibility(game)
    if destination == cast(Coord, game["rival"]):
        resolve_contact(game)
        return
    if check_extraction(game):
        return
    flash(game, f"Moved {direction}. You are in {room_name(destination)}.", "player")
    finish_turn(game)


def search_current(game: GameState) -> None:
    if game["game_over"]:
        return
    location = cast(Coord, game["player"])
    if location in game["searched"]:
        flash(game, "That tile is already clear. Move to another cache marker.", "warning")
        return
    game["searched"].add(location)
    payload: Payload = game["hidden"].get(
        location,
        {"kind": "empty", "label": "Open floor", "icon": "·", "detail": "No cache here."},
    )
    kind = payload["kind"]
    if kind == "dossier":
        game["carrying"] = True
        game["score"] += 60
        flash(game, "DOSSIER FOUND. Reach the cyan extraction lift before Rook catches you.", "success")
        add_feed(game, "Objective changed: carry the dossier to EXTRACTION.", "objective")
        game["rival_visible_until"] = int(game["round"]) + 2
    elif kind == "empty":
        flash(game, f"Searched {room_name(location)}. {payload['label']} — keep moving.", "neutral")
    else:
        game["inventory"].append(payload["label"])
        game["score"] += 10
        flash(game, f"Recovered {payload['icon']} {payload['label']}.", "success")
        if kind == "scanner":
            game["scans"] += 1
        if kind == "intel":
            game["score"] += 10
            game["rival_visible_until"] = max(0, int(game["rival_visible_until"]) - 1)
            add_feed(game, "Transit intel scrambled Rook's route and boosted your score.", "success")
    finish_turn(game)


def scan_area(game: GameState) -> None:
    if game["game_over"] or int(game["scans"]) <= 0:
        return
    game["scans"] = int(game["scans"]) - 1
    current = cast(Coord, game["player"])
    unsearched = [spot for spot in SEARCH_SPOTS if spot not in game["searched"]]
    nearest = min(unsearched, key=lambda spot: grid_distance(current, spot), default=None)
    game["rival_visible_until"] = int(game["round"]) + 3
    if nearest is not None:
        game["clues"].insert(0, f"SCAN: strongest cache signal at {room_short(nearest)} / tile {nearest[0] + 1},{nearest[1] + 1}.")
        flash(game, f"Scan complete. Cache signal strongest in {room_name(nearest)}.", "success")
    else:
        flash(game, "Scan complete. Every cache has already been cleared.", "warning")
    finish_turn(game)


def rig_trap(game: GameState) -> None:
    if game["game_over"] or not has_item(game, "Wire clip"):
        return
    location = cast(Coord, game["player"])
    if location == EXTRACTION or location in game["traps"]:
        flash(game, "This tile cannot take another trap.", "warning")
        return
    game["inventory"].remove("Wire clip")
    game["traps"][location] = "player"
    game["score"] += 5
    flash(game, f"Tripwire armed in {room_name(location)}. Let Rook do the walking.", "success")
    finish_turn(game)


def use_smoke(game: GameState) -> None:
    if game["game_over"] or not has_item(game, "Smoke capsule"):
        return
    current = cast(Coord, game["player"])
    rival = cast(Coord, game["rival"])
    first_steps = [tile for tile in neighbors(current) if tile != rival]
    if not first_steps:
        flash(game, "No clear smoke route from this tile.", "warning")
        return
    destination = max(first_steps, key=lambda tile: grid_distance(tile, rival))
    second_steps = [tile for tile in neighbors(destination) if tile != rival]
    if second_steps:
        destination = max(second_steps, key=lambda tile: grid_distance(tile, rival))
    game["inventory"].remove("Smoke capsule")
    game["player"] = destination
    game["player_history"].append(destination)
    game["score"] += 8
    game["rival_visible_until"] = int(game["round"]) + 1
    flash(game, f"Smoke escape: you blinked to {room_name(destination)}.", "success")
    finish_turn(game)


def use_decoy(game: GameState) -> None:
    if game["game_over"] or not has_item(game, "Holo decoy"):
        return
    game["inventory"].remove("Holo decoy")
    game["rival_stunned"] = 1
    game["score"] += 7
    flash(game, "Holo decoy deployed. Rook is chasing a false body heat signature.", "success")
    finish_turn(game)


def reset_game() -> None:
    st.session_state.game = create_game()


def render_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;600;700;800&display=swap');
        :root { --bg:#080b12; --panel:#111825; --line:rgba(198,218,238,.15); --text:#f4f7fb; --muted:#8592a5; --cyan:#4be0ae; --red:#ff786f; --gold:#ffd166; --blue:#61b8ff; }
        .stApp { background:radial-gradient(circle at 10% -10%,rgba(75,224,174,.12),transparent 28rem),radial-gradient(circle at 100% 0%,rgba(255,120,111,.1),transparent 25rem),linear-gradient(145deg,#080b12,#0e1420 55%,#090d16); color:var(--text); font-family:'Manrope',system-ui,sans-serif; }
        [data-testid="stHeader"] { background:transparent; } [data-testid="stToolbar"] { visibility:hidden; }
        .block-container { max-width:1480px; padding:1.6rem 2.4rem 4rem; }
        div[data-testid="stSidebar"] { background:rgba(6,9,16,.9); border-right:1px solid var(--line); } div[data-testid="stSidebar"] .block-container { padding:1.5rem 1rem; }
        .topbar { display:flex; justify-content:space-between; align-items:center; gap:1rem; margin-bottom:1.1rem; }
        .brand { display:flex; align-items:center; gap:.7rem; } .brand-mark { width:42px; height:42px; display:grid; place-items:center; border-radius:14px; color:#061712; font-weight:800; font-size:1.25rem; background:linear-gradient(135deg,#4be0ae,#b1ffe4); box-shadow:0 0 30px rgba(75,224,174,.22); }
        .brand-name { color:#f6fafc; text-transform:uppercase; letter-spacing:.16em; font-weight:800; font-size:.9rem; } .brand-sub { color:#76859a; font:500 .61rem 'DM Mono',monospace; letter-spacing:.11em; margin-top:.18rem; }
        .live-pill { color:#a9f5dc; border:1px solid rgba(75,224,174,.3); background:rgba(75,224,174,.07); padding:.55rem .75rem; border-radius:99px; font:500 .6rem 'DM Mono',monospace; letter-spacing:.1em; } .live-dot { display:inline-block; width:7px; height:7px; background:var(--cyan); border-radius:50%; margin-right:.42rem; box-shadow:0 0 12px var(--cyan); }
        .hero { border-top:1px solid var(--line); border-bottom:1px solid var(--line); padding:1.1rem 0 1.25rem; display:flex; align-items:flex-end; justify-content:space-between; gap:2rem; } .kicker,.eyebrow { color:var(--cyan); font:500 .63rem 'DM Mono',monospace; letter-spacing:.15em; text-transform:uppercase; } .hero h1 { font-size:clamp(2.6rem,6vw,5.7rem); line-height:.9; letter-spacing:-.08em; margin:.55rem 0 0; font-weight:800; } .hero h1 span { color:var(--red); } .hero-copy { color:#9aa7b8; max-width:34rem; font-size:.85rem; line-height:1.65; margin:0; }
        .metrics { display:grid; grid-template-columns:repeat(5,1fr); gap:.65rem; margin:1rem 0; } .metric { position:relative; overflow:hidden; min-height:70px; border:1px solid var(--line); border-radius:15px; background:rgba(17,24,37,.82); padding:.75rem .85rem; } .metric:after { content:''; position:absolute; width:85px; height:85px; right:-36px; top:-42px; border:1px solid rgba(75,224,174,.15); border-radius:50%; } .metric-label { color:#708096; font:500 .56rem 'DM Mono',monospace; text-transform:uppercase; letter-spacing:.1em; } .metric-value { color:#f7fafc; font-size:1.45rem; letter-spacing:-.05em; font-weight:800; margin-top:.2rem; } .cyan { color:var(--cyan); } .red { color:var(--red); } .gold { color:var(--gold); }
        .notice { color:#c9f8eb; background:rgba(75,224,174,.08); border:1px solid rgba(75,224,174,.26); border-radius:12px; padding:.75rem .9rem; font-size:.76rem; margin:.8rem 0; } .notice.warning { color:#ffe9a8; background:rgba(255,209,102,.08); border-color:rgba(255,209,102,.28); } .notice.danger { color:#ffd0cb; background:rgba(255,120,111,.09); border-color:rgba(255,120,111,.3); }
        .section-head { display:flex; justify-content:space-between; align-items:flex-end; gap:1rem; margin:1.1rem 0 .55rem; } .section-title { color:#f4f8fb; font-size:1.15rem; letter-spacing:-.04em; font-weight:800; } .section-meta { color:#718096; font:500 .59rem 'DM Mono',monospace; text-transform:uppercase; letter-spacing:.1em; }
        .arena-shell { border:1px solid rgba(75,224,174,.24); border-radius:22px; background:linear-gradient(145deg,rgba(17,30,43,.96),rgba(9,14,23,.96)); padding:.8rem; box-shadow:0 25px 65px rgba(0,0,0,.24), inset 0 1px rgba(255,255,255,.04); }
        .arena-top { display:flex; justify-content:space-between; align-items:center; gap:.7rem; padding:.2rem .35rem .75rem; } .arena-label { color:#aaf6df; font:500 .61rem 'DM Mono',monospace; letter-spacing:.13em; } .arena-state { color:#708199; font:500 .58rem 'DM Mono',monospace; letter-spacing:.08em; }
        .map-grid { display:grid; grid-template-columns:repeat(13,minmax(26px,1fr)); gap:3px; width:100%; aspect-ratio:13/9; background:#05080e; padding:4px; border-radius:16px; border:1px solid rgba(198,218,238,.12); }
        .map-tile { position:relative; min-width:0; min-height:0; border-radius:5px; display:flex; align-items:center; justify-content:center; overflow:hidden; color:#748398; font:500 .43rem 'DM Mono',monospace; } .map-tile.wall { background:#070a10; border:1px solid rgba(198,218,238,.045); } .map-tile.corridor { background:rgba(116,132,157,.11); border:1px solid rgba(198,218,238,.08); } .map-tile.room-g { background:rgba(75,224,174,.14); border:1px solid rgba(75,224,174,.18); } .map-tile.room-o { background:rgba(255,209,102,.13); border:1px solid rgba(255,209,102,.18); } .map-tile.room-v { background:rgba(255,120,111,.13); border:1px solid rgba(255,120,111,.18); } .map-tile.room-c { background:rgba(169,140,255,.13); border:1px solid rgba(169,140,255,.19); } .map-tile.room-h { background:rgba(97,184,255,.13); border:1px solid rgba(97,184,255,.18); } .map-tile.extraction { background:rgba(75,224,174,.32); border:1px solid rgba(75,224,174,.8); box-shadow:0 0 14px rgba(75,224,174,.22); }
        .tile-room-code { position:absolute; top:3px; left:4px; opacity:.58; font-size:.37rem; } .tile-marker { color:#c4d0dd; font-size:.75rem; line-height:1; } .tile-marker.cache { color:#ffd166; text-shadow:0 0 10px rgba(255,209,102,.9); animation:pulse 1.7s ease-in-out infinite; } .tile-marker.revealed { color:#fff1b8; } .tile-marker.exit { color:#d4fff0; font-size:.48rem; font-weight:700; } .tile-marker.trap { color:#ff786f; }
        .token { z-index:2; display:grid; place-items:center; min-width:38px; height:25px; padding:0 .3rem; border-radius:7px; font-size:.43rem; font-weight:800; letter-spacing:.04em; } .token.you { color:#041812; background:var(--cyan); box-shadow:0 0 16px rgba(75,224,174,.8); } .token.rook { color:#260d12; background:var(--red); box-shadow:0 0 16px rgba(255,120,111,.7); } .token.both { background:linear-gradient(90deg,var(--cyan),var(--red)); color:#140b0c; } .token.ghost { opacity:.38; border:1px dashed #a9b8c9; color:#bac8d5; background:rgba(145,162,184,.2); box-shadow:none; }
        .arena-legend { display:flex; align-items:center; flex-wrap:wrap; gap:.8rem; padding:.7rem .3rem .1rem; color:#718096; font:500 .55rem 'DM Mono',monospace; } .legend-item { display:inline-flex; align-items:center; gap:.3rem; } .legend-swatch { width:9px; height:9px; border-radius:3px; } .legend-swatch.you { background:var(--cyan); } .legend-swatch.rook { background:var(--red); } .legend-swatch.cache { background:var(--gold); } .legend-swatch.exit { background:#aaf6df; }
        .control-card,.info-card,.screen-card { border:1px solid var(--line); border-radius:18px; background:rgba(17,24,37,.83); padding:1rem; margin-top:.8rem; } .control-card { background:linear-gradient(145deg,rgba(19,38,46,.92),rgba(13,21,31,.9)); } .card-head { display:flex; justify-content:space-between; align-items:center; gap:.6rem; margin-bottom:.75rem; } .card-title { color:#eff7f8; font-weight:800; font-size:.87rem; } .card-tag { color:#7b8ca1; font:500 .55rem 'DM Mono',monospace; letter-spacing:.1em; text-transform:uppercase; }
        .current-tile { border:1px solid rgba(75,224,174,.22); border-radius:11px; background:rgba(75,224,174,.055); color:#a8f2dc; padding:.6rem .7rem; font:500 .65rem 'DM Mono',monospace; line-height:1.5; margin-bottom:.75rem; } .current-tile strong { color:#effff9; font-size:.72rem; }
        .movement-caption { color:#718096; font:500 .55rem 'DM Mono',monospace; letter-spacing:.12em; text-align:center; text-transform:uppercase; margin:.55rem 0 .35rem; } .move-row { display:grid; grid-template-columns:repeat(3,1fr); gap:.4rem; margin-bottom:.4rem; }
        .loadout { display:flex; gap:.38rem; flex-wrap:wrap; } .loadout-chip { color:#cdd9e5; border:1px solid rgba(198,218,238,.15); background:rgba(198,218,238,.06); border-radius:8px; padding:.4rem .5rem; font:500 .56rem 'DM Mono',monospace; } .loadout-chip.hot { color:#061a14; background:var(--cyan); border-color:var(--cyan); }
        .progress-track { height:7px; border-radius:99px; background:rgba(198,218,238,.1); overflow:hidden; margin-top:.55rem; } .progress-fill { height:100%; border-radius:99px; background:linear-gradient(90deg,var(--red),var(--gold)); }
        .feed-item { display:flex; gap:.5rem; padding:.55rem 0; border-bottom:1px solid rgba(198,218,238,.08); } .feed-item:last-child { border-bottom:0; } .feed-dot { flex:0 0 auto; width:6px; height:6px; border-radius:50%; margin-top:.32rem; background:#78889c; } .feed-dot.success { background:var(--cyan); box-shadow:0 0 9px var(--cyan); } .feed-dot.danger { background:var(--red); box-shadow:0 0 9px var(--red); } .feed-dot.rival { background:var(--gold); } .feed-dot.player { background:var(--blue); } .feed-message { color:#a5b2c1; font-size:.66rem; line-height:1.45; }
        .screens-head { display:flex; justify-content:space-between; gap:1rem; align-items:flex-end; margin-top:1.4rem; } .screens-copy { color:#7f8da1; font-size:.69rem; line-height:1.4; max-width:31rem; text-align:right; } .screen-card { margin-top:.65rem; padding:.75rem; } .screen-card.you-screen { border-color:rgba(75,224,174,.25); } .screen-card.rook-screen { border-color:rgba(255,120,111,.25); } .screen-heading { display:flex; justify-content:space-between; gap:.6rem; margin-bottom:.55rem; } .screen-heading strong { color:#dffaf1; font:500 .6rem 'DM Mono',monospace; letter-spacing:.12em; } .rook-screen .screen-heading strong { color:#ffd0cb; } .screen-heading span { color:#728198; font:500 .53rem 'DM Mono',monospace; text-transform:uppercase; }
        .result { border:1px solid rgba(75,224,174,.4); background:linear-gradient(135deg,rgba(75,224,174,.15),rgba(17,28,39,.85)); border-radius:18px; padding:1.1rem 1.2rem; margin:.9rem 0; } .result.loss { border-color:rgba(255,120,111,.4); background:linear-gradient(135deg,rgba(255,120,111,.14),rgba(35,23,33,.85)); } .result-kicker { color:var(--cyan); font:500 .61rem 'DM Mono',monospace; letter-spacing:.13em; } .result.loss .result-kicker { color:var(--red); } .result-title { color:#f7fbfc; font-weight:800; font-size:1.4rem; letter-spacing:-.05em; margin:.25rem 0; } .result-detail { color:#a9b6c5; font-size:.74rem; line-height:1.5; }
        .footer { color:#526278; text-align:center; padding:1.3rem 0 0; font:500 .55rem 'DM Mono',monospace; letter-spacing:.12em; }
        .stButton > button { min-height:40px; border-radius:10px; border:1px solid rgba(198,218,238,.18); background:rgba(126,145,170,.08); color:#dce7ef; font:500 .58rem 'DM Mono',monospace; letter-spacing:.06em; transition:.16s ease; } .stButton > button:hover { color:#bcf8e6; border-color:rgba(75,224,174,.65); background:rgba(75,224,174,.11); transform:translateY(-1px); } .control-card .stButton > button { border-color:rgba(75,224,174,.25); background:rgba(75,224,174,.08); } .stButton > button:disabled { opacity:.35; transform:none; }
        @keyframes pulse { 0%,100% { opacity:.55; transform:scale(.9); } 50% { opacity:1; transform:scale(1.15); } }
        @media (max-width:900px) { .block-container { padding:1rem .8rem 3rem; } .hero { display:block; } .hero-copy { margin-top:1rem; } .metrics { grid-template-columns:repeat(2,1fr); } .metrics .metric:last-child { grid-column:span 2; } .screens-copy { text-align:left; margin-top:.5rem; } .screens-head { display:block; } .map-grid { gap:2px; padding:3px; } .token { min-width:28px; height:20px; font-size:.34rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def tile_class(location: Coord) -> str:
    tile = tile_at(location)
    if location == EXTRACTION:
        return "map-tile extraction"
    if tile == "#":
        return "map-tile wall"
    if tile == ".":
        return "map-tile corridor"
    return f"map-tile room-{tile.lower()}"


def tile_marker(game: GameState, location: Coord, perspective: str) -> str:
    player = cast(Coord, game["player"])
    rival = cast(Coord, game["rival"])
    show_player = perspective == "arena" or perspective == "rival" or location == player
    show_rival = perspective == "arena" or perspective == "player" or location == rival
    rival_visible = (
        perspective == "arena"
        or perspective == "player" and (int(game["round"]) <= int(game["rival_visible_until"]) or location == cast(Coord, game["rival_last_seen"]))
        or perspective == "rival" and location == rival
    )
    player_visible = perspective == "arena" or perspective == "rival" and (
        grid_distance(player, rival) <= 4 or int(game["round"]) <= int(game["rival_visible_until"])
    )
    tokens: List[str] = []
    if location == player and show_player and (perspective != "rival" or player_visible):
        tokens.append("<span class='token you'>YOU</span>")
    if location == rival and show_rival and rival_visible:
        tokens.append("<span class='token rook'>ROOK</span>")
    if location == player and location == rival:
        return "<span class='token both'>CONTACT</span>"
    if perspective == "player" and location == cast(Coord, game["rival_last_seen"]) and not rival_visible:
        tokens.append("<span class='token ghost'>SIGNAL</span>")
    if perspective == "rival" and location == cast(Coord, game["player_last_seen"]) and not player_visible:
        tokens.append("<span class='token ghost'>LAST</span>")
    return "".join(tokens)


def render_board(game: GameState, perspective: str = "arena") -> str:
    cells: List[str] = []
    searched = cast(Set[Coord], game["searched"])
    traps = cast(Dict[Coord, str], game["traps"])
    revealed = cast(Set[Coord], game.get("revealed", set()))
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            location = (x, y)
            tile = tile_at(location)
            if tile == "#":
                cells.append("<div class='map-tile wall'></div>")
                continue
            code = escape(tile if tile != "." else "·")
            marker = ""
            if location == EXTRACTION:
                marker = "<span class='tile-marker exit'>EXIT</span>"
            elif location in traps:
                marker = "<span class='tile-marker trap'>△</span>"
            elif location in SEARCH_SPOTS and location not in searched:
                marker_class = "revealed" if location in revealed else "cache"
                marker = f"<span class='tile-marker {marker_class}'>◆</span>"
            else:
                marker = "<span class='tile-marker'>·</span>"
            tokens = tile_marker(game, location, perspective)
            cells.append(
                f"<div class='{tile_class(location)}'><span class='tile-room-code'>{code}</span>{marker}{tokens}</div>"
            )
    return f"<div class='map-grid'>{''.join(cells)}</div>"


def render_metrics(game: GameState) -> None:
    integrity = int(game["integrity"])
    health = "●" * integrity + "○" * (3 - integrity)
    objective = "EXTRACT" if bool(game["carrying"]) else "LOCATE"
    st.markdown(
        f"""
        <div class='metrics'>
            <div class='metric'><div class='metric-label'>Turn</div><div class='metric-value cyan'>{int(game['round']):02d}<span style='font-size:.7rem;color:#75849a;'> / {MAX_ROUNDS:02d}</span></div></div>
            <div class='metric'><div class='metric-label'>Score</div><div class='metric-value gold'>{int(game['score']):03d}</div></div>
            <div class='metric'><div class='metric-label'>Integrity</div><div class='metric-value red' style='font-size:1.05rem;letter-spacing:.09em;'>{health}</div></div>
            <div class='metric'><div class='metric-label'>Scans</div><div class='metric-value'>{int(game['scans'])}</div></div>
            <div class='metric'><div class='metric-label'>Objective</div><div class='metric-value cyan' style='font-size:1.05rem;'>{objective}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_event(game: GameState) -> None:
    message = str(game["last_action"])
    tone = ""
    lowered = message.lower()
    if "contact" in lowered or "integrity" in lowered or "rook secured" in lowered:
        tone = "danger"
    elif "wall" in lowered or "already" in lowered or "cannot" in lowered:
        tone = "warning"
    st.markdown(f"<div class='notice {tone}'><strong>FIELD EVENT</strong>&nbsp;&nbsp; {escape(message)}</div>", unsafe_allow_html=True)


def render_arena(game: GameState) -> None:
    player = cast(Coord, game["player"])
    rival = cast(Coord, game["rival"])
    st.markdown(
        f"""
        <div class='section-head'><div><div class='eyebrow'>Top-down arena</div><div class='section-title'>The safehouse is live.</div></div><div class='section-meta'>{room_short(player)} / YOU {player[0] + 1},{player[1] + 1}</div></div>
        <div class='arena-shell'>
            <div class='arena-top'><div class='arena-label'>LIVE FLOOR PLAN · ALL MOVEMENT IS TURN-BASED</div><div class='arena-state'>ROOK {rival[0] + 1},{rival[1] + 1}</div></div>
            {render_board(game, 'arena')}
            <div class='arena-legend'><span class='legend-item'><span class='legend-swatch you'></span>YOU</span><span class='legend-item'><span class='legend-swatch rook'></span>ROOK</span><span class='legend-item'><span class='legend-swatch cache'></span>SEARCH CACHE</span><span class='legend-item'><span class='legend-swatch exit'></span>EXTRACTION</span><span class='legend-item' style='margin-left:auto;'>◆ SEARCH · △ TRAP · EXIT = {EXTRACTION[0] + 1},{EXTRACTION[1] + 1}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def action_rerun(action: Any, game: GameState) -> None:
    action(game)
    st.rerun()


def render_controls(game: GameState) -> None:
    player = cast(Coord, game["player"])
    current_payload = cast(Dict[Coord, Payload], game["hidden"]).get(player)
    if current_payload and player not in game["searched"]:
        tile_state = f"<strong>◆ CACHE SIGNAL</strong><br>{escape(current_payload['detail'])}"
    elif player == EXTRACTION:
        tile_state = "<strong>EXTRACTION LIFT</strong><br>Reach this tile while carrying the Prism dossier."
    else:
        tile_state = f"<strong>{escape(room_name(player).upper())}</strong><br>Tile {player[0] + 1},{player[1] + 1} · Search for hidden caches."
    wire_ready = has_item(game, "Wire clip")
    smoke_ready = has_item(game, "Smoke capsule")
    decoy_ready = has_item(game, "Holo decoy")
    st.markdown(
        f"""
        <div class='control-card'>
            <div class='card-head'><div class='card-title'>Your controls</div><div class='card-tag'>one action = one rook response</div></div>
            <div class='current-tile'>{tile_state}</div>
            <div class='movement-caption'>Move your operative</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    disabled = bool(game["game_over"])
    top_left, top_mid, top_right = st.columns(3)
    with top_mid:
        if st.button("NORTH  ↑", key="move_north", use_container_width=True, disabled=disabled or not is_walkable((player[0], player[1] - 1))):
            action_rerun(lambda current: move_player(current, "north"), game)
    left, center, right = st.columns(3)
    with left:
        if st.button("WEST  ←", key="move_west", use_container_width=True, disabled=disabled or not is_walkable((player[0] - 1, player[1]))):
            action_rerun(lambda current: move_player(current, "west"), game)
    with center:
        if st.button("SEARCH  ◆", key="search_current", use_container_width=True, disabled=disabled or player in game["searched"]):
            action_rerun(search_current, game)
    with right:
        if st.button("EAST  →", key="move_east", use_container_width=True, disabled=disabled or not is_walkable((player[0] + 1, player[1]))):
            action_rerun(lambda current: move_player(current, "east"), game)
    _, bottom_mid, _ = st.columns(3)
    with bottom_mid:
        if st.button("SOUTH  ↓", key="move_south", use_container_width=True, disabled=disabled or not is_walkable((player[0], player[1] + 1))):
            action_rerun(lambda current: move_player(current, "south"), game)
    st.markdown("<div class='movement-caption' style='margin-top:.8rem;'>Gadgets and intel</div>", unsafe_allow_html=True)
    gadget_columns = st.columns(4)
    with gadget_columns[0]:
        if st.button(f"SCAN  [{int(game['scans'])}]", key="scan_area", use_container_width=True, disabled=disabled or int(game["scans"]) <= 0):
            action_rerun(scan_area, game)
    with gadget_columns[1]:
        if st.button("TRIPWIRE", key="rig_trap", use_container_width=True, disabled=disabled or not wire_ready):
            action_rerun(rig_trap, game)
    with gadget_columns[2]:
        if st.button("SMOKE", key="use_smoke", use_container_width=True, disabled=disabled or not smoke_ready):
            action_rerun(use_smoke, game)
    with gadget_columns[3]:
        if st.button("DECOY", key="use_decoy", use_container_width=True, disabled=disabled or not decoy_ready):
            action_rerun(use_decoy, game)


def render_status(game: GameState) -> None:
    player = cast(Coord, game["player"])
    rival = cast(Coord, game["rival"])
    distance = grid_distance(player, rival)
    progress = max(5, min(95, 100 - grid_distance(rival, cast(Coord, game["dossier_location"])) * 7))
    objective_text = "CARRY TO EXTRACTION" if bool(game["carrying"]) else "FIND THE DOSSIER"
    inventory = cast(List[str], game["inventory"])
    chips = "".join(
        f"<span class='loadout-chip'>{escape(item)}</span>" for item in inventory
    ) or "<span style=\"color:#718096;font:500 .58rem 'DM Mono',monospace;\">EMPTY LOADOUT</span>"
    st.markdown(
        f"""
        <div class='info-card'>
            <div class='card-head'><div class='card-title'>Mission status</div><div class='card-tag'>{objective_text}</div></div>
            <div style='color:#9eabba;font-size:.7rem;line-height:1.5;'>Extraction lift: <strong style='color:#dffaf1;'>tile {EXTRACTION[0] + 1},{EXTRACTION[1] + 1}</strong><br>Current position: <strong style='color:#dffaf1;'>{escape(format_location(player))}</strong></div>
            <div style='display:flex;justify-content:space-between;margin-top:.9rem;color:#7b8ba0;font:500 .55rem "DM Mono",monospace;'><span>ROOK HUNT SIGNAL</span><span>{progress}%</span></div>
            <div class='progress-track'><div class='progress-fill' style='width:{progress}%;'></div></div>
            <div style='color:#8d9bae;font-size:.68rem;line-height:1.5;margin-top:.75rem;'>Rook is <strong style='color:#ffd166;'>{distance} steps</strong> from your position. {"He has your trail." if distance <= 4 else "Your trail is currently cold."}</div>
        </div>
        <div class='info-card'>
            <div class='card-head'><div class='card-title'>Loadout</div><div class='card-tag'>{len(inventory)} recovered</div></div>
            <div class='loadout'>{chips}</div>
            {"<div class='loadout' style='margin-top:.4rem;'><span class='loadout-chip hot'>PRISM DOSSIER</span></div>" if game['carrying'] else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_feed(game: GameState) -> None:
    items = cast(List[Dict[str, str]], game["feed"])
    feed_markup = "".join(
        f"<div class='feed-item'><span class='feed-dot {escape(item['tone'])}'></span><span class='feed-message'>{escape(item['message'])}</span></div>"
        for item in items[:7]
    )
    st.markdown(
        f"<div class='info-card'><div class='card-head'><div class='card-title'>Live event feed</div><div class='card-tag'>encrypted</div></div>{feed_markup}</div>",
        unsafe_allow_html=True,
    )


def render_double_screen(game: GameState) -> None:
    st.markdown(
        """
        <div class='screens-head'><div><div class='eyebrow'>Two-screen duel</div><div class='section-title'>Your view vs. Rook's view.</div></div><div class='screens-copy'>The arena above shows the truth. These two smaller screens show what each operative can currently see.</div></div>
        """,
        unsafe_allow_html=True,
    )
    player = cast(Coord, game["player"])
    rival = cast(Coord, game["rival"])
    left, right = st.columns(2, gap="medium")
    with left:
        rival_known = int(game["round"]) <= int(game["rival_visible_until"]) or grid_distance(player, rival) <= 4
        st.markdown(
            f"<div class='screen-card you-screen'><div class='screen-heading'><strong>YOUR SCREEN / FIELD VIEW</strong><span>{'ROOK VISIBLE' if rival_known else 'SIGNAL LOST'}</span></div>{render_board(game, 'player')}</div>",
            unsafe_allow_html=True,
        )
    with right:
        player_known = grid_distance(player, rival) <= 4 or int(game["round"]) <= int(game["rival_visible_until"])
        st.markdown(
            f"<div class='screen-card rook-screen'><div class='screen-heading'><strong>ROOK / OPPONENT VIEW</strong><span>{'YOUR TRAIL HOT' if player_known else 'TRAIL COLD'}</span></div>{render_board(game, 'rival')}</div>",
            unsafe_allow_html=True,
        )


def render_result(game: GameState) -> None:
    result: Optional[Dict[str, Any]] = game.get("result")
    if not result:
        return
    result_class = "" if bool(result["won"]) else " loss"
    kicker = "OPERATION COMPLETE" if bool(result["won"]) else "OPERATION LOST"
    st.markdown(
        f"<div class='result{result_class}'><div class='result-kicker'>{kicker}</div><div class='result-title'>{escape(result['title'])}</div><div class='result-detail'>{escape(result['detail'])}</div></div>",
        unsafe_allow_html=True,
    )
    if st.button("RESET ARENA", key="reset_result", use_container_width=True):
        reset_game()
        st.rerun()


def render_sidebar(game: GameState) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class='brand' style='margin-bottom:1.1rem;'><div class='brand-mark' style='width:36px;height:36px;border-radius:11px;font-size:1rem;'>◈</div><div><div class='brand-name' style='font-size:.72rem;'>CIPHER CLASH</div><div class='brand-sub'>FIELD MANUAL / 02</div></div></div>
            <div class='eyebrow'>How to play</div>
            <div style='color:#9aa7b8;font-size:.72rem;line-height:1.7;margin-top:.45rem;'>Move one tile at a time with the directional pad. Search the glowing ◆ caches. Rook takes his own turn after every action.</div>
            <div style='height:1px;background:rgba(198,218,238,.14);margin:1rem 0;'></div>
            <div class='eyebrow'>Win condition</div>
            <div style='color:#d8e5ed;font-size:.72rem;line-height:1.65;margin-top:.45rem;'>Find the Prism dossier, then walk it to the cyan EXIT tile. Three contact hits or a 24-turn clock ends the operation.</div>
            <div style='height:1px;background:rgba(198,218,238,.14);margin:1rem 0;'></div>
            <div class='eyebrow'>Map legend</div>
            <div style='color:#9aa7b8;font-size:.7rem;line-height:1.8;margin-top:.45rem;'>◆ cache &nbsp; △ tripwire<br>YOU = cyan &nbsp; ROOK = red<br>Letters identify each wing.</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
        if st.button("RESET OPERATION", key="reset_sidebar", use_container_width=True):
            reset_game()
            st.rerun()


def main() -> None:
    st.set_page_config(page_title=APP_NAME, page_icon="◈", layout="wide", initial_sidebar_state="expanded")
    render_styles()
    game = ensure_game()
    render_sidebar(game)
    st.markdown(
        """
        <div class='topbar'><div class='brand'><div class='brand-mark'>◈</div><div><div class='brand-name'>Cipher Clash</div><div class='brand-sub'>A turn-based safehouse duel</div></div></div><div class='live-pill'><span class='live-dot'></span>ARENA LIVE / 24 TURN WINDOW</div></div>
        <div class='hero'><div><div class='kicker'>Operation 02 · Prism Relay</div><h1>Move smart.<br><span>Stay unseen.</span></h1></div><p class='hero-copy'>A real playable top-down duel: navigate the safehouse, search caches, deploy gadgets, and beat the rival agent to the extraction lift.</p></div>
        """,
        unsafe_allow_html=True,
    )
    if game["game_over"]:
        render_result(game)
    else:
        render_event(game)
    render_metrics(game)
    left, right = st.columns([1.65, 1], gap="large")
    with left:
        render_arena(game)
        render_controls(game)
    with right:
        render_status(game)
        render_feed(game)
    render_double_screen(game)
    st.markdown("<div class='footer'>CIPHER CLASH · ORIGINAL SPY-FI ARENA · MAKE THE NEXT MOVE COUNT</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
