# Mutual Fund Knowledge Assistant

A facts-only assistant for the HDFC Mutual Fund house page and four HDFC Direct Growth schemes. It quotes the loaded Groww pages. It does not give investment advice.

> Facts only. No investment advice. Answers are short quotations of public pages on HDFC Mutual Fund schemes (Direct Plan, Growth) and official help or regulator pages. They are not a recommendation to buy, sell, or hold any scheme. Past performance is not shown here on purpose. Check the linked page before you act.

The same disclaimer is always visible on the page.

Hosted demo: https://mutual-fund-assistant-beige.vercel.app

## Setup

Python 3.12 is what the hosted app uses (`.python-version`). A local 3.9 virtualenv can run the same code. The chunk and embedding files are already in the repo, so a fresh checkout can answer without scraping.

1. Create the virtualenv and install the app.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy the environment file and put `GROQ_API_KEY` in `.env`. That file is gitignored. `.env.example` has the same keys and an empty secret. Refusals never call the model. Fact answers that are not taken straight from a page do.

```bash
cp .env.example .env
```

| Variable | Role |
| --- | --- |
| `LLM_PROVIDER` | `groq` by default. OpenAI, Anthropic, Gemini, and Mistral use the same `complete(system, user)` call when their SDK is installed from `requirements-providers.txt`. |
| `LLM_MODEL` | `qwen/qwen3.8-27b` |
| `GROQ_API_KEY` | Required for answers that reach the model. |
| `LLM_TEMPERATURE` | `0.1` |
| `LLM_REASONING_EFFORT` | `none` on Groq |

3. Start the page.

```bash
uvicorn app.api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. `GET /api/health` stays 503 until every pipeline stage is `ok` and the embedding model name matches `config.yaml`.

4. To refresh the pages, install the ingest extras and rebuild the index. The new fetch date becomes the “Last updated from sources” date. Restart the local server after a refresh so it drops the cached index.

```bash
pip install -r requirements-ingest.txt
python -m app.cli pipeline
```

Chunk size, `top_k`, the embedding model name, and citation domains live in `config.yaml`. Changing the provider or model means editing `.env` only.

| Command | What it writes |
| --- | --- |
| `python -m app.cli scrape` | `data/raw/<id>/` |
| `python -m app.cli load` | `data/documents/documents.jsonl` |
| `python -m app.cli chunk` | `data/chunks/chunks.jsonl` |
| `python -m app.cli embed` | `data/embeddings/embeddings.jsonl` |
| `python -m app.cli index` | `data/chroma/` and the index stage in `data/pipeline.json` |
| `python -m app.cli pipeline` | Scrape through index, in order |
| `python -m app.cli ask "…"` | One answer and a trace under `data/traces/` |
| `python -m app.cli sample` | `eval/sample_qa.md` from real `POST /api/ask` calls |
| `uvicorn app.api:app --host 127.0.0.1 --port 8000` | The page at http://127.0.0.1:8000 |

Ingest embeddings use `sentence-transformers/all-MiniLM-L6-v2`. A question is embedded with the same model through fastembed. Question-time search reads `chunks.jsonl` and `embeddings.jsonl`.

## Scope

The corpus is the HDFC Mutual Fund house page, four Direct Growth scheme pages, and one Groww Help article. `sources/sources.csv` lists those six URLs. The scraper fetches nothing else. Figures are whatever those pages said on the fetch date. They are not constants in code. The current fetch date is 2026-11-11.

| id | Page |
| --- | --- |
| `hdfc-amc` | [HDFC Mutual Fund overview](https://groww.in/mutual-funds/amc/hdfc-mutual-funds). Fund-house facts and the Groww steps for investing in an HDFC scheme. |
| `hdfc-large-cap` | [HDFC Large Cap Fund Direct Growth](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth) |
| `hdfc-flexi-cap` | [HDFC Flexi Cap Direct Plan Growth](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth). The page slug still says equity fund. |
| `hdfc-elss` | [HDFC ELSS Tax Saver Fund Direct Plan Growth](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth) |
| `hdfc-mid-cap` | [HDFC Mid Cap Fund Direct Growth](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth) |
| `groww-help-capital-gains` | [Section 80C help article](https://groww.in/help/my-account/ma-others/where-can-i-get-the-tax-proof-for-section-80c), which states the Mutual Fund capital-gains download steps. |

Scheme answers can quote expense ratio, exit load, minimum SIP, minimum lump sum, lock-in, riskometer, benchmark, investment objective, category, fund managers, holdings, NAV, AUM, launch date, and a published return when that figure is in the cited chunk.

## Known limits

- A follow-up in the same chat, such as “and the exit load?”, keeps the scheme from the previous question. A new chat starts fresh. A question that names a different scheme uses that scheme.
- The schemes cannot be compared with each other. A question that asks which scheme is higher, lower, or better is outside this version.
- Advice, salary allocation, ranking, other fund houses, and account identifiers are refused before retrieval.
- A number in an answer has to appear in the cited chunk. If the draft fails that check, the page says the fact was not found.
- Answers match the last fetch, not a later edit on the Groww page. Run `python -m app.cli pipeline` to catch up.
- The first question in a fresh process loads MiniLM. Later questions are the ones to time. A warm ask is about a second once Groq is reachable over IPv4.
- On the hosted deploy, the function disk is read-only, so the trace file is not saved and `trace_path` is empty. Locally the trace is `data/traces/<id>.json`.
- Raw HTML, the Chroma folder, traces, and `.env` are not in git. The chunk and embedding files are, so the hosted app can answer without re-scraping.

## Sample Q&A

[`eval/sample_qa.md`](eval/sample_qa.md) has eight queries run through `POST /api/ask` on 2026-11-15. The answers were not written by hand. Each one includes the source link and the fetch date. Regenerate it with `python -m app.cli sample`.

| # | Question | Source |
| --- | --- | --- |
| 1 | About HDFC Mutual Fund | [HDFC Mutual Fund](https://groww.in/mutual-funds/amc/hdfc-mutual-funds) |
| 2 | How to Invest in HDFC MF on Groww | [HDFC Mutual Fund](https://groww.in/mutual-funds/amc/hdfc-mutual-funds) |
| 3 | Expense ratio of HDFC Large Cap Fund Direct Growth | [Large Cap](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth) |
| 4 | Lock-in on HDFC ELSS Tax Saver Fund Direct Plan Growth | [ELSS](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth) |
| 5 | Exit load of HDFC Mid Cap Fund Direct Growth | [Mid Cap](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth) |
| 6 | Minimum SIP for HDFC Flexi Cap Direct Plan Growth | [Flexi Cap](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth) |
| 7 | How do I download a capital-gains statement on Groww? | [Groww Help](https://groww.in/help/my-account/ma-others/where-can-i-get-the-tax-proof-for-section-80c) |
| 8 | Should I buy HDFC Flexi Cap? | Refused. No buy, sell, or hold. |
