# Mutual Fund Assistant

A facts-only chat assistant for the HDFC Mutual Fund house page and four HDFC Direct Growth schemes. Pick a scheme, ask in plain English, and get a short answer quoted from a public page, with the source link.

**Live demo:** https://mutual-fund-assistant-beige.vercel.app

| | |
| --- | --- |
| **What it is** | A Retrieval-Augmented Generation (RAG) assistant that answers scheme-specific factual questions (expense ratio, exit load, lock-in, minimum SIP and similar) from a fixed set of public pages. |
| **Who it is for** | Investors who want one detail without reading a whole scheme page. |
| **What it will not do** | Give advice, rank or compare schemes, cover other fund houses, or explain general terms such as NAV or SIP. |

> Facts only. No investment advice. Answers are short quotations of public pages on HDFC Mutual Fund schemes (Direct Plan, Growth) and official help or regulator pages. They are not a recommendation to buy, sell, or hold any scheme. Check the linked page before you act.

The same disclaimer is always visible on the page.

*Independent project. Not affiliated with Groww or HDFC Mutual Fund. Answers reflect public pages as of the last fetch date shown in the app.*

## How it works

1. **Retrieve.** The question is embedded and matched against pre-built chunks of the source pages.
2. **Guard.** Advice, ranking, salary allocation, other fund houses, and account identifiers are refused before retrieval, so refusals never call the model.
3. **Generate.** The LLM writes a short answer using only the retrieved chunk.
4. **Verify.** Every number in the answer must appear in the cited chunk. If it does not, the app says the fact was not found instead of guessing.

## Scope

The corpus is the HDFC Mutual Fund house page, four Direct Growth scheme pages, and one Groww Help article. `sources/sources.csv` lists those URLs. The scraper fetches nothing else. Figures are whatever those pages said on the fetch date. They are not constants in code. The current fetch date is 2026-11-16.

| id | Page |
| --- | --- |
| `hdfc-amc` | [HDFC Mutual Fund overview](https://groww.in/mutual-funds/amc/hdfc-mutual-funds). Fund-house facts and the Groww steps for investing in an HDFC scheme. |
| `hdfc-large-cap` | [HDFC Large Cap Fund Direct Growth](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth) |
| `hdfc-flexi-cap` | [HDFC Flexi Cap Direct Plan Growth](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth). The page slug still says equity fund. |
| `hdfc-elss` | [HDFC ELSS Tax Saver Fund Direct Plan Growth](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth) |
| `hdfc-mid-cap` | [HDFC Mid Cap Fund Direct Growth](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth) |

Scheme answers can quote expense ratio, exit load, minimum SIP, minimum lump sum, lock-in, riskometer, benchmark, investment objective, category, fund managers, holdings, NAV, AUM, and launch date when that figure is in the cited chunk. Past performance is not shown here on purpose.

## Known limits

- **No comparison across schemes.** The assistant answers from one scheme's pages at a time. A question that asks which scheme is higher, lower, or better is outside this version.
- **No general definitions.** It will not give the full form or meaning of terms such as SIP or NAV, because the source pages do not contain them. It says so instead of answering from the model's own memory.
- **Facts only.** Advice, salary allocation, ranking, other fund houses, and account identifiers are refused before retrieval.
- **Numbers are checked.** A number in an answer has to appear in the cited chunk. If the draft fails that check, the page says the fact was not found.
- **Data is a snapshot.** Answers match the last fetch, not a later edit on the Groww page. Refreshing is manual: run `python -m app.cli pipeline`.
- **Follow-ups keep the scheme.** A follow-up in the same chat, such as "and the exit load?", keeps the scheme from the previous question. A new chat starts fresh. A question that names a different scheme uses that scheme.
- **Cold start.** The first question in a fresh process loads MiniLM. Later questions are the ones to time. A warm ask is about a second once Groq is reachable over IPv4.
- **Hosted traces.** On the hosted deploy, the function disk is read-only, so the trace file is not saved and `trace_path` is empty. Locally the trace is `data/traces/<id>.json`.
- **Not in git.** Raw HTML, the Chroma folder, traces, and `.env` are not in git. The chunk and embedding files are, so the hosted app can answer without re-scraping.

## Roadmap

- Comparison across schemes, using multi-scheme retrieval or a structured comparison view.
- A curated glossary as a separate, approved source for terms like NAV and SIP.
- Scheduled refresh of the source pages instead of a manual run.

## Sample Q&A

[`eval/sample_qa.md`](eval/sample_qa.md) has the full set of queries run through `POST /api/ask`. The answers were not written by hand. Each one uses the 16 November 2026 fetch. Regenerate it with `python -m app.cli sample`. A selection:

| # | Question | Answer | Source | Last updated |
| --- | --- | --- | --- | --- |
| 1 | About HDFC Mutual Fund | HDFC Mutual Fund is currently the largest mutual fund and actively managed equity mutual fund in India. It is one of the most profitable asset management companies (AMC) in the country. The company serviced more than 75000 empanelled distribution partners through 210 branches spread across more than 200 cities in India. | [HDFC Mutual Fund](https://groww.in/mutual-funds/amc/hdfc-mutual-funds) | 2026-11-16 |
| 2 | How to Invest in HDFC MF on Groww | Step 1. Log-in to your Groww account or register if you don't have one. Step 2. Upload your identity proof documents. Step 3. Upload your proof of address documents. Step 4. Select the investment period of your preference. Step 5. Choose your risk appetite - low, mid, or high. Step 6. Choose your preferred HDFC Bank Mutual Fund. Step 7. Click on "Invest One Time" or "Start SIP". | [HDFC Mutual Fund](https://groww.in/mutual-funds/amc/hdfc-mutual-funds) | 2026-11-16 |
| 3 | What is the expense ratio of HDFC Large Cap Fund Direct Growth? | The expense ratio of HDFC Large Cap Fund Direct Growth is 1.0%. | [Large Cap](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth) | 2026-11-16 |
| 4 | What is the lock-in on HDFC ELSS Tax Saver Fund Direct Plan Growth? | The lock-in period is 3 years. | [ELSS](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth) | 2026-11-16 |
| 5 | What is the exit load of HDFC Mid Cap Fund Direct Growth? | The exit load is 1% if redeemed within 1 year. | [Mid Cap](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth) | 2026-11-16 |
| 6 | What is the minimum SIP for HDFC Flexi Cap Direct Plan Growth? | The minimum SIP is ₹100. | [Flexi Cap](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth) | 2026-11-16 |
| 7 | Should I buy HDFC Flexi Cap? | Refused. The assistant does not say whether to buy, sell, or hold. | [Flexi Cap](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth) | 2026-11-16 |

Repository: https://github.com/sahana1710/mutual-fund-assistant-rag

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

4. To refresh the pages, install the ingest extras and rebuild the index. The new fetch date becomes the "Last updated from sources" date. Restart the local server after a refresh so it drops the cached index.

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
