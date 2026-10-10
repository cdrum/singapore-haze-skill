---
name: singapore-haze
description: >-
  Report current Singapore haze from NEA: 24-hour PSI and 1-hour PM2.5 for
  North, South, East, West, and Central, with official descriptors. Use when
  the user asks about Singapore haze, PSI, PM2.5, or air quality for the
  island or a neighbourhood, or wants a recurring haze check.
---

# Singapore haze

Report the latest official NEA readings for **24-hour PSI** and **1-hour PM2.5** for Singapore's five regions (North, South, East, West, Central), each with its official descriptor. The source of truth is NEA's haze site, https://www.haze.gov.sg/. The readings come from NEA's real-time APIs on data.gov.sg. Fetch them with the bundled script. Do not paste in a replacement script.

## 1. Decide the region(s)

- If the user named a region (North, South, East, West, or Central), report only that one.
- If they named a neighbourhood, map it to the nearest region, pass that region to the script, and say which region you used. Clear examples: Toa Payoh, Bishan, Novena, and Orchard are Central; Woodlands, Yishun, and Sembawang are North; Tampines, Pasir Ris, Bedok, and Changi are East; Jurong, Clementi, and Tuas are West; Sentosa, Harbourfront, and Bukit Merah are South. This is a convenience guide, not an official NEA boundary. If you are unsure, report all five.
- If no place was given, report all five.
- The script accepts region names only. It rejects neighbourhood names.

## 2. Fetch the readings

Run the bundled script with Python 3 from the directory that contains this `SKILL.md` and `scripts/haze.py` (the repository root, or the skill folder after installation):

```bash
python3 scripts/haze.py
python3 scripts/haze.py central
python3 scripts/haze.py north east --json
```

Region names are case-insensitive. With no region, the script prints all five. The default output is a table with the reading time in SGT. `--json` prints values, descriptors, and timestamps. No API key is required. The script sends a User-Agent header because data.gov.sg returns 403 without one.

Use the script's numbers, descriptors, and timestamps. If the script fails (non-zero exit, network error, or no usable output), read https://www.haze.gov.sg/ and report the figures shown there, using the descriptor tables below. Never guess or reuse stale numbers. If neither source answers, say the data is unavailable right now.

## 3. Official descriptor ranges (from haze.gov.sg)

**24-hour PSI:** 0–50 Good; 51–100 Moderate; 101–200 Unhealthy; 201–300 Very unhealthy; above 300 Hazardous.

**1-hour PM2.5 (µg/m³):** 0–55 Band 1 Normal; 56–150 Band 2 Elevated; 151–250 Band 3 High; 251 and above Band 4 Very High.

## 4. Report

- Start with the reading time in SGT. The API timestamps are already +08:00. If the PSI and PM2.5 times differ, give both.
- For each region, give both numbers and their descriptors. Example: "Central: 24-hr PSI 174 (Unhealthy), 1-hr PM2.5 119 µg/m³ (Band 2 (Elevated))". For all five, a short table is fine; the script's table can be shown as-is.
- You may add one plain sentence naming the worst region. Mention a trend only when you fetched an earlier reading in this same task.
- Keep it short. Do not add health advice unless the user asks. You may point them to https://www.haze.gov.sg/ for NEA's official advisories.

## Scheduled checks

When the user wants this repeated, create a recurring task at the frequency they ask for, using the scheduler their tool provides. The task should run this skill for their region (or all five) and deliver the report to the people they name. Offer to stop the schedule once the haze eases.
