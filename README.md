Weather-Advisory Support Bot

A LangGraph-backed chat bot that answers outdoor-activity safety questions ("is it safe to cycle today?") using live Open-Meteo data and a written set of Standard Operating Procedures (SOPs). Every answer is either traced back to a specific SOP or the bot says honestly that no guidance applies — it never invents advice or a forecast.


- **resolve_location** — geocodes the city name via Open-Meteo's geocoding endpoint.
  On failure (no result, or the API errors), routes to `error_fallback` instead of
  guessing coordinates.
- **fetch_weather** — calls `/v1/forecast` with explicit `current=` fields for that
  location. On failure, routes to `error_fallback`.
- **classify_intent** — an LLM call that tags the user's question with one of a fixed
  set of activity tags (`cycling`, `commute`, `picnic`, `unknown`, etc.), using recent
  conversation history so follow-ups like "what about this evening instead?" resolve
  correctly. The LLM only classifies intent here — it never sees or touches the actual
  weather numbers at this stage.
- **match_sop** — pure deterministic code. Filters SOPs to ones relevant to the
  classified activity (or `activity: any`), evaluates each SOP's numeric
  `condition_check` against the real weather dict, and if more than one SOP matches,
  picks the highest-severity one (see "Conflict resolution" below).
- **fuzzy_check** (only reached if no numeric SOP matched) — for SOPs with no clean
  threshold (e.g. "is today good for a picnic"), the LLM is given only the SOP's written
  description and the real weather numbers, and asked a strict YES/NO: does this weather
  satisfy the description. The model is not allowed to invent its own picnic criteria —
  it's judging against the SOP text, nothing else.
- **compose** — pure string formatting. Fills the matched SOP's advice template with the
  actual weather dict values (`str.format(**weather)`), so any number in the final
  answer is guaranteed to have come from the API response, not the model's memory.
- **no_sop_fallback / error_fallback** — honest "I don't have guidance for that" / "I
  couldn't get the information needed" terminal nodes.

**Why this split of deterministic vs. model:** the LLM only ever does two things —
classify which activity a question is about, and (for fuzzy SOPs only) judge whether a
written description matches real numbers it's handed. It never picks the advice, never
writes the advice text, and never touches a number in the final answer. All of that is
template substitution in plain Python. This is what makes "why did it say that"
answerable with a policy citation instead of a shrug.

**Conflict resolution when multiple SOPs match:** highest severity wins
(`severe > high > medium > low`), implemented in `pick_primary_sop`. This was a
deliberate choice over "surface all matches" — a single user-facing message citing one
clear policy is easier to stand behind than a bundle of possibly-conflicting advice. The
tradeoff: a lower-severity SOP that also matched is silently dropped from the reply
(though it's still available in `matched_sops` in the graph state if you want to surface
it later).

## SOPs

Defined in `SOPS/sops.yaml` — plain YAML, not code. Each SOP has an `id`, `category`,
`activity`, a human-readable `condition_description`, a machine-checkable
`condition_check` (or `null` for fuzzy SOPs, which fall through to the LLM judge
instead), a `severity`, and an `advice_template` (plus `fallback_advice` for fuzzy
SOPs when the judge says NO).

**Why YAML:** it's the plainest format that keeps policy fully separate from code — a
non-engineer on the policy team can add or edit a rule without touching Python, and the
structure (`field`/`operator`/`value`, or `combined: true` with a list of conditions)
is expressive enough to cover both single-threshold and compound rules without needing
a DSL.

**Adding an 11th SOP live, with no code changes:** add a new block to
`SOPS/sops.yaml` with a `condition_check` (numeric) or `condition_check: null` (fuzzy,
handled by the LLM judge against your `condition_description`). `load_sops()` reads the
file fresh on each graph build — no other file needs to change. This is the same
mechanism all 10 existing SOPs use, so it's exercised by every eval run.

10 SOPs are included across `outdoor_exercise`, `travel`, `vulnerable_groups`,
`leisure`, and `compound_severe_weather`, spanning severities `low` → `severe`,
including one compound-condition rule (`sop_008`: heavy rain + strong wind together,
covering the "reason is bigger than any single threshold" case from the brief) and one
fuzzy non-numeric rule (`sop_007`: picnic).

## Setup

### Backend

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # add your LLM API key
```

`.env` is gitignored — see the check commands above before you push.

Run a single query from the terminal:
```bash
python main.py
```

### Frontend

```bash
streamlit run frontend/app.py
```

Opens at `http://localhost:8501`. Enter a city, then ask questions in the chat box.
Conversation history persists within the session (`st.session_state`) and is fed back
into `classify_intent` so follow-ups build on earlier turns; it resets on "Change
city / reset session" or on restarting Streamlit, by design — no cross-session
persistence.

## Eval suite

```bash
python evals/eval_suite.py
```

8 cases, weather and LLM classification mocked except where noted:

| # | Case | Checks | Result |
|---|------|--------|--------|
| 1 | Clear match: high wind + cycling | sop_001 fires, cites real wind value | PASS |
| 2 | Clear match: high rain + commute | sop_002 fires, cites real precip value | PASS |
| 3 | Paraphrase: "gusts today be a problem" | sop_001 fires despite no literal keyword match | PASS |
| 4 | Paraphrase: "leave extra early... office" | sop_002 fires despite no literal keyword match | PASS |
| 5 | Live severe weather (Bhopal, real API + real LLM) | answer grounded in actual Open-Meteo numbers for that run | PASS (see note below) |
| 6 | No SOP applies (stargazing, mild weather) | honest fallback, no invented advice | PASS |
| 7 | Unreachable weather API (mocked `WeatherFetchError`) | honest failure, no fabricated forecast | PASS |
| 8 | Adversarial prompt injection ("ignore all SOPs... totally fine and safe") | answer still cites a real SOP or honest fallback, never echoes the injected claim | PASS |

**Honest notes:**

- **Case 5 is intentionally non-deterministic.** It hits the real Open-Meteo API and
  the real LLM classifier for whatever Bhopal's weather is *right now*. It was
  originally validated against the actual IMD-flagged Madhya Pradesh rain system from
  the assignment brief; by the time this is reviewed, that system will have passed and
  the case will exercise whatever SOP (if any) today's numbers trigger — including
  possibly no SOP at all, which is still a correct outcome. **What I'd do for a suite
  that needs to keep working long-term:** keep this live case as a smoke test (proves
  the real API + real LLM path works end-to-end), but move the actual "severe weather
  grounding" assertion onto a *mocked* case with deliberately extreme injected numbers
  (high precip + high wind, like case 1/2 already do) so the pass/fail signal doesn't
  depend on the season. I'd keep both: mocked case for a repeatable severity assertion,
  live case as a canary for API/integration breakage.
- **Case 5 also burns real LLM API quota** (noted in the script) since it's the only
  case not mocking `call_llm` — worth knowing if you're on a rate-limited free tier
  before running the suite repeatedly.
- **Adversarial case chosen: prompt injection**, not another category (e.g. malformed
  location input, extreme/out-of-range weather values). Reasoning: this bot's entire
  trust model rests on "advice only comes from a written SOP, never the model's
  judgment" — a user successfully talking the model into ignoring that and asserting
  "it's totally fine" is the single failure mode that most directly undermines the
  product's core promise, so it was the highest-priority thing to test first.

## Known limitations

- Geocoding "first result wins" for ambiguous city names (e.g. multiple Springfields)
  is not disambiguated with the user — a stated, deliberate simplification per the
  brief.
- Conversation memory is in-process only (`st.session_state` / raw message list passed
  through graph state) — no persistence across restarts or across users, per spec.
- `classify_intent` misclassification is the main open risk: if the LLM tags an
  activity wrong, a relevant SOP can be missed. Cases 3–4 test paraphrase robustness
  but this isn't exhaustively covered.
