# 🔥 NJNG Gas Dashboard

Personal natural gas usage tracker — charts, filters, and billing history for New Jersey Natural Gas accounts.

Live site: **https://scammy37.github.io/njng-dashboard** (after GitHub Pages is enabled — see below)

---

## Files

| File | Purpose |
|------|---------|
| `index.html` | Main dashboard — charts, table, filters |
| `extract.html` | Add-bill page — instructions and setup guide |
| `data.json` | All billing records — the data source |
| `add_bill.py` | Script to manually add a bill entry and push |
| `sw.js` | Service worker — enables PWA install and offline access |
| `manifest.json` | PWA manifest — name, icon, display settings |
| `icon.svg` | App icon used by the PWA manifest |
| `scripts/process_bill.py` | Parses a bill PDF and appends the entry to `data.json` |
| `incoming/` | Drop a bill PDF here for Claude (or `process_bill.py`) to pick up |

---

## Adding a new bill

There's no automated login or scraping. Bill PDFs are added manually.
The **Add Bill** page (`extract.html`) has full instructions; click the link
in the dashboard header. Three options:

### Option A — Drop the PDF + ask Claude (easiest, any device)
1. Download the latest bill PDF from njng.com
2. Upload it to [github.com/scammy37/njng-dashboard → `incoming/`](https://github.com/scammy37/njng-dashboard/upload/main/incoming) (works from the GitHub mobile app or any browser)
3. Message Claude: "process the new bill" — it runs `scripts/process_bill.py`, commits the result, and deletes the processed PDF

### Option B — Claude + GitHub web editor (any device)
1. Go to [claude.ai](https://claude.ai), attach your NJNG PDF, use the prompt on the Add Bill page
2. Copy the JSON Claude returns
3. Open `data.json` on [github.com/scammy37/njng-dashboard](https://github.com/scammy37/njng-dashboard), click ✏️, paste the entry, commit

### Option C — Script (home PC, fastest)
Either run the parser directly on the PDF:
```
python scripts/process_bill.py path/to/bill.pdf
```
or get JSON from Claude (Option B) and run:
```
python add_bill.py
```
Paste the JSON when prompted, press Enter twice, then Y to commit and push.

> **New machine?** See the "First time on a new computer?" section on the Add Bill page for Git, Python, and clone setup instructions.

> **Parser note:** `scripts/process_bill.py` was written against NJNG's visual
> bill layout, not a live-extracted PDF text dump — the regex may need a
> tweak the first time it runs against a real PDF. If it fails to match, it
> prints the raw extracted text so the pattern can be adjusted.

---

## data.json entry format

```json
{"label":"May 26","period":"May 07–Jun 08, 2026","days":32,"ccf":35,"therms":37.04,"cost":76.38,"supplyCost":16.92,"deliveryCost":47.46,"customerCharge":12.00,"temp":0}
```

## Field reference

| Field | Type | Notes |
|-------|------|-------|
| `label` | string | Start month + 2-digit year: `"May 26"` |
| `period` | string | Full billing period: `"May 07–Jun 08, 2026"` |
| `days` | integer | Days in billing cycle |
| `ccf` | integer | Raw meter usage, "100's of Cubic Feet" |
| `therms` | number | Billing units — `ccf × BTU content` from the bill |
| `cost` | number | "This Service Period Gas Charges" only — excludes NJR Home Services warranty charges and tax |
| `supplyCost` | number | "BGS" line from the Bill Calculation box |
| `deliveryCost` | number | Sum of all "DEL" lines (can be two if the rate changed mid-cycle) |
| `customerCharge` | number | Flat customer charge line |
| `temp` | number or null | Avg temp °F for the period, if shown on the bill |

---

## Running locally

The dashboard uses `fetch('data.json')` which requires a local server (browsers block file:// fetches).

```bash
cd njng-dashboard
python serve.py
# Open http://localhost:8080
```

`serve.py` reads the `PORT` environment variable so it also works with the Claude Code preview pane automatically.

---

## PWA install

The dashboard is installable as a Progressive Web App. In Chrome/Edge, click the install icon in the address bar (or the three-dot menu → "Install NJNG Gas Dashboard"). Once installed it works offline using the last-fetched data.

---

## Enabling GitHub Pages

This repo doesn't have Pages turned on yet. One-time setup:
1. Go to **Settings → Pages** on this repo
2. Under "Build and deployment", set **Source** to `Deploy from a branch`
3. Set **Branch** to `main` / `/(root)`, click **Save**
4. The site will be live at `https://scammy37.github.io/njng-dashboard` within a few minutes
