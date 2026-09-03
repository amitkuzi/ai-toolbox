# Profile Management

The toolbox now includes commands to manage default profiles for routing decisions.

## Commands

### `list-profiles`
List all available profiles with the default marked.

```bash
python scripts/store.py list-profiles
```

Output:
```
_default
  amit (default)
```

### `get-default-profile`
Get the name of the current default profile.

```bash
python scripts/store.py get-default-profile
```

Output:
```
amit
```

### `set-default-profile <profile_name>`
Set the default profile for routing decisions. The profile must exist in the `profiles/` directory.

```bash
python scripts/store.py set-default-profile amit
```

Output:
```
Default profile set to: amit
```

## How Routing Uses Default Profile

When running the `toolbox-route` skill:

1. The skill reads the default profile using `python scripts/store.py get-default-profile`
2. Unless you explicitly specify a different profile in your task description, the default profile is used for all routing decisions
3. The default profile provides:
   - `weights` — how to rank tools (local_capable, agent_ready, cost, freshness, etc.)
   - `privacy_default` — data residency preferences
   - `license_policy` — which licenses are acceptable
   - `budget_usd_per_task` — spending limit per task
   - `task_type_affinity` — weights for different task types

## Configuration File

The default profile name is stored in `.toolbox-config.json` in the repo root:

```json
{
  "default_profile": "amit"
}
```

This file is automatically managed by the CLI commands above.

## Example Usage

```bash
# View available profiles
python scripts/store.py list-profiles

# Switch to _default profile
python scripts/store.py set-default-profile _default

# Confirm the change
python scripts/store.py get-default-profile
# Output: _default

# Switch back to amit
python scripts/store.py set-default-profile amit
```
