import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Cyber Clash",
    page_icon="\U0001F5A5",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 1100px; }
    #MainMenu, header, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Cyber Clash")
st.caption(
    "A briefcase-and-booby-trap infiltration game, inspired by the classic "
    "rival-spy formula — rebuilt from scratch with original code, art, and physics. "
    "Tap the ⛶ icon in the game to go fullscreen."
)

GAME_HTML = r"""
<div id="cc-root">
  <style>
    #cc-root {
      --cy: #00f0ff;
      --mg: #ff2e88;
      --gold: #ffcc33;
      --danger: #ff3b3b;
      --bg0: #05070d;
      --bg1: #0b1220;
      --panel: #0d1526;
      font-family: 'Share Tech Mono', 'Courier New', monospace;
      color: #d9f6ff;
      position: relative;
      width: 100%;
      max-width: 940px;
      margin: 0 auto;
      user-select: none;
      -webkit-user-select: none;
    }
    #cc-root * { box-sizing: border-box; }
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Share+Tech+Mono&display=swap');

    #cc-stage {
      position: relative;
      width: 100%;
      aspect-ratio: 900 / 620;
      background: var(--bg0);
      border: 1px solid #163049;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 0 0 1px #000, 0 0 40px rgba(0,240,255,0.08), inset 0 0 60px rgba(0,240,255,0.03);
      touch-action: none;
    }
    #cc-canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }

    /* ---- Fullscreen mode ---- */
    #cc-root.cc-fullscreen {
      position: fixed !important;
      inset: 0;
      max-width: none;
      width: 100vw;
      height: 100vh;
      margin: 0;
      z-index: 999999;
      background: #05070d;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    #cc-root.cc-fullscreen #cc-stage {
      aspect-ratio: unset;
      border-radius: 0;
      border: none;
      flex: none;
    }
    #cc-root.cc-fullscreen #cc-footer { display: none; }

    #cc-overlay {
      position: absolute; inset: 0;
      display: flex; align-items: center; justify-content: center;
      background: radial-gradient(ellipse at center, rgba(6,10,20,0.75) 0%, rgba(4,6,12,0.96) 75%);
      backdrop-filter: blur(2px);
      z-index: 50;
      overflow-y: auto;
    }
    #cc-overlay.hidden { display: none; }
    .cc-panel { text-align: center; padding: 24px; width: min(94%, 620px); margin: auto; }
    .cc-title {
      font-family: 'Orbitron', sans-serif;
      font-weight: 900;
      font-size: clamp(26px, 6vw, 50px);
      letter-spacing: 4px;
      color: #eafffe;
      text-shadow:
        0 0 6px var(--cy), 0 0 18px var(--cy),
        3px 0 0 var(--mg), -3px 0 0 rgba(0,240,255,0.6);
      animation: cc-flicker 3.2s infinite;
      margin: 0 0 6px 0;
    }
    .cc-sub {
      font-size: 12px; letter-spacing: 3px; color: #6fb3c9; margin-bottom: 18px;
      text-transform: uppercase;
    }
    @keyframes cc-flicker {
      0%, 92%, 100% { opacity: 1; }
      93% { opacity: 0.55; }
      94% { opacity: 1; }
      95% { opacity: 0.6; }
      96% { opacity: 1; }
    }
    .cc-row { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; margin-top: 10px; }
    .cc-btn {
      font-family: 'Share Tech Mono', monospace;
      background: linear-gradient(180deg, #0f2233, #081019);
      border: 1px solid var(--cy);
      color: var(--cy);
      padding: 12px 20px;
      font-size: 13.5px;
      letter-spacing: 2px;
      text-transform: uppercase;
      border-radius: 4px;
      cursor: pointer;
      transition: all .15s ease;
      box-shadow: 0 0 8px rgba(0,240,255,0.15);
    }
    .cc-btn:hover { background: var(--cy); color: #041018; box-shadow: 0 0 22px var(--cy); }
    .cc-btn.mg { border-color: var(--mg); color: var(--mg); }
    .cc-btn.mg:hover { background: var(--mg); color: #180010; box-shadow: 0 0 22px var(--mg); }
    .cc-btn.gold { border-color: var(--gold); color: var(--gold); }
    .cc-btn.gold:hover { background: var(--gold); color: #201400; box-shadow: 0 0 22px var(--gold); }
    .cc-btn:disabled { opacity: 0.3; cursor: not-allowed; }
    .cc-btn:disabled:hover { background: linear-gradient(180deg, #0f2233, #081019); color: var(--cy); box-shadow: none; }

    .cc-info {
      margin-top: 18px; font-size: 11.5px; line-height: 1.8; color: #8fb7c7;
      text-align: left; background: rgba(0,240,255,0.04); border: 1px solid #16334a;
      border-radius: 6px; padding: 12px 16px;
    }
    .cc-info b { color: var(--gold); }
    .cc-key { display:inline-block; border:1px solid #3a5a6b; border-radius:3px; padding:0 6px; margin:0 2px; color:#dff; background:#0a1622; }
    .cc-winline { font-size: 18px; margin: 12px 0 4px; letter-spacing: 1px; }

    .cc-chapgrid {
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
      margin-top: 14px; max-height: 320px; overflow-y: auto; padding: 4px;
    }
    .cc-chapbtn {
      font-family: 'Share Tech Mono', monospace;
      background: #081019; border: 1px solid #16334a; color: #7ec9db;
      padding: 12px 4px; border-radius: 4px; cursor: pointer; font-size: 13px;
    }
    .cc-chapbtn.unlocked { border-color: var(--cy); color: var(--cy); }
    .cc-chapbtn.unlocked:hover { background: var(--cy); color: #041018; }
    .cc-chapbtn:disabled { opacity: 0.25; cursor: not-allowed; }

    #cc-hud {
      position: absolute; top: 0; left: 0; right: 0; z-index: 3;
      display: flex; justify-content: space-between; padding: 8px 12px;
      font-size: 12px; pointer-events: none;
      text-shadow: 0 0 6px rgba(0,0,0,0.9);
    }
    .cc-hud-side { display: flex; flex-direction: column; gap: 3px; min-width: 140px; }
    .cc-hud-side.right { align-items: flex-end; text-align: right; }
    .cc-name { font-weight: bold; letter-spacing: 1px; }
    .cc-name.cy { color: var(--cy); }
    .cc-name.mg { color: var(--mg); }
    .cc-bar { width: 120px; height: 8px; border: 1px solid #234; background: #0a1420; border-radius: 3px; overflow: hidden; }
    .cc-bar > div { height: 100%; background: var(--gold); width: 0%; transition: width .2s; }
    .cc-hud-mid { text-align: center; font-size: 11px; color: #7ec9db; letter-spacing: 2px; }
    #cc-hud-chapter { color: var(--gold); margin-bottom: 2px; }

    #cc-toast {
      position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
      font-size: 13px; letter-spacing: 1px; color: var(--gold); z-index: 4;
      text-shadow: 0 0 8px #000; opacity: 0; transition: opacity .25s; pointer-events: none;
      white-space: nowrap;
    }
    #cc-toast.show { opacity: 1; }

    /* ---- top-right in-stage icon controls ---- */
    #cc-icons {
      position: absolute; top: 8px; right: 8px; z-index: 20;
      display: flex; gap: 6px;
    }
    #cc-icons button {
      width: 30px; height: 30px; border-radius: 50%;
      background: rgba(8,16,25,0.7); border: 1px solid #234a5c; color: #7ec9db;
      font-size: 14px; cursor: pointer; display: flex; align-items: center; justify-content: center;
    }
    #cc-icons button:hover { border-color: var(--cy); color: var(--cy); }

    /* ---- touch controls ---- */
    #cc-touch {
      position: absolute; inset: 0; z-index: 15; pointer-events: none; display: none;
    }
    #cc-joy-base {
      position: absolute; left: 20px; bottom: 20px; width: 108px; height: 108px;
      border-radius: 50%; background: rgba(0,240,255,0.07); border: 2px solid rgba(0,240,255,0.35);
      pointer-events: auto; touch-action: none;
    }
    #cc-joy-stick {
      position: absolute; left: 50%; top: 50%; width: 44px; height: 44px;
      margin: -22px 0 0 -22px; border-radius: 50%;
      background: rgba(0,240,255,0.55); border: 2px solid var(--cy);
    }
    #cc-touch-action {
      position: absolute; right: 24px; bottom: 30px; width: 76px; height: 76px;
      border-radius: 50%; background: rgba(255,46,136,0.16); border: 2px solid var(--mg);
      color: var(--mg); font-family: inherit; font-weight: bold; font-size: 11px; letter-spacing: 1px;
      pointer-events: auto; touch-action: none;
    }
    #cc-touch-action:active { background: rgba(255,46,136,0.4); }

    #cc-footer {
      display: flex; justify-content: space-between; align-items: center;
      padding: 6px 4px; font-size: 10.5px; color: #4f7c8c; letter-spacing: 1px;
    }
  </style>

  <div id="cc-stage">
    <canvas id="cc-canvas" width="900" height="620"></canvas>

    <div id="cc-icons">
      <button id="cc-btn-fs" title="Fullscreen">⛶</button>
      <button id="cc-btn-restart2" title="Restart chapter">⟲</button>
    </div>

    <div id="cc-hud" style="display:none">
      <div class="cc-hud-side" id="cc-hud-p1">
        <div class="cc-name cy">AGENT CYAN</div>
        <div class="cc-bar"><div id="cc-bar-p1"></div></div>
        <div id="cc-traps-p1" style="color:#7ec9db">TRAPS: ●●</div>
      </div>
      <div class="cc-hud-mid">
        <div id="cc-hud-chapter"></div>
        <div id="cc-timer">00:00</div>
        <div id="cc-shardpool" style="color:#ffcc33">SHARDS 0/5</div>
      </div>
      <div class="cc-hud-side right" id="cc-hud-p2">
        <div class="cc-name mg" id="cc-p2-label">AGENT MAGENTA</div>
        <div class="cc-bar"><div id="cc-bar-p2" style="background:var(--mg); margin-left:auto;"></div></div>
        <div id="cc-traps-p2" style="color:#7ec9db">TRAPS: ●●</div>
      </div>
    </div>

    <div id="cc-touch">
      <div id="cc-joy-base"><div id="cc-joy-stick"></div></div>
      <button id="cc-touch-action">RIG</button>
    </div>

    <div id="cc-toast"></div>

    <div id="cc-overlay">
      <div class="cc-panel" id="cc-panel-menu">
        <div class="cc-title">CYBER CLASH</div>
        <div class="cc-sub">Infiltrate // Sabotage // Extract</div>
        <div class="cc-row">
          <button class="cc-btn" id="cc-btn-campaign">Campaign</button>
          <button class="cc-btn gold" id="cc-btn-chapters">Chapter Select</button>
          <button class="cc-btn mg" id="cc-btn-2p">2P Skirmish</button>
        </div>
        <div class="cc-info">
          Grab your target number of <b>data shards</b> from the facility and reach your glowing <b>extraction pad</b> before your rival does.<br>
          Sneak up to a console and <b>rig it</b> to zap whoever triggers it next — it won't hurt you.<br><br>
          <b>Agent Cyan</b>: <span class="cc-key">W</span><span class="cc-key">A</span><span class="cc-key">S</span><span class="cc-key">D</span> move, <span class="cc-key">SPACE</span> rig console<br>
          <b>Agent Magenta</b> (2P): <span class="cc-key">←</span><span class="cc-key">↑</span><span class="cc-key">↓</span><span class="cc-key">→</span> move, <span class="cc-key">ENTER</span> rig console<br>
          <b>Touch devices</b>: on-screen stick moves you, RIG button sabotages consoles. 2P Skirmish needs a physical keyboard.<br>
          Tap <b>⛶</b> in the top-right corner of the game to play fullscreen.
        </div>
      </div>
    </div>
  </div>
  <div id="cc-footer">
    <span>CYBER CLASH v2.0 — 16-chapter campaign build — independent fan project</span>
  </div>

  <script>
  (function(){
    "use strict";
    const root = document.getElementById('cc-root');
    const stage = root.querySelector('#cc-stage');
    const canvas = root.querySelector('#cc-canvas');
    const ctx = canvas.getContext('2d');
    const W = 900, H = 620;
    const overlay = root.querySelector('#cc-overlay');
    const panelMenu = root.querySelector('#cc-panel-menu');
    const hud = root.querySelector('#cc-hud');
    const toastEl = root.querySelector('#cc-toast');
    const btnCampaign = root.querySelector('#cc-btn-campaign');
    const btnChapters = root.querySelector('#cc-btn-chapters');
    const btn2P = root.querySelector('#cc-btn-2p');
    const btnFs = root.querySelector('#cc-btn-fs');
    const btnRestart2 = root.querySelector('#cc-btn-restart2');
    const barP1 = root.querySelector('#cc-bar-p1');
    const barP2 = root.querySelector('#cc-bar-p2');
    const trapsP1El = root.querySelector('#cc-traps-p1');
    const trapsP2El = root.querySelector('#cc-traps-p2');
    const timerEl = root.querySelector('#cc-timer');
    const shardPoolEl = root.querySelector('#cc-shardpool');
    const hudChapterEl = root.querySelector('#cc-hud-chapter');
    const p2LabelEl = root.querySelector('#cc-p2-label');
    const touchWrap = root.querySelector('#cc-touch');
    const joyBase = root.querySelector('#cc-joy-base');
    const joyStick = root.querySelector('#cc-joy-stick');
    const actionBtn = root.querySelector('#cc-touch-action');

    const TOTAL_CHAPTERS = 16;
    const WALL_T = 14;

    // ---------- PROGRESS PERSISTENCE ----------
    function loadProgress(){
      try{
        const v = parseInt(localStorage.getItem('cc_max_chapter') || '1', 10);
        return isNaN(v) ? 1 : Math.max(1, Math.min(v, TOTAL_CHAPTERS));
      }catch(e){ return 1; }
    }
    function saveProgress(v){
      try{ localStorage.setItem('cc_max_chapter', String(v)); }catch(e){}
    }
    let maxChapterReached = loadProgress();

    // ---------- SEEDED RNG ----------
    function mulberry32(seed){
      let a = seed >>> 0;
      return function(){
        a |= 0; a = (a + 0x6D2B79F5) | 0;
        let t = Math.imul(a ^ (a >>> 15), 1 | a);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
      };
    }
    function shuffled(arr, rng){
      const a = arr.slice();
      for(let i=a.length-1;i>0;i--){
        const j = Math.floor(rng()*(i+1));
        [a[i],a[j]] = [a[j],a[i]];
      }
      return a;
    }

    // ---------- LEVEL TEMPLATES ----------
    function outerWalls(){
      return [
        {x:0,y:0,w:W,h:WALL_T}, {x:0,y:H-WALL_T,w:W,h:WALL_T},
        {x:0,y:0,w:WALL_T,h:H}, {x:W-WALL_T,y:0,w:WALL_T,h:H},
      ];
    }
    function templateA(){
      return [
        {x:300,y:40,w:14,h:150}, {x:300,y:230,w:14,h:140}, {x:300,y:410,w:14,h:170},
        {x:600,y:40,w:14,h:140}, {x:600,y:220,w:14,h:150}, {x:600,y:420,w:14,h:160},
        {x:40,y:300,w:150,h:14}, {x:240,y:300,w:120,h:14},
        {x:660,y:300,w:90,h:14}, {x:800,y:300,w:60,h:14},
        {x:430,y:150,w:80,h:16}, {x:430,y:450,w:80,h:16},
        {x:160,y:140,w:16,h:80}, {x:720,y:140,w:16,h:80},
      ];
    }
    function templateB(){
      return [
        {x:60,y:170,w:290,h:14}, {x:560,y:170,w:280,h:14},
        {x:60,y:436,w:290,h:14}, {x:560,y:436,w:280,h:14},
        {x:443,y:60,w:14,h:90}, {x:443,y:230,w:14,h:80}, {x:443,y:390,w:14,h:90},
        {x:180,y:280,w:16,h:70}, {x:704,y:280,w:16,h:70},
        {x:340,y:60,w:16,h:60}, {x:544,y:500,w:16,h:60},
      ];
    }
    function mirrorRect(r){ return {x: W - r.x - r.w, y: r.y, w: r.w, h: r.h}; }

    function rectsOverlap(a,b){
      return a.x < b.x+b.w && a.x+a.w > b.x && a.y < b.y+b.h && a.y+a.h > b.y;
    }
    function inflate(r, m){ return {x:r.x-m, y:r.y-m, w:r.w+2*m, h:r.h+2*m}; }

    function seededPillars(rng, count, existingWalls){
      const pillars = [];
      let attempts = 0;
      while(pillars.length < count && attempts < 300){
        attempts++;
        const horiz = rng() < 0.5;
        const w = horiz ? (50 + Math.floor(rng()*40)) : 16;
        const h = horiz ? 16 : (50 + Math.floor(rng()*40));
        const x = 60 + Math.floor(rng() * (W - 120 - w));
        const y = 60 + Math.floor(rng() * (H - 120 - h));
        const cand = {x,y,w,h};
        const bx = inflate(cand, 34);
        let clear = true;
        for(const wl of existingWalls){ if(rectsOverlap(bx, wl)){ clear = false; break; } }
        for(const p of pillars){ if(rectsOverlap(bx, inflate(p,20))){ clear = false; break; } }
        if(clear) pillars.push(cand);
      }
      return pillars;
    }

    const SHARD_POOL = [
      {x:110,y:150}, {x:790,y:150}, {x:110,y:470}, {x:790,y:470},
      {x:450,y:520}, {x:450,y:100}, {x:230,y:310}, {x:670,y:310},
      {x:110,y:310}, {x:790,y:310},
    ];
    const CONSOLE_POOL = [
      {x:170,y:90}, {x:170,y:470}, {x:450,y:300}, {x:730,y:90}, {x:730,y:470}, {x:450,y:80},
      {x:450,y:540}, {x:60,y:300}, {x:840,y:300}, {x:300,y:520},
    ];

    function posClear(p, walls, margin){
      const box = inflate({x:p.x-4,y:p.y-4,w:8,h:8}, margin);
      for(const w of walls){ if(rectsOverlap(box, w)) return false; }
      return true;
    }
    function pickPositions(pool, count, rng, walls){
      const order = shuffled(pool.map((_,i)=>i), rng);
      const picked = [];
      for(const idx of order){
        if(picked.length >= count) break;
        if(posClear(pool[idx], walls, 16)) picked.push(pool[idx]);
      }
      if(picked.length < count){
        for(const idx of order){
          if(picked.length >= count) break;
          if(!picked.includes(pool[idx])) picked.push(pool[idx]);
        }
      }
      return picked.slice(0, count);
    }

    function buildLevel(chapter){
      const rng = mulberry32(1000 + chapter*97);
      const useA = chapter % 2 === 1;
      let base = useA ? templateA() : templateB();
      const mirror = rng() < 0.5;
      if(mirror) base = base.map(mirrorRect);
      const pillarCount = Math.min(1 + Math.floor(chapter/3), 5);
      const wallsSoFar = outerWalls().concat(base);
      const pillars = seededPillars(rng, pillarCount, wallsSoFar);
      const walls = wallsSoFar.concat(pillars);

      const shardsNeeded = chapter <= 5 ? 3 : (chapter <= 11 ? 4 : 5);
      const totalSpawns = Math.min(shardsNeeded + 2, SHARD_POOL.length);
      const shardSpawns = pickPositions(SHARD_POOL, totalSpawns, rng, walls);

      const consoleCount = Math.min(6 + Math.floor(chapter/4), CONSOLE_POOL.length);
      const consolePositions = pickPositions(CONSOLE_POOL, consoleCount, rng, walls);

      const aiSpeedMult = Math.min(1 + (chapter-1)*0.035, 1.65);
      const maxTraps = Math.min(2 + Math.floor((chapter-1)/6), 4);

      return {
        chapter, walls, shardsNeeded, shardSpawns, consolePositions,
        aiSpeedMult, maxTraps,
        name: 'CHAPTER ' + chapter + (useA ? ' — TWIN VAULTS' : ' — CROSS JUNCTION') + (mirror ? ' (MIRRORED)' : ''),
      };
    }

    const padCyan = {x:60,y:60,r:26};
    const padMag = {x:840,y:560,r:26};

    // ---------- ENTITIES ----------
    const RADIUS = 14;
    function makePlayer(id,color,isAI,startX,startY,pad){
      return {
        id, color, isAI, x:startX, y:startY, vx:0, vy:0, angle:0,
        stun:0, shardCount:0, trapsPlaced:0, maxTraps:2, spdMult:1,
        pad, aiTarget:null, aiSecondaryTarget:null, aiRepathTimer:0,
      };
    }
    let p1, p2, particles, elapsed, gameOver, winner, mode, running;
    let walls = [], consoles = [], shards = [];
    let currentChapter = 1, shardsNeeded = 3;
    let shakeTime=0, shakeMag=0;

    function loadLevel(chapter, forSkirmish){
      const level = buildLevel(chapter);
      walls = level.walls;
      consoles = level.consolePositions.map(p=>({x:p.x,y:p.y,rigged:null,cool:0}));
      shards = level.shardSpawns.map(p=>({x:p.x,y:p.y,taken:false}));
      shardsNeeded = level.shardsNeeded;
      p1.maxTraps = level.maxTraps;
      p2.maxTraps = level.maxTraps;
      p2.spdMult = forSkirmish ? 1 : level.aiSpeedMult;
      currentChapter = chapter;
      hudChapterEl.textContent = forSkirmish ? 'SKIRMISH' : level.name;
    }

    function trapsPlacedActive(playerId){
      return consoles.filter(c=>c.rigged===playerId).length;
    }

    function resetEntities(m){
      mode = m; // 'campaign' | '2p'
      p1 = makePlayer('p1', getComputedStyle(root).getPropertyValue('--cy').trim() || '#00f0ff', false, 70, H-70, padCyan);
      p2 = makePlayer('p2', getComputedStyle(root).getPropertyValue('--mg').trim() || '#ff2e88', mode==='campaign', W-70, 70, padMag);
      particles = [];
      elapsed = 0;
      gameOver = false;
      winner = null;
      running = true;
      p2LabelEl.textContent = mode==='campaign' ? 'RIVAL A.I.' : 'AGENT MAGENTA';
      hud.style.display = 'flex';
      overlay.classList.add('hidden');
      touchWrap.style.display = isTouch ? 'block' : 'none';
    }

    function startCampaign(chapter){
      resetEntities('campaign');
      loadLevel(chapter, false);
      toast(('CHAPTER ' + chapter + ' — INFILTRATION BEGINS'));
      updateHUD();
    }
    function startSkirmish(){
      resetEntities('2p');
      const rngPick = Math.floor(Math.random()*TOTAL_CHAPTERS) + 1;
      loadLevel(rngPick, true);
      updateHUD();
    }

    // ---------- INPUT ----------
    const keysDown = new Set();
    const usedKeys = new Set(['w','a','s','d',' ','arrowup','arrowdown','arrowleft','arrowright','enter']);
    window.addEventListener('keydown', (e)=>{
      const k = e.key.toLowerCase();
      if(usedKeys.has(k)) e.preventDefault();
      if(!keysDown.has(k)){ keysDown.add(k); handleRigPress(k); }
      if(k === 'escape' && root.classList.contains('cc-fullscreen') && !document.fullscreenElement){
        applyFullscreenLayout(false);
      }
    }, {passive:false});
    window.addEventListener('keyup', (e)=>{ keysDown.delete(e.key.toLowerCase()); });

    function handleRigPress(k){
      if(!running || gameOver) return;
      if(k === ' ') tryRig(p1);
      if(k === 'enter' && mode==='2p') tryRig(p2);
    }
    function tryRig(player){
      if(player.stun>0) return;
      if(trapsPlacedActive(player.id) >= player.maxTraps){ toast(player===p1?"CYAN: trap limit reached":"MAGENTA: trap limit reached"); return; }
      let best=null, bd=1e9;
      for(const c of consoles){
        const d = Math.hypot(c.x-player.x, c.y-player.y);
        if(d<48 && d<bd){ bd=d; best=c; }
      }
      if(best && best.rigged !== player.id){
        best.rigged = player.id;
        spawnSparks(best.x,best.y,player.color,10);
        toast((player.id==='p1'?"CYAN":"MAGENTA")+" rigged a console");
      }
    }

    // ---------- TOUCH JOYSTICK ----------
    const isTouch = ('ontouchstart' in window) || (navigator.maxTouchPoints && navigator.maxTouchPoints > 0);
    let joyActive=false, joyId=null, joyDX=0, joyDY=0;
    function joyRect(){ return joyBase.getBoundingClientRect(); }
    function updateJoy(cx,cy){
      const r = joyRect();
      const cX = r.left + r.width/2, cY = r.top + r.height/2;
      let dx = cx-cX, dy = cy-cY;
      const max = r.width/2;
      const dist = Math.hypot(dx,dy);
      if(dist>max){ dx = dx/dist*max; dy = dy/dist*max; }
      joyStick.style.transform = 'translate(' + dx + 'px,' + dy + 'px)';
      joyDX = dx/max; joyDY = dy/max;
    }
    function joyStart(e){
      const t = e.changedTouches ? e.changedTouches[0] : e;
      joyActive = true;
      joyId = e.changedTouches ? t.identifier : 'mouse';
      updateJoy(t.clientX, t.clientY);
      e.preventDefault();
    }
    function joyMove(e){
      if(!joyActive) return;
      let t = null;
      if(e.changedTouches){
        for(const tt of e.changedTouches){ if(tt.identifier===joyId){ t=tt; break; } }
        if(!t) return;
      } else t = e;
      updateJoy(t.clientX, t.clientY);
      e.preventDefault();
    }
    function joyEnd(e){
      if(!joyActive) return;
      if(e.changedTouches){
        let found=false;
        for(const tt of e.changedTouches){ if(tt.identifier===joyId) found=true; }
        if(!found) return;
      }
      joyActive=false; joyDX=0; joyDY=0;
      joyStick.style.transform = 'translate(0,0)';
    }
    joyBase.addEventListener('touchstart', joyStart, {passive:false});
    joyBase.addEventListener('touchmove', joyMove, {passive:false});
    joyBase.addEventListener('touchend', joyEnd);
    joyBase.addEventListener('touchcancel', joyEnd);
    joyBase.addEventListener('mousedown', joyStart);
    window.addEventListener('mousemove', joyMove);
    window.addEventListener('mouseup', joyEnd);
    function actionPress(e){ e.preventDefault(); if(running && !gameOver) tryRig(p1); }
    actionBtn.addEventListener('touchstart', actionPress, {passive:false});
    actionBtn.addEventListener('mousedown', actionPress);

    // ---------- PHYSICS ----------
    const ACCEL = 900, MAXSPD = 210, FRICTION = 6.0;
    function moveEntity(e, dirx, diry, dt){
      const maxspd = MAXSPD * (e.spdMult || 1);
      if(e.stun>0){
        e.stun -= dt;
        e.vx *= (1-Math.min(1,FRICTION*dt));
        e.vy *= (1-Math.min(1,FRICTION*dt));
      } else {
        const len = Math.hypot(dirx,diry);
        if(len>0.001){ dirx/=len; diry/=len; e.angle = Math.atan2(diry,dirx); }
        e.vx += dirx*ACCEL*dt;
        e.vy += diry*ACCEL*dt;
        const spd = Math.hypot(e.vx,e.vy);
        if(spd>maxspd){ e.vx *= maxspd/spd; e.vy *= maxspd/spd; }
        e.vx *= (1-Math.min(1,FRICTION*dt*0.5));
        e.vy *= (1-Math.min(1,FRICTION*dt*0.5));
      }
      let nx = e.x + e.vx*dt;
      let ny = e.y + e.vy*dt;
      const boxAt = (px,py)=>({x:px-RADIUS,y:py-RADIUS,w:RADIUS*2,h:RADIUS*2});
      let bx = boxAt(nx, e.y);
      if(walls.some(w=>rectsOverlap(bx,w))){ nx = e.x; e.vx = 0; }
      let by = boxAt(nx, ny);
      if(walls.some(w=>rectsOverlap(by,w))){ ny = e.y; e.vy = 0; }
      e.x = Math.max(RADIUS+WALL_T, Math.min(W-RADIUS-WALL_T, nx));
      e.y = Math.max(RADIUS+WALL_T, Math.min(H-RADIUS-WALL_T, ny));
    }

    function humanInput(player){
      let dx=0,dy=0;
      if(player===p1){
        if(keysDown.has('w')) dy-=1;
        if(keysDown.has('s')) dy+=1;
        if(keysDown.has('a')) dx-=1;
        if(keysDown.has('d')) dx+=1;
        if(Math.abs(joyDX)>0.08 || Math.abs(joyDY)>0.08){ dx += joyDX; dy += joyDY; }
      } else {
        if(keysDown.has('arrowup')) dy-=1;
        if(keysDown.has('arrowdown')) dy+=1;
        if(keysDown.has('arrowleft')) dx-=1;
        if(keysDown.has('arrowright')) dx+=1;
      }
      return [dx,dy];
    }

    function aiInput(dt){
      const me = p2, foe = p1;
      me.aiRepathTimer -= dt;
      if(me.aiRepathTimer<=0){
        me.aiRepathTimer = 0.5;
        if(me.shardCount>=shardsNeeded){
          me.aiTarget = {x:me.pad.x, y:me.pad.y};
        } else {
          let best=null,bd=1e9;
          for(const s of shards){ if(s.taken) continue; const d=Math.hypot(s.x-me.x,s.y-me.y); if(d<bd){bd=d;best=s;} }
          me.aiTarget = best ? {x:best.x,y:best.y} : {x:me.pad.x,y:me.pad.y};
        }
        if(Math.random()<0.35){
          let nearFoeConsole=null, bd=1e9;
          for(const c of consoles){
            if(c.rigged) continue;
            const d = Math.hypot(c.x-foe.x, c.y-foe.y);
            if(d<220 && d<bd){bd=d; nearFoeConsole=c;}
          }
          me.aiSecondaryTarget = nearFoeConsole || null;
        }
      }
      let target = me.aiTarget;
      if(me.aiSecondaryTarget && trapsPlacedActive('p2') < me.maxTraps){
        const dNear = Math.hypot(me.aiSecondaryTarget.x-me.x, me.aiSecondaryTarget.y-me.y);
        if(dNear>40) target = me.aiSecondaryTarget;
        else { tryRig(me); me.aiSecondaryTarget=null; }
      }
      if(!target) return [0,0];
      let dx = target.x - me.x, dy = target.y - me.y;
      const d = Math.hypot(dx,dy);
      if(d<6) return [0,0];
      return [dx/d, dy/d];
    }

    // ---------- PARTICLES / FX ----------
    function spawnSparks(x,y,color,n){
      for(let i=0;i<n;i++){
        const a = Math.random()*Math.PI*2, sp = 40+Math.random()*140;
        particles.push({x,y,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp,life:0.5+Math.random()*0.4,maxLife:0.9,color,size:2+Math.random()*2});
      }
    }
    function spawnExplosion(x,y){
      for(let i=0;i<26;i++){
        const a = Math.random()*Math.PI*2, sp = 60+Math.random()*220;
        particles.push({x,y,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp,life:0.5+Math.random()*0.5,maxLife:1,color: Math.random()<0.5?'#ff5533':'#ffcc33',size:2+Math.random()*3});
      }
      shakeTime = 0.4; shakeMag = 9;
    }
    function updateParticles(dt){
      for(let i=particles.length-1;i>=0;i--){
        const p = particles[i];
        p.x += p.vx*dt; p.y += p.vy*dt;
        p.vx *= (1-2.2*dt); p.vy *= (1-2.2*dt);
        p.life -= dt;
        if(p.life<=0) particles.splice(i,1);
      }
    }

    // ---------- GAME LOGIC ----------
    function toast(msg){
      toastEl.textContent = msg;
      toastEl.classList.add('show');
      clearTimeout(toastEl._t);
      toastEl._t = setTimeout(()=>toastEl.classList.remove('show'), 1600);
    }
    function checkShardPickup(player){
      for(const s of shards){
        if(!s.taken && Math.hypot(s.x-player.x,s.y-player.y)<22){
          s.taken = true;
          player.shardCount++;
          spawnSparks(s.x,s.y,'#ffcc33',16);
          toast((player.id==='p1'?"CYAN":(mode==='campaign'?"RIVAL":"MAGENTA"))+" acquired a data shard ("+player.shardCount+"/"+shardsNeeded+")");
        }
      }
    }
    function checkTrapTrigger(player){
      for(const c of consoles){
        if(c.rigged && c.rigged !== player.id && c.cool<=0){
          const d = Math.hypot(c.x-player.x,c.y-player.y);
          if(d<26){
            c.cool = 0.05;
            c.rigged = null;
            player.stun = 1.4;
            const ang = Math.atan2(player.y-c.y, player.x-c.x);
            player.vx = Math.cos(ang)*260; player.vy = Math.sin(ang)*260;
            spawnExplosion(c.x,c.y);
            toast((player.id==='p1'?"CYAN":(mode==='campaign'?"RIVAL":"MAGENTA"))+" got zapped!");
          }
        }
      }
    }
    function checkExtraction(player){
      const pad = player.pad;
      if(player.shardCount>=shardsNeeded && Math.hypot(player.x-pad.x,player.y-pad.y)<pad.r){
        gameOver = true;
        winner = player.id;
        running = false;
      }
    }

    function updateHUD(){
      barP1.style.width = Math.min(100,(p1.shardCount/shardsNeeded)*100)+'%';
      barP2.style.width = Math.min(100,(p2.shardCount/shardsNeeded)*100)+'%';
      trapsP1El.textContent = 'TRAPS: ' + '●'.repeat(Math.max(0,p1.maxTraps-trapsPlacedActive('p1'))) + '○'.repeat(trapsPlacedActive('p1'));
      trapsP2El.textContent = 'TRAPS: ' + '●'.repeat(Math.max(0,p2.maxTraps-trapsPlacedActive('p2'))) + '○'.repeat(trapsPlacedActive('p2'));
      const remaining = shards.filter(s=>!s.taken).length;
      shardPoolEl.textContent = 'SHARDS LEFT: ' + remaining + ' / NEED ' + shardsNeeded;
      const mm = Math.floor(elapsed/60).toString().padStart(2,'0');
      const ss = Math.floor(elapsed%60).toString().padStart(2,'0');
      timerEl.textContent = mm+':'+ss;
    }

    const menuHTML = panelMenu.innerHTML;
    function backToMenu(){
      running=false; gameOver=false; hud.style.display='none'; touchWrap.style.display='none';
      panelMenu.innerHTML = menuHTML;
      wireMenuButtons();
      overlay.classList.remove('hidden');
    }
    function wireMenuButtons(){
      root.querySelector('#cc-btn-campaign').addEventListener('click', ()=>startCampaign(maxChapterReached));
      root.querySelector('#cc-btn-chapters').addEventListener('click', showChapterSelect);
      root.querySelector('#cc-btn-2p').addEventListener('click', startSkirmish);
    }
    function showChapterSelect(){
      let grid = '<div class="cc-chapgrid">';
      for(let i=1;i<=TOTAL_CHAPTERS;i++){
        const unlocked = i <= maxChapterReached;
        grid += '<button class="cc-chapbtn ' + (unlocked?'unlocked':'') + '" data-ch="' + i + '" ' + (unlocked?'':'disabled') + '>CH ' + i + '</button>';
      }
      grid += '</div>';
      panelMenu.innerHTML = '<div class="cc-title" style="font-size:clamp(20px,4.5vw,32px)">CHAPTER SELECT</div>' +
        '<div class="cc-sub">' + maxChapterReached + ' / ' + TOTAL_CHAPTERS + ' UNLOCKED</div>' +
        grid +
        '<div class="cc-row"><button class="cc-btn mg" id="cc-btn-back">Back</button></div>';
      panelMenu.querySelectorAll('.cc-chapbtn.unlocked').forEach(b=>{
        b.addEventListener('click', ()=> startCampaign(parseInt(b.getAttribute('data-ch'),10)) );
      });
      root.querySelector('#cc-btn-back').addEventListener('click', backToMenu);
    }
    function showWin(){
      hud.style.display='none';
      touchWrap.style.display='none';
      overlay.classList.remove('hidden');
      if(mode==='campaign'){
        if(winner==='p1'){
          maxChapterReached = Math.max(maxChapterReached, currentChapter+1 > TOTAL_CHAPTERS ? TOTAL_CHAPTERS : currentChapter+1);
          saveProgress(maxChapterReached);
          const finished = currentChapter >= TOTAL_CHAPTERS;
          panelMenu.innerHTML =
            '<div class="cc-title" style="font-size:clamp(20px,5vw,34px)">' + (finished ? 'CAMPAIGN COMPLETE' : 'CHAPTER COMPLETE') + '</div>' +
            '<div class="cc-winline" style="color:var(--cy)">AGENT CYAN extracted with the data</div>' +
            '<div class="cc-row">' +
              (finished ? '' : '<button class="cc-btn" id="cc-btn-next">Next Chapter</button>') +
              '<button class="cc-btn gold" id="cc-btn-replay">Replay Chapter</button>' +
              '<button class="cc-btn mg" id="cc-btn-menu">Main Menu</button>' +
            '</div>';
          if(!finished){
            root.querySelector('#cc-btn-next').addEventListener('click', ()=>startCampaign(currentChapter+1));
          }
          root.querySelector('#cc-btn-replay').addEventListener('click', ()=>startCampaign(currentChapter));
          root.querySelector('#cc-btn-menu').addEventListener('click', backToMenu);
        } else {
          panelMenu.innerHTML =
            '<div class="cc-title" style="font-size:clamp(20px,5vw,34px)">CHAPTER FAILED</div>' +
            '<div class="cc-winline" style="color:var(--mg)">The rival A.I. extracted first</div>' +
            '<div class="cc-row">' +
              '<button class="cc-btn" id="cc-btn-retry">Retry Chapter</button>' +
              '<button class="cc-btn mg" id="cc-btn-menu">Main Menu</button>' +
            '</div>';
          root.querySelector('#cc-btn-retry').addEventListener('click', ()=>startCampaign(currentChapter));
          root.querySelector('#cc-btn-menu').addEventListener('click', backToMenu);
        }
      } else {
        const who = winner==='p1' ? 'AGENT CYAN' : 'AGENT MAGENTA';
        panelMenu.innerHTML =
          '<div class="cc-title" style="font-size:clamp(20px,5vw,34px)">MISSION COMPLETE</div>' +
          '<div class="cc-winline" style="color:' + (winner==='p1'?'var(--cy)':'var(--mg)') + '">' + who + ' extracted with the data</div>' +
          '<div class="cc-row">' +
            '<button class="cc-btn" id="cc-btn-again">Play Again</button>' +
            '<button class="cc-btn mg" id="cc-btn-menu">Main Menu</button>' +
          '</div>';
        root.querySelector('#cc-btn-again').addEventListener('click', startSkirmish);
        root.querySelector('#cc-btn-menu').addEventListener('click', backToMenu);
      }
    }

    // ---------- RENDER ----------
    function drawGrid(t){
      ctx.fillStyle = '#05070d';
      ctx.fillRect(0,0,W,H);
      ctx.save();
      ctx.strokeStyle = 'rgba(0,240,255,0.05)';
      ctx.lineWidth = 1;
      const off = (t*12)%40;
      for(let x=-40+off;x<W;x+=40){ ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke(); }
      for(let y=-40+off;y<H;y+=40){ ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke(); }
      ctx.restore();
    }
    function drawWalls(){
      for(const w of walls){
        const g = ctx.createLinearGradient(w.x,w.y,w.x,w.y+w.h);
        g.addColorStop(0,'#16324a'); g.addColorStop(1,'#0a1a28');
        ctx.fillStyle = g;
        ctx.fillRect(w.x,w.y,w.w,w.h);
        ctx.strokeStyle = 'rgba(0,240,255,0.35)';
        ctx.lineWidth = 1;
        ctx.strokeRect(w.x+0.5,w.y+0.5,w.w-1,w.h-1);
      }
    }
    function drawPad(pad,color,ready,t){
      ctx.save();
      ctx.translate(pad.x,pad.y);
      for(let i=0;i<3;i++){
        const r = pad.r*0.5 + (t*40 + i*18)%40;
        ctx.beginPath(); ctx.arc(0,0,r,0,Math.PI*2);
        ctx.strokeStyle = color+(ready? 'cc':'33');
        ctx.lineWidth = 2;
        ctx.stroke();
      }
      ctx.beginPath(); ctx.arc(0,0,pad.r,0,Math.PI*2);
      ctx.fillStyle = ready? color+'22' : '#0a1622';
      ctx.fill();
      ctx.strokeStyle = color; ctx.lineWidth=2; ctx.stroke();
      ctx.restore();
    }
    function drawConsole(c,t){
      ctx.save();
      ctx.translate(c.x,c.y);
      const pulse = 0.6+0.4*Math.sin(t*4);
      let col = '#3a5a6b', glow=null;
      if(c.rigged==='p1'){ col='#00f0ff'; glow='#00f0ff'; }
      else if(c.rigged==='p2'){ col='#ff2e88'; glow='#ff2e88'; }
      if(glow){ ctx.shadowColor = glow; ctx.shadowBlur = 14*pulse; }
      ctx.fillStyle = col;
      ctx.beginPath();
      const s=10;
      ctx.moveTo(0,-s); ctx.lineTo(s,0); ctx.lineTo(0,s); ctx.lineTo(-s,0); ctx.closePath();
      ctx.fill();
      ctx.shadowBlur=0;
      ctx.strokeStyle = '#0a1622'; ctx.lineWidth=1.5; ctx.stroke();
      ctx.restore();
    }
    function drawShard(s,t){
      if(s.taken) return;
      ctx.save();
      ctx.translate(s.x,s.y);
      ctx.rotate(t*1.6);
      ctx.shadowColor = '#ffcc33'; ctx.shadowBlur = 12;
      ctx.fillStyle = '#ffcc33';
      ctx.beginPath();
      ctx.moveTo(0,-9); ctx.lineTo(7,0); ctx.lineTo(0,9); ctx.lineTo(-7,0); ctx.closePath();
      ctx.fill();
      ctx.restore();
    }
    function drawPlayer(pl){
      ctx.save();
      ctx.translate(pl.x,pl.y);
      const flash = pl.stun>0 && Math.floor(pl.stun*14)%2===0;
      ctx.shadowColor = pl.color; ctx.shadowBlur = flash? 2 : 16;
      ctx.fillStyle = flash ? '#552222' : pl.color;
      ctx.beginPath(); ctx.arc(0,0,RADIUS,0,Math.PI*2); ctx.fill();
      ctx.shadowBlur=0;
      ctx.strokeStyle = '#05070d'; ctx.lineWidth=2; ctx.stroke();
      ctx.rotate(pl.angle);
      ctx.fillStyle = '#05070d';
      ctx.beginPath(); ctx.moveTo(RADIUS-2,0); ctx.lineTo(RADIUS-9,-5); ctx.lineTo(RADIUS-9,5); ctx.closePath(); ctx.fill();
      ctx.restore();
      if(pl.stun>0){
        ctx.save();
        ctx.translate(pl.x,pl.y-RADIUS-14);
        ctx.font = '11px monospace';
        ctx.fillStyle = '#ffcc33';
        ctx.textAlign='center';
        ctx.fillText('⚡ STUNNED', 0, 0);
        ctx.restore();
      }
    }
    function drawParticles(){
      for(const p of particles){
        const a = Math.max(0,p.life/p.maxLife);
        ctx.globalAlpha = a;
        ctx.fillStyle = p.color;
        ctx.beginPath(); ctx.arc(p.x,p.y,p.size,0,Math.PI*2); ctx.fill();
      }
      ctx.globalAlpha = 1;
    }
    function drawScanlines(){
      ctx.save();
      ctx.globalAlpha = 0.05;
      ctx.fillStyle = '#000';
      for(let y=0;y<H;y+=3){ ctx.fillRect(0,y,W,1); }
      ctx.restore();
    }

    let lastT = performance.now();
    function loop(now){
      requestAnimationFrame(loop);
      let dt = (now-lastT)/1000;
      lastT = now;
      dt = Math.min(dt,0.033);
      const t = now/1000;

      if(running && !gameOver && p1){
        elapsed += dt;
        const [d1x,d1y] = humanInput(p1);
        moveEntity(p1, d1x, d1y, dt);
        if(mode==='2p'){
          const [d2x,d2y] = humanInput(p2);
          moveEntity(p2, d2x, d2y, dt);
        } else {
          const [d2x,d2y] = aiInput(dt);
          moveEntity(p2, d2x, d2y, dt);
        }
        checkShardPickup(p1); checkShardPickup(p2);
        checkTrapTrigger(p1); checkTrapTrigger(p2);
        checkExtraction(p1); checkExtraction(p2);
        updateParticles(dt);
        if(shakeTime>0) shakeTime-=dt;
        updateHUD();
        if(gameOver) showWin();
      }

      ctx.save();
      if(shakeTime>0){
        const m = shakeMag * (shakeTime/0.4);
        ctx.translate((Math.random()*2-1)*m, (Math.random()*2-1)*m);
      }
      drawGrid(t);
      drawWalls();
      drawPad(padCyan, '#00f0ff', p1 ? p1.shardCount>=shardsNeeded : false, t);
      drawPad(padMag, '#ff2e88', p2 ? p2.shardCount>=shardsNeeded : false, t);
      for(const c of consoles) drawConsole(c,t);
      for(const s of shards) drawShard(s,t);
      drawParticles();
      if(p1) drawPlayer(p1);
      if(p2) drawPlayer(p2);
      drawScanlines();
      ctx.restore();
    }
    requestAnimationFrame(loop);

    // ---------- FULLSCREEN ----------
    function fitStage(){
      if(!root.classList.contains('cc-fullscreen')) return;
      const maxW = window.innerWidth;
      const maxH = window.innerHeight;
      const scale = Math.min(maxW/900, maxH/620);
      stage.style.width = Math.floor(900*scale)+'px';
      stage.style.height = Math.floor(620*scale)+'px';
    }
    function applyFullscreenLayout(on){
      if(on){ root.classList.add('cc-fullscreen'); }
      else { root.classList.remove('cc-fullscreen'); stage.style.width=''; stage.style.height=''; }
      fitStage();
    }
    async function toggleFullscreen(){
      const wantOn = !root.classList.contains('cc-fullscreen');
      if(wantOn){
        try{
          if(root.requestFullscreen) await root.requestFullscreen();
          else if(root.webkitRequestFullscreen) root.webkitRequestFullscreen();
        }catch(e){ /* native fullscreen blocked in this embed — CSS fallback still fills the frame */ }
        applyFullscreenLayout(true);
      } else {
        applyFullscreenLayout(false);
        try{
          if(document.fullscreenElement) await document.exitFullscreen();
          else if(document.webkitFullscreenElement) document.webkitExitFullscreen();
        }catch(e){}
      }
    }
    document.addEventListener('fullscreenchange', ()=>{
      if(!document.fullscreenElement && root.classList.contains('cc-fullscreen')) applyFullscreenLayout(false);
    });
    window.addEventListener('resize', fitStage);
    window.addEventListener('orientationchange', ()=>setTimeout(fitStage,200));
    btnFs.addEventListener('click', toggleFullscreen);
    btnRestart2.addEventListener('click', ()=>{
      if(!mode) return;
      if(mode==='campaign') startCampaign(currentChapter);
      else startSkirmish();
    });

    // ---------- INIT ----------
    wireMenuButtons();
    if(isTouch) touchWrap.style.display = 'none';
    running = false;
  })();
  </script>
</div>
"""

components.html(GAME_HTML, height=780, scrolling=False)

with st.expander("How to play"):
    st.markdown(
        """
- **Campaign:** 16 chapters vs the Rival A.I. Each chapter is a procedurally-varied
  facility layout — alternating structural templates, mirrored orientations, extra
  hazard pillars, more consoles, more required shards, and a faster rival as you climb
  the chapter ladder. Win a chapter to unlock the next; progress is saved in your browser.
- **Chapter Select:** jump straight to any chapter you've already unlocked.
- **2P Skirmish:** local same-keyboard match on a random layout — no progress needed.
- **Move:** Agent Cyan uses `W A S D`. Agent Magenta (2-player mode) uses the arrow keys.
  On a touch device, use the on-screen stick (bottom-left) and RIG button (bottom-right).
- **Rig a trap:** stand near a console and press `SPACE` (Cyan) / `ENTER` (Magenta) /
  tap **RIG** on touch. It only zaps the *other* agent.
- **Fullscreen:** tap the ⛶ icon in the top-right of the game to expand to fullscreen
  on desktop or mobile; press `Esc` or tap it again to exit.
        """
    )

st.caption(
    "Built with an HTML5 canvas game engine (custom physics, particle effects, seeded "
    "procedural level generation, and a simple AI) embedded in Streamlit. "
    "Refresh the page to fully reset campaign progress."
)
