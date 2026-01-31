# HEARTBEAT.md Template

## Quiet Hours
If current hour is between 23:00-08:00 local:
- Only respond to urgent/direct mentions
- Otherwise: HEARTBEAT_OK

## Periodic Checks
Read memory/heartbeat-state.json. Run checks where (now - lastCheck) > interval.
Update timestamps after each check.

## Default
If no checks due and nothing urgent: HEARTBEAT_OK
