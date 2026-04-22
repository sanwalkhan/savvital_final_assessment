"""
intake_triage.py
-----------------
Estate Planning Intake Triage - AI Recommendation Engine
Built for Savvital Technical Assessment | Task 1

Reads client profiles, sends them through Groq (free tier) for analysis,
and spits out structured JSON recommendations + an evidence log.

Setup:
    pip install groq
    set GROQ_API_KEY=your_key_here   (Windows)
    export GROQ_API_KEY=your_key     (Mac/Linux)
    python intake_triage.py
"""

import json
import os
import re
import sys

try:
    from groq import Groq
except ImportError:
    print("groq not installed, installing now...")
    os.system(f"{sys.executable} -m pip install groq -q")
    from groq import Groq


CLIENT_PROFILES = [
    {
        "name": "John Snow",
        "age": 38,
        "marital_status": "Married",
        "has_children": True,
        "owns_property": True,
        "has_business": False,
    },
    {
        "name": "Sanwal K",
        "age": 34,
        "marital_status": "Single",
        "has_children": False,
        "owns_property": False,
        "has_business": True,
    },
    {
        "name": "James D",
        "age": 32,
        "marital_status": "Divorced",
        "has_children": True,
        "owns_property": True,
        "has_business": True,
    },
]


INSTRUMENTS = [
    "Living Trust",
    "Last Will & Testament",
    "Healthcare Directive",
    "Durable Power of Attorney",
    "Financial Power of Attorney",
    "HIPAA Authorization",
    "Business Succession Plan",
    "Pour-Over Will",
    "Guardianship Designation",
]


def build_prompt(profile: dict) -> str:
    """Turn a client dict into a well-structured prompt the LLM can act on."""

    context_flags = []
    if profile["has_children"]:
        context_flags.append("has minor children")
    if profile["owns_property"]:
        context_flags.append("owns real estate")
    if profile["has_business"]:
        context_flags.append("owns a business")
    if not context_flags:
        context_flags.append("no dependents, no property, no business")

    instruments_list = "\n   ".join(INSTRUMENTS)


    complexity_hints = []
    if profile["age"] >= 60:
        complexity_hints.append("advanced age")
    if profile["has_business"]:
        complexity_hints.append("active business owner")
    if profile["has_children"] and profile["marital_status"] in ("Divorced", "Widowed", "Separated"):
        complexity_hints.append("single parent with minor children")
    if profile["has_children"] and profile["marital_status"] == "Married" and profile["owns_property"]:
        complexity_hints.append("young family with real estate")
    complexity_note = (
        f"Complexity signals detected: {', '.join(complexity_hints)}."
        if complexity_hints
        else "No high-complexity signals detected."
    )

    prompt = f"""You are a senior estate planning paralegal at a US law firm with over 15 years \
of experience advising clients across a wide range of life situations — from young singles \
to blended families and multi-generational business owners. Your role is to review a client \
profile and recommend the most appropriate planning instruments for their specific circumstances \
under US law.

Think carefully before you write anything. Consider the client's age, family structure, asset \
exposure, and any complexity flags together — not in isolation. A divorced parent with a business \
needs very different instruments than a married homeowner with no dependents. Recommend only \
what this person genuinely needs right now. Quality over quantity.

─────────────────────────────────────────
CLIENT PROFILE
─────────────────────────────────────────
Name           : {profile["name"]}
Age            : {profile["age"]}
Marital Status : {profile["marital_status"]}
Context        : {", ".join(context_flags)}
{complexity_note}
─────────────────────────────────────────

TASK — complete all three steps before producing output:

STEP 1 — SELECT INSTRUMENTS
   Choose between 2 and 5 instruments from the list below. No more, no fewer.
   List the single most critical instrument first.
   Use exact names as they appear — do not paraphrase or invent new ones.

   Available instruments:
   {instruments_list}

STEP 2 — WRITE RATIONALE
   Write 2–3 sentences in plain, professional English.
   Imagine you are briefly briefing a colleague just before a client meeting.
   Anchor your reasoning to this client's specific profile (age, family, assets).
   Do not use legal jargon. Be clear, direct, and human.

STEP 3 — SET URGENCY
   Apply the highest tier that fits (read all three before deciding):

   High   → client is age 60+, OR is an active business owner, OR has a highly complex
             family situation (e.g. blended family, estrangement, special-needs dependent,
             single parent after divorce/widowing, terminal illness)
   Medium → moderate complexity: young or mid-age family, owns property, has some assets,
             but no business and no acute family complexity
   Low    → young, single, minimal assets, no dependents, no property

─────────────────────────────────────────
OUTPUT FORMAT
─────────────────────────────────────────
Return ONLY a valid JSON object.
No markdown. No code fences. No explanation outside the JSON. No extra keys.

{{
  "client_name": "{profile["name"]}",
  "recommended_instruments": ["most critical first", "...", "..."],
  "rationale": "2-3 sentences, plain English, specific to this client.",
  "urgency_flag": "High|Medium|Low"
}}"""

    return prompt


def call_groq(prompt: str, client: Groq) -> str:
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=512,
    )
    return resp.choices[0].message.content.strip()


def parse_json_response(raw: str) -> dict:
    """Extract and parse JSON from LLM output, even if wrapped in markdown fences."""
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"Could not extract JSON from response:\n{raw}")


def validate_result(parsed: dict, profile: dict) -> list[str]:
    """
    Basic sanity checks on the parsed LLM output.
    Returns a list of warning strings (empty = all good).
    """
    warnings = []
    instruments = parsed.get("recommended_instruments", [])

    if not (2 <= len(instruments) <= 5):
        warnings.append(
            f"Instrument count out of range: got {len(instruments)}, expected 2–5."
        )

    invalid = [i for i in instruments if i not in INSTRUMENTS]
    if invalid:
        warnings.append(f"Unrecognised instrument(s): {invalid}")

    if parsed.get("urgency_flag") not in ("High", "Medium", "Low"):
        warnings.append(f"Invalid urgency_flag: {parsed.get('urgency_flag')}")

    
    if profile.get("has_business") and parsed.get("urgency_flag") == "Low":
        warnings.append("Urgency seems too low for an active business owner.")

    return warnings


def main():
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("ERROR: GROQ_API_KEY environment variable not set.")
        print("Get a free key at https://console.groq.com")
        sys.exit(1)

    groq_client = Groq(api_key=api_key)

    results = []
    evidence_log = []

    for profile in CLIENT_PROFILES:
        print(f"\nProcessing: {profile['name']} ...", flush=True)

        prompt = build_prompt(profile)
        raw_response = call_groq(prompt, groq_client)

        try:
            parsed = parse_json_response(raw_response)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  [ERROR] Failed to parse JSON for {profile['name']}: {e}")
            parsed = {}

      
        if parsed:
            warnings = validate_result(parsed, profile)
            if warnings:
                for w in warnings:
                    print(f"  [WARN] {w}")
            else:
                print("  [OK] Output passed all validation checks.")

        results.append(parsed)

       
        evidence_log.append({
            "client_name":    profile["name"],
            "input_profile":  profile,
            "prompt_sent":    prompt,
            "raw_llm_output": raw_response,
            "parsed_result":  parsed,
            "warnings":       validate_result(parsed, profile) if parsed else ["parse_failed"],
        })

        if parsed:
            print(f"  Urgency     : {parsed.get('urgency_flag', 'N/A')}")
            print(f"  Instruments : {', '.join(parsed.get('recommended_instruments', []))}")
            print(f"  Rationale   : {parsed.get('rationale', '')[:120]}...")

    
    with open("sample_output.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n-> sample_output.json saved")

   
    with open("evidence_log_raw.json", "w") as f:
        json.dump(evidence_log, f, indent=2)
    print("-> evidence_log_raw.json saved")

    print("\n=== FINAL RESULTS ===")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()