# Example 01 — Basic shot existence + availability check

Goal: confirm a shot exists and required FAIR-MAST Level-2 groups are available.

## Commands

```bash
mast-freegsnke doctor
mast-freegsnke check --shot 30201 --config ../../configs/config.example.json
```

## Expected outputs

- Printed report indicating shot existence and which Level-2 groups are present/missing.
