# Estate Planning Intake Triage — AI Recommendation Engine
**Task 1**


## What This Does

This tool reads client profiles, sends them to an LLM (Groq / LLaMA 3.3 70B), and gets back structured estate planning recommendations which instruments to use, why, and how urgently. Results are saved as clean JSON plus a full evidence log for review.


## Setup & Run

```bash
pip install groq

# Set your API key (free at https://console.groq.com)
export GROQ_API_KEY=your_key_here        # Mac/Linux
set GROQ_API_KEY=your_key_here           # Windows

python intake_triage.py
```

**Output files generated:**
- `sample_output.json` — clean recommendations for each client
- `evidence_log_raw.json` — full audit trail: prompt sent, raw LLM response, parsed result, and any warnings


## Prompt Design

The prompt gives the LLM a clear role (senior estate planning paralegal), structured client data, a fixed instrument list to pick from, and explicit rules for urgency scoring.

Two things I was deliberate about:

**Reasoning before output.** The prompt tells the model to think through the client's full picture before producing JSON age, family structure, assets, and complexity signals together. Without this, the model tends to pattern-match on individual fields and miss combinations that matter. A divorced parent who owns a business and has minor children needs a very different set of instruments than the raw fields suggest individually. Asking it to reason first catches those interactions.

**Complexity pre-computation.** Rather than leaving complexity inference entirely to the LLM, the Python code detects signals upfront  things like "single parent after divorce" or "active business owner" and injects a plain-English summary into the prompt. This anchors the urgency decision and reduces inconsistency across runs.



## Human Review Design

LLMs are probabilistic. The same profile run twice can return slightly different results, and the model can occasionally hallucinate an instrument name or assign a mismatched urgency level. That's not acceptable in a domain where urgency flags directly affect how quickly a real client gets a call.

So the system is designed around the assumption that a human reviews before anything is acted on.

**What's built in for reviewers:**

- `validate_result()` checks every response automatically instrument count (must be 2–5), instrument names (must match the allowed list exactly), valid urgency flag, and obvious mismatches like a business owner flagged as Low urgency. Warnings print to console and are saved in the evidence log.

- `evidence_log_raw.json` keeps the full trace the exact prompt sent, the raw LLM response before any parsing, the parsed result, and any warnings. A reviewer can open this file and see exactly what the model was asked and what it said, not just the cleaned-up output.

**What a reviewer should check before trusting the output:**

- Any warnings in the log: especially unrecognised instrument names or urgency mismatches
- Rationale quality: is it actually specific to the client, or generic boilerplate?
- High-stakes profiles (business owners, single parents, complex family situations) — spot-check these manually since the cost of a wrong recommendation is highest there

The goal was to make the AI do the heavy lifting while keeping a human meaningfully in the loop — not just rubber-stamping output, but having the tools to actually audit it.


## Project Structure


intake_triage.py          ← main script
sample_output.json        ← generated on run
evidence_log_raw.json     ← full audit trail, generated on run
README.md                 ← this file


How to run:

==>bash
cd task1
pip install -r requirements.txt

 Windows
set GROQ_API_KEY=your_key_here
python intake_triage.py

 Mac / Linux
export GROQ_API_KEY=your_key_here
python intake_triage.py


Get a free Groq API key at https://console.groq.com (no credit card needed).