/* ═══════════════════════════════════════════════════════════
   WORD SENSE — game.js
   All game state, API calls, and UI updates live here.
   Backend base URL is controlled by API_BASE at the top.
   ═══════════════════════════════════════════════════════════ */

// ── Config ────────────────────────────────────────────────────────────────────
// Change this to your Vercel URL when you deploy the backend.
// In local dev mode (USE_MOCK = true) no real API calls are made.
const API_BASE  = "http://localhost:8000";
const USE_MOCK  = true;   // ← flip to false once the backend is live

// ── DOM refs ─────────────────────────────────────────────────────────────────
const scoreEl      = document.getElementById("score");
const roundEl      = document.getElementById("round");
const wordPtsEl    = document.getElementById("word-pts");
const wordsLeftEl  = document.getElementById("words-left");
const letterRow    = document.getElementById("letter-row");
const semPctEl     = document.getElementById("sem-pct");
const thermoFill   = document.getElementById("thermo-fill");
const tempLabelEl  = document.getElementById("temp-label");
const radarCircle  = document.getElementById("radar-circle");
const radarEmoji   = document.getElementById("radar-emoji");
const clueList     = document.getElementById("clue-list");
const cluePlaceholder = document.getElementById("clue-placeholder");
const guessLog     = document.getElementById("guess-log");
const guessInput   = document.getElementById("guess-input");
const submitBtn    = document.getElementById("submit-btn");
const hintBtn      = document.getElementById("hint-btn");
const skipBtn      = document.getElementById("skip-btn");
const feedbackBanner = document.getElementById("feedback-banner");
const nextBtn      = document.getElementById("next-btn");
const toast        = document.getElementById("toast");
const apiBadge     = document.getElementById("api-badge");

// ── Game State ────────────────────────────────────────────────────────────────
const state = {
  totalScore:    0,
  roundNumber:   0,
  wordLength:    0,
  wordScore:     0,
  firstLetter:   "",
  currentTarget: null,   // only known client-side in mock mode
  hintsUsed:     0,
  roundOver:     false,
};

// ── Temperature config ────────────────────────────────────────────────────────
const TEMPS = [
  { min: 0,  max: 15,  label: "❄  COLD — Unrelated concept",        color: "#94a3b8", emoji: "🥶", borderVar: "pbox-blue"  },
  { min: 15, max: 35,  label: "🌊 COOL — Slightly related",          color: "#60a5fa", emoji: "💧", borderVar: "pbox-blue"  },
  { min: 35, max: 60,  label: "⚠  WARM — Getting close in meaning",  color: "#fbbf24", emoji: "🌡️", borderVar: "pbox-yellow"},
  { min: 60, max: 85,  label: "🔥 HOT  — Right concept!",            color: "#f97316", emoji: "🔥", borderVar: "pbox-red"   },
  { min: 85, max: 101, label: "🚀 BOILING — You're right there!",    color: "#ef4444", emoji: "🚀", borderVar: "pbox-red"   },
];

function tempForPct(pct) {
  return TEMPS.find(t => pct >= t.min && pct < t.max) || TEMPS[0];
}

// ── Toast ─────────────────────────────────────────────────────────────────────
let toastTimer;
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 3000);
}

// ── Tile helpers ──────────────────────────────────────────────────────────────
function buildTiles(length, firstLetter) {
  letterRow.innerHTML = "";
  for (let i = 0; i < length; i++) {
    const div = document.createElement("div");
    div.className = "tile" + (i === 0 ? " revealed" : "");
    div.textContent = i === 0 ? firstLetter.toUpperCase() : "_";
    div.dataset.index = i;
    letterRow.appendChild(div);
  }
}

function revealAllTiles(word) {
  const tiles = letterRow.querySelectorAll(".tile");
  word.toUpperCase().split("").forEach((ch, i) => {
    setTimeout(() => {
      if (tiles[i]) {
        tiles[i].textContent = ch;
        tiles[i].className = "tile correct";
      }
    }, i * 80);
  });
}

// ── Thermometer ───────────────────────────────────────────────────────────────
function setThermo(pct) {
  const t = tempForPct(pct);
  thermoFill.style.width = pct + "%";
  semPctEl.textContent   = pct.toFixed(1) + "%";
  tempLabelEl.textContent = t.label;
  tempLabelEl.style.color = t.color;
  radarEmoji.textContent  = t.emoji;

  // Recolour radar rings
  document.querySelectorAll(".ring").forEach(r => {
    r.style.borderColor = t.color;
  });
}

// ── Score counter animation ───────────────────────────────────────────────────
function animateScore(from, to) {
  const duration = 600;
  const start = performance.now();
  function tick(now) {
    const p = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1 - p, 3);
    scoreEl.textContent = Math.round(from + (to - from) * ease);
    if (p < 1) requestAnimationFrame(tick);
    else scoreEl.textContent = to;
  }
  requestAnimationFrame(tick);
}

// ── Guess log ─────────────────────────────────────────────────────────────────
function addGuessRow(guess, result) {
  const t = tempForPct(result.semantic_pct || 0);

  const row = document.createElement("div");
  row.className = "guess-row";
  row.style.borderLeftColor = t.color;

  let extra = "";
  if (result.is_antonym) {
    extra += `<span class="guess-antonym">⟺ ANTONYM</span>`;
  }
  if (result.is_likely_typo) {
    extra += `<span class="guess-spell">📝 Spelling: ${result.spelling_pct}%</span>`;
  }

  row.innerHTML = `
    <span class="guess-word">${guess}</span>
    ${extra}
    <span class="guess-spell">✏ ${result.spelling_pct?.toFixed(1) ?? "—"}%</span>
    <span class="guess-temp" style="color:${t.color}">${result.semantic_pct?.toFixed(1) ?? "—"}%</span>
  `;

  // newest on top
  guessLog.prepend(row);
}

// ── Clue / Hint display ───────────────────────────────────────────────────────
function addClue(type, text, accentColor = "var(--purple-lt)") {
  if (cluePlaceholder) cluePlaceholder.style.display = "none";

  const card = document.createElement("div");
  card.className = "clue-card";
  card.style.borderLeftColor = accentColor;
  card.innerHTML = `<div class="clue-type" style="color:${accentColor}">${type}</div>${text}`;
  clueList.appendChild(card);
}

// ── Control lock / unlock ─────────────────────────────────────────────────────
function lockControls() {
  guessInput.disabled = true;
  submitBtn.disabled  = true;
  hintBtn.disabled    = true;
  skipBtn.disabled    = true;
}

function unlockControls() {
  guessInput.disabled = false;
  submitBtn.disabled  = false;
  hintBtn.disabled    = false;
  skipBtn.disabled    = false;
  guessInput.focus();
}

// ── Mock data bank (used when USE_MOCK = true) ────────────────────────────────
const MOCK_WORDS = [
  {
    word: "species",   length: 7,  firstLetter: "s", score: 70,
    definition: "A group of organisms sharing common characteristics and capable of interbreeding.",
    examples: [
      "The _______ of finches Darwin observed differed in beak shape.",
      "Over 8 million _______ are estimated to live on Earth."
    ]
  },
  {
    word: "eclipse",   length: 7,  firstLetter: "e", score: 70,
    definition: "An astronomical event where one celestial body moves into the shadow of another.",
    examples: [
      "The solar _______ left the city in total darkness for two minutes.",
      "Ancient cultures feared the lunar _______ as a bad omen."
    ]
  },
  {
    word: "metaphor",  length: 8,  firstLetter: "m", score: 80,
    definition: "A figure of speech in which a word or phrase is applied to something it doesn't literally denote.",
    examples: [
      "\"Life is a journey\" is a common _______ used in poetry.",
      "He used a powerful _______ to describe his grief."
    ]
  },
  {
    word: "neuron",    length: 6,  firstLetter: "n", score: 60,
    definition: "A specialised cell transmitting nerve impulses throughout the body.",
    examples: [
      "Each _______ can connect to thousands of other cells.",
      "The _______ fired rapidly as the subject processed the image."
    ]
  },
  {
    word: "gravity",   length: 7,  firstLetter: "g", score: 70,
    definition: "The natural force that attracts objects with mass towards one another.",
    examples: [
      "Isaac Newton described _______ after observing a falling apple.",
      "Without _______, the astronaut floated freely inside the capsule."
    ]
  },
];

let mockIndex    = 0;
let mockCurrent  = null;
let mockHintIdx  = 0;
let usedIndices  = [];

function getMockWord() {
  // Prevent repeats within session
  const available = MOCK_WORDS
    .map((w, i) => i)
    .filter(i => !usedIndices.includes(i));

  if (available.length === 0) return null;

  const idx = available[Math.floor(Math.random() * available.length)];
  usedIndices.push(idx);
  mockCurrent  = MOCK_WORDS[idx];
  mockHintIdx  = 0;
  return {
    word_length:     mockCurrent.length,
    first_letter:    mockCurrent.firstLetter,
    potential_score: mockCurrent.score,
  };
}

function getMockHint() {
  if (!mockCurrent) return { hint: "No active round." };
  if (mockHintIdx === 0) {
    mockHintIdx++;
    return { type: "📖 Definition", hint: mockCurrent.definition };
  }
  const ex = mockCurrent.examples[mockHintIdx - 1];
  mockHintIdx++;
  return ex
    ? { type: "✏️ Example", hint: ex }
    : { type: "ℹ️ Info", hint: "No more hints available for this word!" };
}

function getMockGuess(guess) {
  if (!mockCurrent) return { status: "error" };
  const g = guess.trim().toLowerCase();
  const t = mockCurrent.word.toLowerCase();

  if (g === t) {
    return { status: "correct", earned_score: state.wordScore, total_score: state.totalScore + state.wordScore };
  }

  // Fake semantic similarity based on string overlap for demo
  const spelling_pct = Math.round(
    [...g].filter((c, i) => c === (t[i] || "")).length / Math.max(g.length, t.length) * 100 +
    Math.random() * 20
  );

  // Pseudo-semantic based on shared chars
  const sharedChars = new Set([...g].filter(c => t.includes(c))).size;
  const semantic_pct = Math.min(95, Math.round(sharedChars / t.length * 100 * (0.6 + Math.random() * 0.8)));

  return {
    status:       "incorrect",
    spelling_pct: Math.min(99, spelling_pct),
    semantic_pct: Math.min(95, semantic_pct),
    is_antonym:   false,
    is_likely_typo: spelling_pct >= 85,
    temperature:  tempForPct(semantic_pct).label,
  };
}

// ── API wrappers ──────────────────────────────────────────────────────────────
async function apiStartRound() {
  if (USE_MOCK) return getMockWord();
  const res = await fetch(`${API_BASE}/start_round`, { method: "POST" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function apiHint() {
  if (USE_MOCK) return getMockHint();
  const res = await fetch(`${API_BASE}/hint`, { method: "POST" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function apiGuess(guess) {
  if (USE_MOCK) return getMockGuess(guess);
  const res = await fetch(`${API_BASE}/guess`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ guess }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function apiSkip() {
  if (USE_MOCK) return { target_word: mockCurrent?.word ?? "???" };
  const res = await fetch(`${API_BASE}/skip`, { method: "POST" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Round lifecycle ───────────────────────────────────────────────────────────
async function startRound() {
  feedbackBanner.style.display = "none";
  nextBtn.style.display        = "none";
  clueList.innerHTML           = `<p id="clue-placeholder" style="color:var(--muted);font-size:.85rem;font-style:italic;">Press 💡 Hint to reveal clues…</p>`;
  guessLog.innerHTML           = `<p style="color:var(--muted);font-size:.82rem;font-style:italic;">No guesses yet this round.</p>`;
  setThermo(0);

  lockControls();
  submitBtn.innerHTML = `<span class="loader"></span> Loading…`;

  try {
    const data = await apiStartRound();

    if (!data) {
      showToast("🎉 All words played! Resetting session…");
      usedIndices = [];
      await startRound();
      return;
    }

    state.wordLength   = data.word_length;
    state.wordScore    = data.potential_score;
    state.firstLetter  = data.first_letter;
    state.hintsUsed    = 0;
    state.roundOver    = false;
    state.roundNumber += 1;

    roundEl.textContent   = state.roundNumber;
    wordPtsEl.textContent = state.wordScore;
    buildTiles(state.wordLength, state.firstLetter);
    unlockControls();
    submitBtn.innerHTML = "▶ Guess";

    // Words left: total pool minus how many have been used
    const total     = USE_MOCK ? MOCK_WORDS.length : "?";
    const used      = USE_MOCK ? usedIndices.length : state.roundNumber;
    const remaining = USE_MOCK ? (MOCK_WORDS.length - usedIndices.length) : "?";
    wordsLeftEl.textContent = `${remaining}/${total}`;

    showToast(`Round ${state.roundNumber} started — ${state.wordLength}-letter word!`);
  } catch (err) {
    submitBtn.innerHTML = "▶ Guess";
    unlockControls();
    showToast("⚠ Error loading word. Retrying…");
    console.error(err);
    setTimeout(startRound, 2000);
  }
}

// ── Hint handler ──────────────────────────────────────────────────────────────
async function requestHint() {
  if (state.roundOver) return;
  hintBtn.disabled = true;

  try {
    const data = await apiHint();
    state.hintsUsed++;

    // Deduct score for hints
    const newScore = Math.max(5, Math.floor(state.wordScore * (state.hintsUsed === 1 ? 0.7 : 0.85)));
    state.wordScore = newScore;
    wordPtsEl.textContent = newScore;

    if (data.hint === "No more hints available for this word!") {
      showToast("No more hints for this word!");
    } else {
      addClue(data.type || "💡 Hint", data.hint);
    }
  } catch (err) {
    showToast("⚠ Could not fetch hint.");
    console.error(err);
  } finally {
    hintBtn.disabled = false;
  }
}

// ── Guess handler ─────────────────────────────────────────────────────────────
async function submitGuess() {
  if (state.roundOver) return;
  const raw = guessInput.value.trim();
  if (!raw) { guessInput.focus(); return; }

  const guess = raw.toLowerCase();
  guessInput.value = "";
  lockControls();
  submitBtn.innerHTML = `<span class="loader"></span>`;

  try {
    const result = await apiGuess(guess);

    if (result.status === "correct") {
      // ── Correct ──
      const earned = result.earned_score ?? state.wordScore;
      const prev   = state.totalScore;
      state.totalScore = result.total_score ?? (state.totalScore + earned);

      animateScore(prev, state.totalScore);
      revealAllTiles(USE_MOCK ? mockCurrent.word : guess);
      setThermo(100);

      feedbackBanner.style.display = "flex";
      feedbackBanner.style.color   = "#4ade80";
      feedbackBanner.style.background = "rgba(74,222,128,0.08)";
      feedbackBanner.style.border  = "2px solid #4ade80";
      feedbackBanner.innerHTML     = `🎉 CORRECT! +${earned} pts`;

      nextBtn.style.display = "block";
      nextBtn.textContent   = "▶ NEXT WORD";
      state.roundOver = true;
      submitBtn.innerHTML = "▶ Guess";

    } else {
      // ── Incorrect ──
      const pct = result.semantic_pct ?? 0;
      setThermo(pct);
      addGuessRow(guess, result);

      // Brief shake on input
      guessInput.style.animation = "none";
      void guessInput.offsetWidth;
      guessInput.style.animation = "shake 0.3s ease";

      submitBtn.innerHTML = "▶ Guess";
      unlockControls();

      if (result.is_antonym) showToast("⟺ That's the opposite word!");
      else if (result.is_likely_typo) showToast(`📝 Almost! Check your spelling (${result.spelling_pct}% match)`);
    }
  } catch (err) {
    submitBtn.innerHTML = "▶ Guess";
    unlockControls();
    showToast("⚠ Error checking guess.");
    console.error(err);
  }
}

// ── Skip handler ──────────────────────────────────────────────────────────────
async function skipWord() {
  if (state.roundOver) return;
  lockControls();

  try {
    const data = await apiSkip();
    const word  = data.target_word ?? "???";

    revealAllTiles(word);
    setThermo(0);

    feedbackBanner.style.display = "flex";
    feedbackBanner.style.color   = "#f87171";
    feedbackBanner.style.background = "rgba(248,113,113,0.08)";
    feedbackBanner.style.border  = "2px solid #f87171";
    feedbackBanner.innerHTML     = `⏭ Skipped — the word was <b style="margin-left:6px">${word.toUpperCase()}</b>`;

    nextBtn.style.display = "block";
    nextBtn.textContent   = "▶ TRY NEXT WORD";
    state.roundOver = true;
    submitBtn.innerHTML = "▶ Guess";
  } catch (err) {
    unlockControls();
    submitBtn.innerHTML = "▶ Guess";
    showToast("⚠ Error skipping.");
    console.error(err);
  }
}

// ── Keyboard shortcut (Enter) ─────────────────────────────────────────────────
guessInput.addEventListener("keydown", e => {
  if (e.key === "Enter") submitGuess();
});

// ── Shake keyframe (injected) ─────────────────────────────────────────────────
const shakeStyle = document.createElement("style");
shakeStyle.textContent = `
  @keyframes shake {
    0%,100%{transform:translateX(0)}
    20%{transform:translateX(-6px)}
    40%{transform:translateX(6px)}
    60%{transform:translateX(-4px)}
    80%{transform:translateX(4px)}
  }
`;
document.head.appendChild(shakeStyle);

// ── Badge ─────────────────────────────────────────────────────────────────────
apiBadge.textContent = USE_MOCK ? "⚙ MOCK MODE" : "🌐 LIVE API";
apiBadge.style.color = USE_MOCK ? "var(--yellow-lt)" : "var(--green-lt)";
apiBadge.style.borderColor = USE_MOCK ? "var(--yellow)" : "var(--green)";

// ── Boot ──────────────────────────────────────────────────────────────────────
startRound();
