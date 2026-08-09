# UIL Prep App

A Python project for organizing and searching UIL preparation material, including PDF extraction and alignment/indexing utilities.

## Components

- `alignment.py` — alignment processing
- `alignments/` — alignment data
- `index/` — generated/searchable index data
- `requirements.txt` — runtime dependencies

## Setup

```bash
python -m pip install -r requirements.txt
python alignment.py
```

## Notes

The project uses PDF and web-processing libraries. Keep source materials appropriately licensed, and document any generated indexes or datasets that should be rebuilt rather than committed.
