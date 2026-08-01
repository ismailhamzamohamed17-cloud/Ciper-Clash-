from __future__ import annotations

import html
import random
from typing import Any, Dict, List, Optional, Set, Tuple, cast

import streamlit as st


Location = Tuple[str, str]
Payload = Dict[str, str]
GameState = Dict[str, Any]

MAX_ROUNDS = 12

ROOMS: Dict[str, Dict[str, Any]] = {
    "Glasshouse": {
        "eyebrow": "01 / SOUTH WING",
        "subtitle": "orchids, mirrors, warm air",
        "description": "A humid conservatory built around a black-water fountain. Every surface reflects twice.",
        "accent": "#50e3bb",
        "accent_soft": "rgba(80, 227, 187, .13)",
        "icon": "✦",
        "spots": [
            {"name": "Orchid bench", "detail": "A lacquered bench beneath a bank of grow lights."},
            {"name": "Mirror plinth", "detail": "A polished plinth displaying a tiny brass compass."},
            {"name": "Service hatch", "detail": "A narrow hatch hidden behind a curtain of fern."},
        ],
    },
    "Velvet Room": {
        "eyebrow": "02 / WEST WING",
        "subtitle": "records, velvet, red light",
        "description": "A listening room with a velvet banquette and a record console still humming at 33 RPM.",
        "accent": "#ff756c",
        "accent_soft": "rgba(255, 117, 108, .13)",
        "icon": "◈",
        "spots": [
            {"name": "Record console", "detail": "A walnut console with a needle frozen above a vinyl groove."},
            {"name": "Drinks cabinet", "detail": "Cut crystal, tonic, and one bottle with the label peeled away."},
            {"name": "Velvet banquette", "detail": "Deep cushions with a suspiciously sharp seam."},
        ],
    },
    "Observatory": {
        "eyebrow": "03 / NORTH WING",
        "subtitle": "rain, brass, city lights",
        "description": "An octagonal room under a glass dome. The storm outside makes every signal flicker.",
        "accent": "#ffd166",
        "accent_soft": "rgba(255, 209, 102, .13)",
        "icon": "⌁",
        "spots": [
            {"name": "Telescope mount", "detail": "A brass mount aimed at a skyline that is not on any map."},
            {"name": "Map table", "detail": "A city map pinned beneath a clear sheet of glass."},
            {"name": "Weather console", "detail": "A quiet console pulsing with one amber warning light."},
        ],
    },
}

ITEMS: List[Payload] = [
    {
        "kind": "dossier",
        "label": "Prism dossier",
        "icon": "✦",
        "detail": "The target file. Get it to the extraction lift before Rook does.",
    },
    {
        "kind": "wire",
        "label": "Wire clip",
        "icon": "⌁",
        "detail": "A ceramic snip tool. Disarms one rival tripwire or rigs one of your own.",
    },
    {
        "kind": "smoke",
        "label": "Smoke capsule",
        "icon": "◌",
        "detail": "A palm-sized escape cloud. The first bad search costs less integrity.",
    },
    {
        "kind": "booster",
        "label": "Signal booster",
        "icon": "⌁",
        "detail": "One burst of clean intel. Adds a second scan to your loadout.",
    },
    {
        "kind": "decoy",
        "label": "Mirror decoy",
        "icon": "◇",
        "detail": "A false reflection that can draw Rook into a trap.",
    },
    {
        "kind": "intel",
        "label": "Transit note",
        "icon": "▱",
        "detail": "A fragment of the extraction route. Worth a little momentum.",
    },
]


def escape(value: str) -> str:
    """Escape text before placing it inside a custom HTML surface."""
    return html.escape(value, quote=True)


def all_locations() -> List[Location]:
    return [
        (room_name, spot["name"])
        for room_name, room in ROOMS.items()
        for spot in room["spots"]
    ]


def create_game() -> GameState:
    locations = all_locations()
    payloads: List[Payload] = [dict(item) for item in ITEMS]
    payloads.extend(
        [
            {"kind": "empty", "label": "Clean air", "icon": "·", "detail": "Nothing but dust and a faint trace of ozone."},
            {"kind": "empty", "label": "False lead", "icon": "·", "detail": "A convincing detail planted to waste your time."},
            {"kind": "empty", "label": "Cold surface", "icon": "·", "detail": "No signal. No heat. Keep moving."},
        ]
    )
    random.shuffle(payloads)
    hidden = {location: payloads[index] for index, location in enumerate(locations)}
    dossier_location = next(location for location in locations if hidden[location]["kind"] == "dossier")
    return {
        "round": 1,
        "score": 0,
        "momentum": 0,
        "integrity": 3,
        "clue_tokens": 1,
        "searched": set(),
        "rival_searched": set(),
        "hidden": hidden,
        "dossier_location": dossier_location,
        "traps": {},
        "inventory": [],
        "clues": [],
        "feed": [
            {"message": "Mission clock live. Rook is already inside the suite.", "kind": "system"},
            {"message": "Find the Prism dossier. Leave no clean angles.", "kind": "objective"},
        ],
        "selected_room": "Glasshouse",
        "game_over": False,
        "result": None,
        "rival_progress": 0,
        "rival_alert": 1,
        "last_action": "Choose a wing and search a location.",
    }


def ensure_game() -> GameState:
    if "game" not in st.session_state:
        st.session_state.game = create_game()
    return cast(GameState, st.session_state.game)


def add_feed(game: GameState, message: str, kind: str = "neutral") -> None:
    feed: List[Dict[str, str]] = game["feed"]
    game["feed"] = [{"message": message, "kind": kind}, *feed][:9]


def flash(game: GameState, message: str, kind: str = "neutral") -> None:
    game["last_action"] = message
    add_feed(game, message, kind)


def has_item(game: GameState, label: str) -> bool:
    return label in game["inventory"]


def end_game(game: GameState, title: str, detail: str, won: bool) -> None:
    game["game_over"] = True
    game["result"] = {"title": title, "detail": detail, "won": won}
    flash(game, detail, "success" if won else "danger")


def resolve_rival_turn(game: GameState) -> None:
    """Give the rival one imperfect but dangerous action after every player move."""
    if game["game_over"]:
        return

    candidate_locations = [
        location for location in all_locations() if location not in game["rival_searched"]
    ]
    if not candidate_locations:
        return

    # Rook alternates between searching and seeding danger, with a small bias toward searching.
    should_plant = random.random() < 0.24 and bool(game["inventory"])
    if should_plant:
        trap_candidates = [
            location
            for location in candidate_locations
            if location not in game["traps"] and location not in game["searched"]
        ]
        if trap_candidates:
            trap_location = random.choice(trap_candidates)
            game["traps"][trap_location] = "rival"
            room_name, spot_name = trap_location
            add_feed(game, f"Rook seeded a silent tripwire near {spot_name}.", "danger")
            game["rival_alert"] = min(5, game["rival_alert"] + 1)
            return

    location = random.choice(candidate_locations)
    game["rival_searched"].add(location)
    payload: Payload = game["hidden"][location]
    room_name, spot_name = location

    if game["traps"].get(location) == "player":
        game["traps"].pop(location, None)
        game["score"] += 5
        game["momentum"] = min(100, game["momentum"] + 14)
        add_feed(game, f"Rook hit your tripwire in {room_name}. Clean work, operative.", "success")
        return

    if payload["kind"] == "dossier":
        game["rival_progress"] = 100
        end_game(
            game,
            "Rook got there first",
            "The Prism dossier vanished into the rain. Reset the operation and change your route.",
            False,
        )
        return

    if payload["kind"] != "empty":
        game["rival_progress"] = min(92, game["rival_progress"] + random.randint(7, 16))
        add_feed(game, f"Rook searched {spot_name}. His signal moved north.", "rival")
    else:
        add_feed(game, f"Rook searched {spot_name} and came up empty.", "neutral")


def finish_player_action(game: GameState) -> None:
    if game["game_over"]:
        return
    resolve_rival_turn(game)
    if game["game_over"]:
        return
    game["round"] += 1
    if game["round"] > MAX_ROUNDS:
        end_game(
            game,
            "The window closed",
            "The extraction lift locked down before either operative had a clean exit.",
            False,
        )


def resolve_trap(game: GameState, location: Location) -> bool:
    if game["traps"].get(location) != "rival":
        return True

    game["traps"].pop(location, None)
    if has_item(game, "Wire clip"):
        game["inventory"].remove("Wire clip")
        game["score"] += 4
        game["momentum"] = min(100, game["momentum"] + 11)
        flash(game, "Tripwire disarmed. Your wire clip is spent.", "success")
        return True

    if has_item(game, "Smoke capsule"):
        game["inventory"].remove("Smoke capsule")
        game["score"] += 1
        flash(game, "The trap snapped. Your smoke capsule covered the escape.", "warning")
        return True

    game["integrity"] -= 1
    game["score"] = max(0, game["score"] - 3)
    flash(game, "Tripwire hit. Integrity -1. Rook knows you are close.", "danger")
    game["rival_alert"] = min(5, game["rival_alert"] + 1)
    if game["integrity"] <= 0:
        end_game(game, "Compromised in the suite", "Three alarms. One careless angle too many.", False)
        return False
    return True


def search_location(game: GameState, room_name: str, spot_name: str) -> None:
    if game["game_over"]:
        return
    location = (room_name, spot_name)
    if location in game["searched"]:
        return

    game["searched"].add(location)
    payload: Payload = game["hidden"][location]
    add_feed(game, f"You searched {spot_name} in {room_name}.", "player")
    if not resolve_trap(game, location):
        return

    if payload["kind"] == "dossier":
        game["score"] += 50
        game["momentum"] = 100
        end_game(
            game,
            "Prism dossier secured",
            "You found the file before Rook could close the suite. Get to extraction.",
            True,
        )
        return

    if payload["kind"] == "empty":
        flash(game, f"{payload['label']} — the angle is cold.", "neutral")
    else:
        label = payload["label"]
        game["inventory"].append(label)
        game["score"] += 8 if payload["kind"] != "intel" else 5
        game["momentum"] = min(100, game["momentum"] + 12)
        flash(game, f"Recovered: {label}.", "success")
        if payload["kind"] == "booster":
            game["clue_tokens"] += 1
            add_feed(game, "Signal booster charged. You have one extra scan.", "success")
        if payload["kind"] == "intel":
            game["rival_alert"] = max(1, game["rival_alert"] - 1)
            add_feed(game, "Transit note acquired. Rook's read on the suite just got fuzzier.", "success")

    finish_player_action(game)


def scout_room(game: GameState, room_name: str) -> None:
    if game["game_over"] or game["clue_tokens"] <= 0:
        return
    game["clue_tokens"] -= 1
    possible = [
        location
        for location in all_locations()
        if location[0] == room_name
        and location not in game["searched"]
        and game["hidden"][location]["kind"] in {"dossier", "wire", "booster", "intel", "decoy"}
    ]
    if possible:
        room, spot = random.choice(possible)
        game["clues"].insert(0, f"{room}: a clean signal is strongest near {spot}.")
        flash(game, f"Scan complete. Something useful is close to {spot}.", "success")
    else:
        game["clues"].insert(0, f"{room_name}: only dead surfaces and false heat.")
        flash(game, f"Scan complete. {room_name} is mostly cold.", "warning")
    finish_player_action(game)


def rig_trap(game: GameState, room_name: str, spot_name: str) -> None:
    if game["game_over"] or not has_item(game, "Wire clip"):
        return
    location = (room_name, spot_name)
    if location in game["searched"] or location in game["traps"]:
        return
    game["inventory"].remove("Wire clip")
    game["traps"][location] = "player"
    game["score"] += 2
    flash(game, f"Tripwire rigged at {spot_name}. Let Rook do the walking.", "success")
    finish_player_action(game)


def select_room(room_name: str) -> None:
    game = ensure_game()
    game["selected_room"] = room_name
    st.rerun()


def render_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
        :root {
            --ink: #f4f7fb;
            --muted: #9aa8bb;
            --panel: rgba(19, 28, 47, .82);
            --panel-strong: #172239;
            --line: rgba(168, 191, 219, .16);
            --cyan: #50e3bb;
            --coral: #ff756c;
            --gold: #ffd166;
            --navy: #080d19;
        }
        .stApp {
            background:
                radial-gradient(circle at 10% 0%, rgba(80, 227, 187, .11), transparent 28rem),
                radial-gradient(circle at 92% 5%, rgba(255, 117, 108, .10), transparent 30rem),
                linear-gradient(145deg, #080d19 0%, #0d1526 52%, #09101f 100%);
            color: var(--ink);
            font-family: 'Manrope', ui-sans-serif, system-ui, sans-serif;
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stToolbar"] { visibility: hidden; }
        .block-container { max-width: 1450px; padding: 2.25rem 3rem 4rem; }
        .brand-row { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom: 1.7rem; }
        .brand-left { display:flex; align-items:center; gap:.8rem; }
        .brand-mark { width:42px; height:42px; display:grid; place-items:center; border-radius:14px; color:#07121d; background:linear-gradient(135deg, #50e3bb, #90f4d6); font-size:1.45rem; font-weight:800; box-shadow:0 0 30px rgba(80,227,187,.24); }
        .brand-name { color:var(--ink); font-size:1.02rem; letter-spacing:.18em; font-weight:800; text-transform:uppercase; }
        .brand-sub { color:var(--muted); font-family:'DM Mono', monospace; font-size:.68rem; letter-spacing:.08em; margin-top:.2rem; }
        .status-pill { display:inline-flex; align-items:center; gap:.5rem; border:1px solid rgba(80,227,187,.28); color:#96f4dc; background:rgba(80,227,187,.07); padding:.55rem .8rem; border-radius:999px; font-family:'DM Mono',monospace; font-size:.65rem; letter-spacing:.08em; }
        .status-dot { width:7px; height:7px; border-radius:50%; background:#50e3bb; box-shadow:0 0 10px #50e3bb; }
        .hero { display:flex; justify-content:space-between; align-items:flex-end; gap:2rem; padding:1.4rem 0 1.7rem; border-top:1px solid var(--line); border-bottom:1px solid var(--line); margin-bottom:1.2rem; }
        .hero-kicker { color:var(--cyan); font-family:'DM Mono', monospace; font-size:.7rem; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.7rem; }
        .hero-title { font-size:clamp(2.4rem, 5.3vw, 5.5rem); line-height:.94; letter-spacing:-.075em; font-weight:800; margin:0; color:#f7fafc; }
        .hero-title span { color:var(--coral); }
        .hero-copy { color:var(--muted); max-width:29rem; font-size:.94rem; line-height:1.65; margin:0; }
        .metric-grid { display:grid; grid-template-columns:repeat(4, 1fr); gap:.7rem; margin:1.1rem 0 1.4rem; }
        .metric { min-height:86px; background:rgba(18, 29, 49, .68); border:1px solid var(--line); border-radius:17px; padding:1rem 1.05rem; position:relative; overflow:hidden; }
        .metric:after { content:''; position:absolute; width:90px; height:90px; right:-35px; top:-42px; border-radius:50%; border:1px solid rgba(80,227,187,.17); }
        .metric-label { color:#8190a4; font-family:'DM Mono',monospace; font-size:.63rem; letter-spacing:.11em; text-transform:uppercase; }
        .metric-value { color:#f6f8fc; font-size:1.65rem; font-weight:800; letter-spacing:-.05em; margin-top:.25rem; }
        .metric-value.cyan { color:var(--cyan); }
        .metric-value.coral { color:var(--coral); }
        .metric-value.gold { color:var(--gold); }
        .section-label { display:flex; justify-content:space-between; align-items:center; color:#8b9ab1; font-family:'DM Mono',monospace; font-size:.67rem; letter-spacing:.12em; text-transform:uppercase; margin: .35rem 0 .65rem; }
        .section-label strong { color:#eef4f8; font-weight:500; }
        .map-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:.72rem; margin-bottom:1.05rem; }
        .room-card { border-radius:19px; border:1px solid var(--line); min-height:160px; padding:1rem; position:relative; overflow:hidden; background:linear-gradient(145deg, rgba(25,37,59,.9), rgba(15,23,40,.72)); }
        .room-card.selected { border-color:rgba(80,227,187,.7); box-shadow:0 0 0 1px rgba(80,227,187,.12), 0 16px 42px rgba(0,0,0,.16); }
        .room-card .room-glow { position:absolute; width:135px; height:135px; border-radius:50%; top:-60px; right:-35px; opacity:.13; filter:blur(1px); }
        .room-icon { font-size:1.35rem; font-weight:800; position:relative; }
        .room-eyebrow { color:#8d9bb0; font-family:'DM Mono',monospace; font-size:.6rem; letter-spacing:.07em; margin-top:.85rem; }
        .room-name { color:#f4f7fb; font-size:1.03rem; font-weight:800; letter-spacing:-.03em; margin:.3rem 0 .16rem; }
        .room-subtitle { color:#94a2b4; font-size:.71rem; line-height:1.4; }
        .room-progress { color:#6f8197; font-family:'DM Mono',monospace; font-size:.61rem; position:absolute; bottom:1rem; left:1rem; }
        .room-panel { border:1px solid var(--line); background:rgba(17,27,46,.68); border-radius:22px; padding:1.2rem; margin-bottom:1.2rem; }
        .room-panel-head { display:flex; align-items:flex-start; justify-content:space-between; gap:1rem; margin-bottom:1rem; }
        .room-panel-title { color:#f4f7fb; font-size:1.45rem; font-weight:800; letter-spacing:-.045em; }
        .room-panel-copy { color:#93a1b4; font-size:.78rem; line-height:1.5; max-width:31rem; margin-top:.25rem; }
        .scan-chip { color:#07151a; background:var(--gold); border-radius:999px; padding:.42rem .7rem; font-family:'DM Mono',monospace; font-size:.62rem; white-space:nowrap; }
        .spot-row { display:grid; grid-template-columns:1fr auto; align-items:center; gap:.75rem; border-top:1px solid rgba(168,191,219,.11); padding:.9rem 0 .25rem; }
        .spot-name { color:#e7edf5; font-size:.84rem; font-weight:700; }
        .spot-detail { color:#7f90a6; font-size:.7rem; line-height:1.45; margin-top:.23rem; }
        .spot-status { color:var(--cyan); font-family:'DM Mono',monospace; font-size:.6rem; letter-spacing:.08em; text-transform:uppercase; }
        .side-card { border:1px solid var(--line); background:rgba(17,27,46,.68); border-radius:22px; padding:1.2rem; margin-bottom:1rem; }
        .side-card.rival { background:linear-gradient(145deg, rgba(54,26,43,.73), rgba(20,27,46,.73)); }
        .agent-row { display:flex; align-items:center; gap:.8rem; }
        .agent-avatar { width:44px; height:44px; display:grid; place-items:center; border-radius:15px; color:#180e16; background:linear-gradient(135deg,#ff756c,#ffb087); font-size:1.3rem; font-weight:800; }
        .agent-name { color:#f6f8fc; font-size:.96rem; font-weight:800; }
        .agent-role { color:#a98b9c; font-family:'DM Mono',monospace; font-size:.6rem; letter-spacing:.09em; margin-top:.22rem; }
        .progress-shell { height:6px; background:rgba(214,226,237,.12); border-radius:999px; overflow:hidden; margin-top:1rem; }
        .progress-fill { height:100%; border-radius:999px; background:linear-gradient(90deg,#ff756c,#ffd166); box-shadow:0 0 13px rgba(255,117,108,.45); }
        .loadout { display:flex; flex-wrap:wrap; gap:.45rem; margin-top:.8rem; }
        .loadout-chip { color:#cdd8e4; border:1px solid rgba(168,191,219,.16); background:rgba(168,191,219,.07); padding:.43rem .58rem; border-radius:9px; font-family:'DM Mono',monospace; font-size:.61rem; }
        .loadout-chip.hot { color:#071b19; background:var(--cyan); border-color:var(--cyan); }
        .feed-item { display:flex; gap:.65rem; padding:.68rem 0; border-bottom:1px solid rgba(168,191,219,.09); }
        .feed-item:last-child { border-bottom:0; }
        .feed-dot { flex:0 0 auto; width:6px; height:6px; margin-top:.4rem; border-radius:50%; background:#708098; }
        .feed-dot.success { background:var(--cyan); box-shadow:0 0 10px rgba(80,227,187,.65); }
        .feed-dot.danger { background:var(--coral); box-shadow:0 0 10px rgba(255,117,108,.45); }
        .feed-dot.rival { background:var(--gold); }
        .feed-message { color:#aab7c8; font-size:.71rem; line-height:1.45; }
        .clue { color:#0d1b20; background:rgba(80,227,187,.93); border-radius:11px; padding:.65rem .72rem; font-family:'DM Mono',monospace; font-size:.63rem; line-height:1.5; margin-top:.55rem; }
        .flash { border-radius:13px; padding:.8rem .9rem; font-size:.78rem; margin:0 0 1rem; border:1px solid rgba(80,227,187,.27); color:#bdf7e9; background:rgba(80,227,187,.08); }
        .flash.warning { color:#ffe5a0; border-color:rgba(255,209,102,.27); background:rgba(255,209,102,.08); }
        .flash.danger { color:#ffc4c0; border-color:rgba(255,117,108,.3); background:rgba(255,117,108,.08); }
        .result-card { border:1px solid rgba(80,227,187,.38); background:linear-gradient(135deg,rgba(80,227,187,.16),rgba(19,31,49,.73)); border-radius:23px; padding:1.2rem 1.3rem; margin-bottom:1rem; }
        .result-card.loss { border-color:rgba(255,117,108,.38); background:linear-gradient(135deg,rgba(255,117,108,.13),rgba(31,24,44,.73)); }
        .result-kicker { color:var(--cyan); font-family:'DM Mono',monospace; font-size:.63rem; letter-spacing:.12em; text-transform:uppercase; }
        .result-card.loss .result-kicker { color:var(--coral); }
        .result-title { color:#f7fafc; font-weight:800; font-size:1.45rem; letter-spacing:-.05em; margin:.28rem 0 .3rem; }
        .result-copy { color:#a9b7c8; font-size:.78rem; line-height:1.5; }
        .footer-line { color:#566a83; font-family:'DM Mono',monospace; font-size:.61rem; letter-spacing:.07em; text-align:center; padding:1.1rem 0 0; }
        .stButton > button { min-height:40px; border-radius:11px; border:1px solid rgba(168,191,219,.19); background:rgba(137,158,185,.08); color:#dce6ef; font-family:'DM Mono',monospace; font-size:.63rem; letter-spacing:.06em; transition:all .18s ease; }
        .stButton > button:hover { border-color:rgba(80,227,187,.62); color:#baf7e8; background:rgba(80,227,187,.09); transform:translateY(-1px); }
        .stButton > button:disabled { opacity:.45; color:#8090a4; border-color:rgba(168,191,219,.1); }
        div[data-testid="stSidebar"] { background:rgba(8,13,25,.84); border-right:1px solid rgba(168,191,219,.13); }
        div[data-testid="stSidebar"] .block-container { padding:2rem 1.2rem; }
        @media (max-width: 850px) {
            .block-container { padding:1.3rem 1rem 3rem; }
            .hero { display:block; }
            .hero-copy { margin-top:1rem; }
            .metric-grid { grid-template-columns:repeat(2,1fr); }
            .map-grid { grid-template-columns:1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_grid(game: GameState) -> None:
    integrity = int(game["integrity"])
    integrity_label = "●" * integrity + "○" * (3 - integrity)
    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric"><div class="metric-label">Operation</div><div class="metric-value cyan">{int(game['round']):02d}<span style="font-size:.8rem;color:#7e8da1;font-weight:500;"> / {MAX_ROUNDS:02d}</span></div></div>
            <div class="metric"><div class="metric-label">Field score</div><div class="metric-value gold">{int(game['score']):03d}</div></div>
            <div class="metric"><div class="metric-label">Integrity</div><div class="metric-value coral" style="font-size:1.18rem;letter-spacing:.08em;">{integrity_label}</div></div>
            <div class="metric"><div class="metric-label">Momentum</div><div class="metric-value cyan">{int(game['momentum'])}<span style="font-size:.8rem;color:#7e8da1;font-weight:500;">%</span></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_room_map(game: GameState) -> None:
    st.markdown(
        '<div class="section-label"><strong>Choose a wing</strong><span>One move per round</span></div>',
        unsafe_allow_html=True,
    )
    columns = st.columns(3)
    for column, (room_name, room) in zip(columns, ROOMS.items()):
        searched_count = sum(1 for location in game["searched"] if location[0] == room_name)
        selected = room_name == game["selected_room"]
        with column:
            selected_class = " selected" if selected else ""
            st.markdown(
                f"""
                <div class="room-card{selected_class}">
                    <div class="room-glow" style="background:{room['accent']};"></div>
                    <div class="room-icon" style="color:{room['accent']};">{room['icon']}</div>
                    <div class="room-eyebrow">{escape(room['eyebrow'])}</div>
                    <div class="room-name">{escape(room_name)}</div>
                    <div class="room-subtitle">{escape(room['subtitle'])}</div>
                    <div class="room-progress">{searched_count} / 3 angles cleared</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.button(
                "OPEN WING" if not selected else "WING SELECTED",
                key=f"room_{room_name}",
                on_click=select_room,
                args=(room_name,),
                use_container_width=True,
                disabled=game["game_over"],
            )


def render_selected_room(game: GameState) -> None:
    room_name = str(game["selected_room"])
    room = ROOMS[room_name]
    st.markdown(
        f"""
        <div class="room-panel">
            <div class="room-panel-head">
                <div>
                    <div class="section-label" style="margin:0 0 .35rem;"><strong>{escape(room['eyebrow'])}</strong><span>{escape(room['subtitle'])}</span></div>
                    <div class="room-panel-title">{escape(room_name)}</div>
                    <div class="room-panel-copy">{escape(room['description'])}</div>
                </div>
                <div class="scan-chip">{int(game['clue_tokens'])} SCAN{'S' if game['clue_tokens'] != 1 else ''}</div>
            </div>
        """,
        unsafe_allow_html=True,
    )
    if not game["game_over"]:
        scan_column, _ = st.columns([1, 2.6])
        with scan_column:
            st.button(
                "SCAN THIS WING",
                key=f"scan_{room_name}",
                on_click=scout_room,
                args=(game, room_name),
                use_container_width=True,
                disabled=game["clue_tokens"] <= 0,
            )

    for spot in room["spots"]:
        spot_name = str(spot["name"])
        location = (room_name, spot_name)
        searched = location in game["searched"]
        player_trap = game["traps"].get(location) == "player"
        status = "CLEARED" if searched else ("RIGGED" if player_trap else "UNREAD")
        status_color = "#50e3bb" if searched or player_trap else "#8292a7"
        st.markdown(
            f"""
            <div class="spot-row">
                <div>
                    <div class="spot-name">{escape(spot_name)}</div>
                    <div class="spot-detail">{escape(spot['detail'])}</div>
                </div>
                <div class="spot-status" style="color:{status_color};">{status}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        search_column, rig_column = st.columns([1, 1])
        with search_column:
            st.button(
                "SEARCH ANGLE",
                key=f"search_{room_name}_{spot_name}",
                on_click=search_location,
                args=(game, room_name, spot_name),
                use_container_width=True,
                disabled=searched or game["game_over"],
            )
        with rig_column:
            st.button(
                "RIG TRIPWIRE",
                key=f"rig_{room_name}_{spot_name}",
                on_click=rig_trap,
                args=(game, room_name, spot_name),
                use_container_width=True,
                disabled=(
                    searched
                    or game["game_over"]
                    or location in game["traps"]
                    or not has_item(game, "Wire clip")
                ),
            )
    st.markdown("</div>", unsafe_allow_html=True)


def render_rival_card(game: GameState) -> None:
    progress = int(game["rival_progress"])
    alert = int(game["rival_alert"])
    st.markdown(
        f"""
        <div class="side-card rival">
            <div class="section-label"><strong>Adversary signal</strong><span style="color:#ff938a;">LIVE</span></div>
            <div class="agent-row">
                <div class="agent-avatar">◒</div>
                <div><div class="agent-name">Rook</div><div class="agent-role">UNAFFILIATED / SILENT RUNNER</div></div>
            </div>
            <div class="progress-shell"><div class="progress-fill" style="width:{progress}%;"></div></div>
            <div style="display:flex;justify-content:space-between;color:#aa8e9d;font-family:'DM Mono',monospace;font-size:.6rem;margin-top:.45rem;"><span>DOSSIER READ</span><span>{progress}%</span></div>
            <div style="color:#a98b9c;font-size:.72rem;line-height:1.5;margin-top:1rem;">Rook's alert level: <strong style="color:#ffd166;">{'▰' * alert}{'▱' * (5-alert)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_loadout(game: GameState) -> None:
    inventory: List[str] = game["inventory"]
    chips = "".join(
        f'<span class="loadout-chip {"hot" if item == "Prism dossier" else ""}">{escape(item)}</span>'
        for item in inventory
    )
    if not chips:
        chips = '<span style="color:#718198;font-family:\'DM Mono\',monospace;font-size:.64rem;">EMPTY / KEEP MOVING</span>'
    st.markdown(
        f"""
        <div class="side-card">
            <div class="section-label"><strong>Loadout</strong><span>{len(inventory)} recovered</span></div>
            <div class="loadout">{chips}</div>
            <div style="color:#74859c;font-size:.69rem;line-height:1.5;margin-top:.8rem;">Wire clips rig tripwires. Smoke capsules soften a bad hit. The dossier is the only way out.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_feed(game: GameState) -> None:
    items: List[Dict[str, str]] = game["feed"]
    feed_markup = "".join(
        f"<div class='feed-item'><div class='feed-dot {escape(item['kind'])}'></div><div class='feed-message'>{escape(item['message'])}</div></div>"
        for item in items[:6]
    )
    st.markdown(
        f"""
        <div class="side-card">
            <div class="section-label"><strong>Field feed</strong><span>encrypted</span></div>
            {feed_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_clues(game: GameState) -> None:
    clues: List[str] = game["clues"]
    if not clues:
        return
    markup = "".join(f'<div class="clue">{escape(clue)}</div>' for clue in clues[:3])
    st.markdown(
        f"<div class='section-label'><strong>Intercepted intel</strong><span>{len(clues)} note{'s' if len(clues) != 1 else ''}</span></div>{markup}",
        unsafe_allow_html=True,
    )


def render_sidebar(game: GameState) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand-left" style="margin-bottom:1.2rem;">
                <div class="brand-mark" style="width:36px;height:36px;border-radius:12px;font-size:1.1rem;">◈</div>
                <div><div class="brand-name" style="font-size:.78rem;">CIPHER CLASH</div><div class="brand-sub">FIELD MANUAL / 01</div></div>
            </div>
            <div class="section-label"><strong>How to play</strong><span>briefing</span></div>
            <div style="color:#9aa8bb;font-size:.75rem;line-height:1.7;">
                Pick a wing, search one angle, then survive Rook's response. Recover tools to rig danger and spend scans when the room feels too quiet.
            </div>
            <div style="height:1px;background:rgba(168,191,219,.14);margin:1.2rem 0;"></div>
            <div class="section-label"><strong>Win condition</strong><span>prism</span></div>
            <div style="color:#d7e3ec;font-size:.75rem;line-height:1.65;">Find the Prism dossier before the 12-round window closes. Three trap hits compromise the operation.</div>
            <div style="height:1px;background:rgba(168,191,219,.14);margin:1.2rem 0;"></div>
            <div class="section-label"><strong>Design note</strong><span>original</span></div>
            <div style="color:#77889e;font-size:.69rem;line-height:1.6;">A new, original spy-fi duel: no borrowed names, characters, or art. Just pressure, misdirection, and one clean exit.</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
        st.button("RESET OPERATION", key="reset_sidebar", on_click=lambda: st.session_state.update(game=create_game()), use_container_width=True)


def render_result(game: GameState) -> None:
    result: Optional[Dict[str, Any]] = game.get("result")
    if not result:
        return
    result_class = "" if result["won"] else " loss"
    kicker = "OPERATION COMPLETE" if result["won"] else "OPERATION LOST"
    st.markdown(
        f"""
        <div class="result-card{result_class}">
            <div class="result-kicker">{kicker}</div>
            <div class="result-title">{escape(str(result['title']))}</div>
            <div class="result-copy">{escape(str(result['detail']))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.button("START A FRESH OPERATION", key="reset_result", on_click=lambda: st.session_state.update(game=create_game()), use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Cipher Clash", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
    render_styles()
    game = ensure_game()
    render_sidebar(game)

    st.markdown(
        """
        <div class="brand-row">
            <div class="brand-left"><div class="brand-mark">◈</div><div><div class="brand-name">Cipher Clash</div><div class="brand-sub">A high-pressure espionage duel</div></div></div>
            <div class="status-pill"><span class="status-dot"></span>SUITE 06 / SIGNAL LIVE</div>
        </div>
        <div class="hero">
            <div><div class="hero-kicker">Operation 06 · The Prism Relay</div><h1 class="hero-title">Stay sharp.<br><span>Leave no trace.</span></h1></div>
            <p class="hero-copy">Two operatives. Three wings. One dossier hidden in plain sight. Search smarter than your rival, rig the angles they will trust, and make the cleanest exit.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not game["game_over"]:
        flash_kind = ""
        last_action = str(game["last_action"])
        if "Integrity" in last_action or "tripwire" in last_action.lower() and "disarmed" not in last_action.lower():
            flash_kind = "danger" if "Integrity" in last_action else "warning"
        st.markdown(f'<div class="flash {flash_kind}"><strong>FIELD NOTE</strong>&nbsp;&nbsp; {escape(last_action)}</div>', unsafe_allow_html=True)
    else:
        render_result(game)

    render_metric_grid(game)
    left_column, right_column = st.columns([1.7, 1], gap="large")
    with left_column:
        render_room_map(game)
        render_selected_room(game)
        render_clues(game)
    with right_column:
        render_rival_card(game)
        render_loadout(game)
        render_feed(game)

    st.markdown('<div class="footer-line">CIPHER CLASH · ORIGINAL FIELD SIMULATION · PRESSURE MAKES THE PATTERN</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
