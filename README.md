# Align: Retirement and Hobby Helper with Mirror (LLM-Twin)

Align is a **local-only** helper app for mid-life and elder transition into retirement—and for those already retired, to reconnect with hobbies or start new ones.

## What it does

- **Start page**: Asks pertinent questions (basic info, working vs retired, retirement date, desired hobby to learn or restart). Your answers become your **profile** and seed **Mirror**, your personal LLM-twin.
- **Mirror**: A user-specific corpus (and optionally a small trained model) that grows from your profile and continued use. Over time it can prompt for more (appointments, meds, hobby details) and use that for helper messages.
- **Stack**: Uses [dictionary](https://github.com/DJMcClellan1966/dictionary) (basis, word list, grammar, sentence index), a **Harvard sentence corpus** (genre sentences), [scratchLLM](https://github.com/DJMcClellan1966/scratchLLM) (intent, retrieval, respond), and [App Forge](https://github.com/DJMcClellan1966) (template-based app generation). Your queries (hobby, retirement, meds, tips) are answered from Mirror + dictionary (respond_bridge). **App Forge is where information is shared**: profile, Mirror summary, meds, and appointments are stored in **shared_info** and passed into every app build so generated apps are pre-filled with your data.
- **Concept-grounded flow**: For each query, Align retrieves a **concept bundle** and **genre style sentences** (concept → style retrieval), merges style into the retrieval pool, then runs a **dictionary critic** on the answer (score, accept/warn). **Register-aware retrieval** prefers definitional vs narrative sentences by intent. A **sentence–sentence graph** supports “similar sentence” and “expand idea.” **Twin-driven pre-focus** (focus set from Mirror + profile) steers concept/style retrieval. **Episodic traces** (query, response, concepts) are logged and can be synced to Mirror via **Settings → Sync traces to Mirror**. Optional **build-app** steps: refine description with Mirror (`ALIGN_REFINE_DESCRIPTION=1`), rewrite app copy with Mirror (`ALIGN_REWRITE_APP_COPY=1`).

**Local only**: All processing runs on your machine. The only time the app may use the network is when building the genre corpus (e.g. fetching Harvard sentences) or when you explicitly ask to look something up.

## Prerequisites

- Python 3.10+
- [Dictionary](https://github.com/DJMcClellan1966/dictionary) repo
- [scratchLLM](https://github.com/DJMcClellan1966/scratchLLM) repo
- App Forge (in the dictionary repo or set `app_forge_path` in config)

## Setup

1. Clone or place **dictionary** and **scratchLLM** (e.g. `Desktop/dictionary`, `Desktop/scratchLLM`).
2. Edit **config/paths.json**: set `dictionary_path`, `scratchllm_path`, and optionally `align_data_dir`, `app_forge_path`, `harvard_corpus_path`.
3. Install dependencies:
   ```bash
   pip install requests
   ```

## Run

From the align folder:

```bash
# Launch the Align GUI (onboarding + Mirror + query + app build)
python run_align.py
```

Or use the CLI (after Mirror is set up):

```bash
python cli.py set-genre retirement
python cli.py build-app "a hobby tracker for my retirement"
```

## Project layout

- **config/paths.json** – Paths to dictionary, scratchLLM, App Forge, data dir. Use **Settings → Paths** in the GUI if missing.
- **config/genres.json** – Genre ids and dataset/slice for corpus.
- **config/concept_bridge.json** – Thresholds for dictionary critic, style sentences, sentence graph (Jaccard, min shared concepts).
- **run_align.py** – Launches the Align GUI (onboarding, agent, query with Mirror + dictionary, Edit profile, Build app, meds/appointments, Train Mirror).
- **Align/gui.py** – Main GUI: proactive agent message, Ask (respond_bridge), Remember this / Record outcome, Edit profile, Build app, one-click **Build my helper app**, **Health** (meds, appointments), **Settings** (Paths, Train Mirror model, Sync traces to Mirror).
- **Align/respond_bridge.py** – Concept retrieval → style sentences → generate (retrieve) → dictionary critic; episodic log.
- **Align/concept_style_retrieval.py** – Concept bundle + genre sentences by concept; register filter; focus set.
- **Align/dictionary_critic.py** – Post-generation score and accept/warn/reject.
- **Align/sentence_graph.py** – Sentence–sentence graph (similar sentence, expand idea).
- **Align/focus_set.py** – Twin-driven pre-focus (terms and likely queries from Mirror + profile).
- **Align/episodic.py** – Episodic trace log and sync_traces_to_mirror.
- **Align/shared_info.py** – Shared info store (profile + Mirror + meds + appointments); refreshed for every app build so App Forge receives it.
- **Align/onboarding.py** – Step 1/2 onboarding, hobby dropdown, preview; supports edit-profile flow.
- **Align/meds_appointments.py** – Structured meds (name, dose, time) and appointments (what, when, where); saved to Mirror and shared_info.
- **cli.py** – CLI: set-genre, build-app (when using genre corpus + dictionary).
- **scripts/build_app.py** – Builds app with **shared_info** passed to dictionary/App Forge. Optional: refine description with Mirror (`ALIGN_REFINE_DESCRIPTION=1`), rewrite app copy (`ALIGN_REWRITE_APP_COPY=1`).
- **data/** – profile.json, mirror/ (truth_base, focus_set, meds, appointments), shared_info.json, episodic.jsonl, builds/.

## Grammar and structure

Align uses the dictionary's **word list**, **grammar rules** (POS, explain/compare/relate), and **diagram helpers** (`grammar.py`). For meds and appointments, Mirror stores user preferences and the genre corpus can include health-related sentences; extend dictionary grammar or templates only if you need richer date/numeric handling.

## License

See repository license.
