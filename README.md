<<<<<<< HEAD
# Backup Buddy AI

## What it does and who it's for

Backup Buddy AI is a calculator for households in Pakistan (or anywhere
with regular power outages) who own, or are about to buy, a UPS, battery
bank, inverter, or solar backup system. Most people size these systems by
guesswork or by trusting whatever a shopkeeper recommends. This app takes
a plain description of the appliances someone wants to run, or a manual
list, and turns it into:

- how many watts those appliances draw continuously and at startup surge
- how many hours the battery bank can actually support that load
- whether the inverter is big enough, and how much safety margin is left
- which appliances to switch off first if the runtime target isn't met
- a plain-language usage plan explaining all of the above

The electrical math (load, runtime, safety margin, load-shedding order) is
plain deterministic Python, not the AI. The AI is only used to read free
text and to explain the already-computed numbers. This matters because it
means the numbers you see are always reproducible and never something the
model invented.

## Live URL

**[ADD YOUR DEPLOYED STREAMLIT CLOUD URL HERE]**

Test it in an incognito window before submitting, exactly like the repo,
to confirm it loads with no login prompt.

## Features

- **Two ways to add appliances**: describe them in a sentence ("3 fans, a
  fridge, and WiFi for 4 hours, on a 12V 200Ah battery") or add rows
  manually.
- **AI appliance + hardware extraction**: the free-text description is
  parsed into a structured appliance list (name, quantity, running watts,
  surge watts, priority) and, if mentioned, battery/inverter specs too.
  Wattages are matched against a 29-item reference table where possible;
  anything outside the table is estimated and flagged as `estimated: true`
  so it's never presented as a measured fact.
- **Editable appliance table**: every AI-generated or manually-entered row
  can be corrected before anything is calculated.
- **Backup runtime calculator**: usable battery energy and estimated
  runtime, computed from voltage, capacity (Ah), battery count, safe
  discharge depth (%), and inverter efficiency (%) — all of these are
  live inputs, not fixed constants.
- **Inverter safety check**: continuous load vs. inverter rating, and a
  worst-case surge estimate (all appliances running plus the single
  largest motor-start jump) vs. the inverter's peak rating. Status is
  Optimal below 85% of rating, Marginal between 85-100%, Overloaded above
  100% of either rating.
- **Priority-based load shedding**: if the runtime target isn't met, the
  app removes Optional appliances first, then Preferred (largest load
  first within each group), and shows exactly which ones and the
  resulting new runtime. Essential appliances are never removed
  automatically.
- **AI usage plan**: a plain-language explanation of the results plus a
  practical schedule, generated from the calculated numbers.
- **Charts**: load contribution per appliance, plus live status readouts
  for continuous/surge draw as a percentage of inverter rating.

## The AI feature

Two separate AI calls, each with its own system prompt, each Gemini API.

**1. Appliance + hardware extractor** — turns a sentence into structured
data, grounded against a reference wattage table so it isn't guessing
numbers from nothing:

```
You extract appliances and hardware specs from plain text.
Rules:
1. Match appliances to reference wattages where possible. Set estimated: false.
2. If unknown, estimate wattage. Set estimated: true.
3. Priority defaults to "Preferred". Use Essential/Optional based on user urgency.
4. Extract battery and inverter specs if provided. Otherwise return null.
5. If solar panel array capacity (DC watts) is specified but the inverter AC rating is missing, estimate the inverter_rating by dividing the total solar capacity by 1.20 (assuming a standard 1.15 to 1.25 Inverter Loading Ratio / DC-to-AC ratio).
6. If an inverter continuous rating is known (either stated directly, or derived from solar capacity per rule 5) but no peak/surge rating is mentioned, estimate inverter_peak_rating as the continuous rating multiplied by 1.6 (typical inverter surge headroom).
Return exactly this JSON:
{
  "appliances": [{"name": "string", "quantity": int, "running_watts": int, "surge_watts": int, "priority": "Essential|Preferred|Optional", "estimated": bool}],
  "required_hours": number,
  "system_specs": {"battery_voltage": number|null, "battery_capacity_ah": number|null, "battery_count": number|null, "inverter_rating": number|null, "inverter_peak_rating": number|null}
}
```

**2. Backup planning advisor** — receives the already-calculated results
(never touches the math itself) and produces the plain-language plan:

```
You are an electrical backup planning assistant inside the Backup Buddy AI app.
You will receive calculated electrical results (continuous load, surge load, usable energy, estimated runtime, inverter status, and removed appliances).

Responsibilities:
1. Explain results in simple, plain language.
2. Flag any overload, low runtime, or surge capacity warnings.
3. Write a practical appliance usage schedule fitting calculated runtime.
4. Separate calculated facts from assumptions.
5. Never change, override, or invent calculated numeric values.
6. Explicitly state when appliance wattages were estimated.
7. Recommend consulting a qualified electrician for installation work.

Return answer in exactly these six sections using Markdown headers (##):
## System Assessment
## Calculated Limitations
## Recommended Usage Plan
## Appliances to Reduce
## Assumptions
## Safety Notice
```

## Tools, services, and models used

- **Streamlit** — app framework and UI
- **Pandas** — appliance table handling
- **Plotly** — load contribution chart
- **Google Gemini API** (`google-genai` SDK, model `gemini-2.0-flash` by
  default, configurable via the `GEMINI_MODEL` secret) — both AI calls
- **Streamlit Community Cloud** — hosting

## Known limitations / assumptions (stated up front, not hidden)

- Appliance wattages not in the reference table are AI estimates, not
  measured values — always shown as such in the extracted table.
- Surge load is modeled as: total continuous load of everything, plus the
  single largest individual appliance's (surge - running) jump. This
  approximates "one motor starts while everything else is already on,"
  which is the realistic worst case, not literally every motor starting
  simultaneously.
- The solar-to-inverter sizing conversion (dividing solar DC watts by
  1.20) is a standard rule-of-thumb inverter loading ratio, not a
  substitute for an actual system design.
- If a peak/surge inverter rating isn't given, either by AI extraction or
  in the manual form, the app assumes it as 1.6x the continuous rating
  (a typical surge headroom for common inverters). This is always
  editable — the manual form's Peak Rating field stops auto-filling the
  moment you type your own value into it.
- This tool is a planning aid. It does not replace a licensed electrician
  for wiring, installation, or safety-critical decisions — the app says
  this explicitly in its own output.

## Screenshots

**[ADD AT LEAST 3 SCREENSHOTS HERE before submitting: (1) the input panel
with an AI-extracted appliance list, (2) the results panel showing load,
runtime, and inverter status, (3) the AI usage plan output.]**

## How to run locally

```bash
git clone <your-repo-url>
cd backup-buddy-ai
pip install -r requirements.txt

# Add your own Gemini API key (get one free at https://aistudio.google.com/apikey)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# then edit .streamlit/secrets.toml and paste your real key

streamlit run app.py
```

## How to deploy (Streamlit Community Cloud)

1. Push this repo to a **public** GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in, click
   "New app", and point it at this repo and `app.py`.
3. In the app's **Settings -> Secrets**, paste:
   ```
   GEMINI_API_KEY = "your-real-key"
   GEMINI_MODEL = "gemini-2.0-flash"
   ```
4. Deploy. Test the live URL in an incognito window, then paste it into
   the Live URL section above.

Note: this app will not run on Vercel — Streamlit needs a persistent
server process, which Vercel's serverless model does not provide.
=======
# BackupBuddyAI
>>>>>>> e1f86727a521c50047246931e876ad0088625673
