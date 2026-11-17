# CC Switch Skill source bridge

This independent compatibility repository exposes the upstream Graphify Codex Skill and the exact ClawHub `aysun168/skill-vetter-bak` publication in the folder format CC Switch updates. The packages are converted without installing them or executing upstream code.

| Skill | Official source | CC Switch path |
|---|---|---|
| Graphify | [GitHub Releases](https://github.com/Graphify-Labs/graphify/releases) | `skills/graphify/SKILL.md` |
| skill-vetter | [ClawHub release](https://clawhub.ai/aysun168/skills/skill-vetter-bak) | `skills/skill-vetter/SKILL.md` |

The refresh job checks every Monday at 10:00 Asia/Shanghai (02:00 UTC) and changes only the two exported folders. Each folder records the upstream version and artifact SHA-256. Graphify's Skill files and notices come from the verified release wheel. ClawHub's Skill file is checked against the version-specific canonical file. Unknown bundle contents stop the refresh.

Graphify's Python CLI is managed separately. The exported `UPSTREAM.json` records the Skill bundle version and does not claim the executable was upgraded. Each output retains the upstream license or license reference. This repository contains no local profiles, tokens, settings, or project files.
