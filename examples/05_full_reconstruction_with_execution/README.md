# Example 05 — Full reconstruction with FreeGSNKE execution

Goal: run inverse/forward scripts via the execution harness and capture logs.

## Commands

```bash
mast-freegsnke run \
  --shot 30201 \
  --config ../../configs/config.example.json \
  --machine ../../machine_configs/MAST \
  --execute-freegsnke --freegsnke-mode both
```

If FreeGSNKE is installed in a separate Python:

```bash
mast-freegsnke run \
  --shot 30201 \
  --config ../../configs/config.example.json \
  --machine ../../machine_configs/MAST \
  --execute-freegsnke --freegsnke-mode both \
  --freegsnke-python /path/to/freegsnke/python
```

## Expected outputs

- `runs/shot_30201/logs/*.txt`
- `runs/shot_30201/freegsnke_execution.json`
