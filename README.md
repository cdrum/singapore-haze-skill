# Singapore haze skill

A small, tool-agnostic [agent skill](https://agentskills.io) that reports Singapore's latest official haze readings: **24-hour PSI** and **1-hour PM2.5** for North, South, East, West, and Central, with the descriptors published on [haze.gov.sg](https://www.haze.gov.sg/).

The agent follows `SKILL.md` and runs `scripts/haze.py`. The script is Python 3 standard library only. NEA publishes the data on data.gov.sg with no API key. Requests must send a User-Agent header; the script does that, because data.gov.sg returns HTTP 403 without one.

`SKILL.md` at the repository root and `skills/singapore-haze/SKILL.md` are the same skill. The `name` in the frontmatter is `singapore-haze`, so install it into a folder of that name. Claude Code, Codex, and Cursor use that `name` and `description` to load the skill. Grok Bot can save the same file as a private skill.

## Sample output

Captured from the live APIs at 09:00 SGT on 10 October 2026. The next run will differ.

```
24-hr PSI as of 2026-10-10 09:00 SGT (2026-10-10T09:00:00+08:00)
1-hr PM2.5 as of 2026-10-10 09:00 SGT (2026-10-10T09:00:00+08:00)

Region   24-hr PSI  PSI descriptor  1-hr PM2.5 (µg/m³)  PM2.5 descriptor
-------  ---------  --------------  ------------------  -----------------
North    124        Unhealthy       80                  Band 2 (Elevated)
South    135        Unhealthy       81                  Band 2 (Elevated)
East     156        Unhealthy       110                 Band 2 (Elevated)
West     160        Unhealthy       111                 Band 2 (Elevated)
Central  174        Unhealthy       119                 Band 2 (Elevated)

Contains information from the PSI and PM2.5 real-time datasets accessed on 2026-10-10 from data.gov.sg (National Environment Agency), made available under the Singapore Open Data Licence version 1.0 (https://developers.data.gov.sg/open-data-licence).
```

One region, or JSON:

```bash
python3 scripts/haze.py central
python3 scripts/haze.py north east --json
```

Region names are case-insensitive. An unknown name prints an error to stderr and exits non-zero. A network or API failure does the same, and the script does not print guessed or partial readings.

## Run it yourself

Requires Python 3. From the repository root:

```bash
python3 scripts/haze.py
python3 -m unittest discover -s tests -v
```

There is nothing to install and no dependency list.

## Install the skill

Copy `SKILL.md` and `scripts/haze.py` so the script stays at `scripts/haze.py` next to `SKILL.md`. The skill tells the agent to run it from that directory.

### Claude Code

Personal skill, available in every project:

```bash
mkdir -p ~/.claude/skills/singapore-haze/scripts
cp SKILL.md ~/.claude/skills/singapore-haze/SKILL.md
cp scripts/haze.py ~/.claude/skills/singapore-haze/scripts/haze.py
```

For one project, use `.claude/skills/singapore-haze/` the same way. Claude Code loads `~/.claude/skills/<name>/SKILL.md` and `.claude/skills/<name>/SKILL.md`. See [Extend Claude with skills](https://code.claude.com/docs/en/skills).

### Codex

User skill:

```bash
mkdir -p ~/.agents/skills/singapore-haze/scripts
cp SKILL.md ~/.agents/skills/singapore-haze/SKILL.md
cp scripts/haze.py ~/.agents/skills/singapore-haze/scripts/haze.py
```

A repository can ship the same folder at `.agents/skills/singapore-haze/`. Codex still reads the older `~/.codex/skills/` location. Restart Codex after adding a skill. See [Agent Skills](https://developers.openai.com/codex/skills).

### Cursor

Cursor loads project skills from `.agents/skills/` and `.cursor/skills/`, and user skills from `~/.agents/skills/` and `~/.cursor/skills/`. The folder name must match `name`:

```bash
mkdir -p ~/.cursor/skills/singapore-haze/scripts
cp SKILL.md ~/.cursor/skills/singapore-haze/SKILL.md
cp scripts/haze.py ~/.cursor/skills/singapore-haze/scripts/haze.py
```

Use `.cursor/skills/singapore-haze/` inside a repo for a project skill. See [Cursor agent skills](https://cursor.com/docs/context/skills).

### Grok Bot

Grok Bot stores a private skill as instructions, not as a folder on disk.

1. Clone this repository so `scripts/haze.py` is on a machine where the Bot can run Python.
2. Paste `SKILL.md` into a Grok Bot conversation and ask it to save the instructions as a private skill.
3. Invoke it with `/` in the desktop composer. If it is missing, open Marketplace → Your plugins → Manage plugins and skills and check Private skills.

The saved skill tells the Bot to run `python3 scripts/haze.py` from the clone. Grok Bot's own docs describe saving a private skill: https://docs.x.ai/grok-bot/skills-routines-and-automations. To repeat the report, ask the Bot to run the skill on a schedule and to stop once the haze eases.

`skills/singapore-haze/` is the same bundle (its `scripts/haze.py` matches the root script). You can copy that directory instead of the two root files.

## Data source and attribution

Readings are from the National Environment Agency, via the data.gov.sg real-time APIs:

- 24-hour PSI (`psi_twenty_four_hourly`): https://api-open.data.gov.sg/v2/real-time/api/psi
- 1-hour PM2.5 (`pm25_one_hourly`): https://api-open.data.gov.sg/v2/real-time/api/pm25

Contains information from the PSI and PM2.5 real-time datasets accessed from [data.gov.sg](https://data.gov.sg) (National Environment Agency), made available under the [Singapore Open Data Licence version 1.0](https://developers.data.gov.sg/open-data-licence).

The licence asks for a conspicuous notice that names the dataset, the date you accessed it, the source, and a link to the licence. The script prints that notice, including the access date, under the table and in the JSON `attribution` field. data.gov.sg does not suggest that NEA endorses this skill.

## Descriptor tables

These are the ranges published on [haze.gov.sg](https://www.haze.gov.sg/). The script uses the same cut-points.

**24-hour PSI**

| PSI | Descriptor |
| --- | --- |
| 0–50 | Good |
| 51–100 | Moderate |
| 101–200 | Unhealthy |
| 201–300 | Very unhealthy |
| Above 300 | Hazardous |

**1-hour PM2.5 (µg/m³)**

| PM2.5 | Band | Descriptor |
| --- | --- | --- |
| 0–55 | 1 | Normal |
| 56–150 | 2 | Elevated |
| 151–250 | 3 | High |
| 251 and above | 4 | Very High |

## Disclaimer

This skill repeats NEA's measurements and the published descriptor for each number. It is not official health advice, a forecast, or guidance on going outdoors, exercise, or masks. Check [haze.gov.sg](https://www.haze.gov.sg/) for NEA's current readings and advisories.

## Licence

The skill and the script are MIT. See `LICENSE`. Copyright 2026 Chris Drumgoole. The haze data remains under the Singapore Open Data Licence, not the MIT licence.
