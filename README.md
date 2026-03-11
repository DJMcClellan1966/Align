# Align: Genre-specific sentence dictionary + scratchLLM + App Forge

Align orchestrates building a **genre-specific corpus** (e.g. hobbies, art) from Harvard Library Public Domain Corpus or another dataset, then:

1. Builds a **sentence dictionary** and **word-graph** (via the dictionary app).
2. **Trains** scratchLLM's GPT on that corpus.
3. Uses **scratchLLM** (intent/user) + **dictionary** (context) + **App Forge** to **create apps**. Generated apps stay **local** on your machine.

## Prerequisites

- Python 3.10+
- [Dictionary](https://github.com/DJMcClellan1966/dictionary) repo (for unified basis and App Forge bridge).
- [scratchLLM](https://github.com/DJMcClellan1966/scratchLLM) repo (for training and intent).
- App Forge (in the dictionary repo or configured path).

## Setup

1. Clone or place the **dictionary** and **scratchLLM** repos (e.g. `Desktop/dictionary`, `Desktop/scratchLLM`).

2. Edit **config/paths.json** and set:
   - `dictionary_path`: path to the dictionary repo root (e.g. `.../dictionary/dictionary`).
   - `scratchllm_path`: path to the scratchLLM repo root (e.g. `.../scratchLLM/scratchLLM`).
   - Optionally `align_data_dir`: where Align stores per-genre data (default: `align/data/`).

3. Install dependencies (dictionary and scratchLLM have their own; Align scripts call into them):

   ```bash
   pip install requests
   ```

## Usage

### CLI

From the `align` folder:

```bash
# Set genre and build corpus + basis + train LM (run in order)
python cli.py set-genre hobbies

# Build an app from a description (uses current genre's basis + App Forge)
python cli.py build-app "a recipe manager for my hobby"
```

Generated app files are written to a folder you choose; **the app stays on your machine** (no cloud).

### Adding a genre

1. Add an entry in **config/genres.json** with `dataset` (`harvard` | `custom`) and optional `harvard_slice` or `path`.
2. Run `python cli.py set-genre <genre_id>` to fetch the corpus and build the basis + train the LM.

### Dataset choice

- **Harvard** (default for hobbies, art, fiction): Harvard Library Public Domain Corpus; slice by fiction/non-fiction when available.
- **Custom**: Set `path` in the genre config to a JSONL of sentences (e.g. `{"text": "...", "source": "...", "reference": "..."}` per line).

## Project layout

- **config/genres.json** – Genre id → dataset/slice/path.
- **config/paths.json** – Paths to dictionary, scratchLLM, optional App Forge.
- **scripts/fetch_genre_corpus.py** – Fetch Harvard (or custom) → `data/<genre>/genre_sentences.jsonl`.
- **scripts/build_genre_basis.py** – Build sentence dictionary + word-graph (calls dictionary build).
- **scripts/train_genre_llm.py** – Build corpus for scratchLLM and run training.
- **scripts/build_app.py** – Load BasisEngine from genre basis, get context, call App Forge, save app locally.
- **data/<genre>/** – Per-genre outputs: genre_sentences.jsonl, unified_basis/, corpus/, checkpoints.
- **cli.py** – CLI: `set-genre`, `build-app`.

## Local only

All processing runs on your machine. The built app is written to a local folder you choose; **no data is sent to the cloud**. The app stays local for use.

## Adding a genre

1. Edit **config/genres.json** and add an entry, e.g.:
   ```json
   "cooking": {
     "dataset": "harvard",
     "harvard_slice": "fiction",
     "description": "Cooking and recipes"
   }
   ```
2. For a custom corpus (e.g. your own JSONL), set `"dataset": "custom"` and `"path": "C:/path/to/sentences.jsonl"`.
3. Run `python cli.py set-genre cooking` to fetch, build basis, and train the LM for that genre.
