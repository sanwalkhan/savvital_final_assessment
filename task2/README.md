## Task 2 — Operations KPI Dashboard

**What it does:**
Simulates a year of estate planning case data (320 cases), then builds a multi-panel Plotly dashboard and exports it as a standalone `dashboard.html` — no server needed, just open in a browser.

**Files:**
```
task2/
├── dashboard.py                  # generates data + builds dashboard
├── requirements.txt
├── dashboard.html                # the actual dashboard (open this)
├── dashboard_writeup.md         # dashboard metrics story and dataset summary
```

**Dashboard write-up:** See `task2/dashboard_writeup.md` for the customer support dataset story, metric rationale, and a noted dataset limitation.

**How to run:**

```bash
cd task2
pip install -r requirements.txt
python dashboard.py
# then open dashboard.html in your browser
```

**KPIs included and why:**

| Panel | Metric | Why it matters |
|---|---|---|
| Top cards | Total Cases, Conversion Rate, Avg Case Value | Firm-level pulse — at a glance |
| Stage bar | Cases per pipeline stage | Spots where the funnel is backed up |
| Source donut | Lead source breakdown | Marketing ROI — which channels to invest in |
| Conversion line | Monthly close rate % | Trend visibility — is the team improving? |
| Revenue bars | Monthly revenue ($k) | Ties directly to firm growth goals |
| Days per stage | Avg time in each stage | Operational bottleneck finder |

Drafting typically takes the longest (~12 days avg in the model) — exactly the kind of thing the AI drafting tools in this role would target.

---

## Notes

- No paid tools used anywhere — Groq free tier for LLM, Plotly/Pandas/NumPy for the dashboard
- The evidence log in Task 1 was deliberately included to support the human-in-the-loop validation requirement mentioned in the JD
- The dashboard dataset is synthetic but modeled on realistic estate planning funnel distributions