# CC Switch Graphify Skill source bridge

This compatibility repository exports the [official Graphify Codex Skill](https://github.com/Graphify-Labs/graphify/releases) as `skills/graphify/SKILL.md` for CC Switch.

The refresh runs every Monday at 10:00 Asia/Shanghai (02:00 UTC). It verifies the official release wheel's SHA-256 and updates only `skills/graphify`. It does not install the wheel or run upstream code. `UPSTREAM.json` records the release and artifact digest. The Skill includes the upstream notices and licenses.

CC Switch manages the Skill files. Upgrade the separate Python CLI through its original tool installer.
