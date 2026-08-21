## Summary

- Add support for custom Claude projects path to enable compatibility with Claude Code variants like [cc-mirror](https://github.com/numman-ali/cc-mirror) that store sessions in non-standard directories
- Configuration priority: `CCBOT_CLAUDE_PROJECTS_PATH` > `CLAUDE_CONFIG_DIR/projects` > `~/.claude/projects`
- Added unit tests for the new configuration options

## Usage

Users of Claude Code variants can now use ccbot by setting one of:

```bash
# Option 1: Direct path to projects directory
export CCBOT_CLAUDE_PROJECTS_PATH="/path/to/custom/projects"

# Option 2: Claude config directory (adds /projects automatically)
export CLAUDE_CONFIG_DIR="/path/to/custom/config"
```

For example, with cc-mirror/zai:
```bash
export CLAUDE_CONFIG_DIR="/home/user/.cc-mirror/zai/config"
ccbot
```

## Test Plan

- [x] Added 4 new unit tests for `claude_projects_path` configuration
- [x] All 212 existing tests pass
- [x] Tested with `CCBOT_CLAUDE_PROJECTS_PATH` environment variable
- [x] Tested with `CLAUDE_CONFIG_DIR` environment variable
- [x] Verified priority order: `CCBOT_CLAUDE_PROJECTS_PATH` takes precedence

Fixes #29
