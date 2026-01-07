Custom X12 to JSON mapping

Purpose

This repo gives you a simple, client-specific mapping layer on top of X12. It lets you keep a base mapping per transaction set (ex: 322, 850) and override it per client when senders deviate from the standard. The Python helper loads the mapping, applies rules, and produces clean JSON for your Logic App or Azure Function.

Approach

- Parse X12 into an array of segments (segment id + element array).
- Apply a JSON mapping file that describes which segment/element maps to which JSON property.
- Support overrides per client, value mapping, transforms, and repeated segments.

Repository layout

- `mapping/schema.json`: schema for mapping files.
- `mapping/standards/850.json`: base 850 example.
- `mapping/clients/acme/850.json`: client overrides for 850.
- `mapping/standards/322.json`: base 322 mapping built from `real-sample` files.
- `mapping/clients/real-sample/322.json`: overrides for 322 (R4 qualifier handling, equipment type mapping).
- `mapping/clients/real-sample/322_demo.json`: repeat-segment demo mapping.
- `schema/322.json`: output JSON shape for 322.
- `src/mapper.py`: mapping engine.
- `src/demo.py`: demo runner with a basic parser.
- `samples/`: sample X12 files.

Setup

1) Ensure Python 3 is available.
2) (Optional) Create a virtual environment.
3) Run the demo to validate.

```bash
python src/demo.py samples/850_acme.edi
python src/demo.py samples/850_acme_qualifier_I.edi
python src/demo.py samples/322_repeat_demo.edi --mapping mapping/clients/real-sample/322_demo.json
```

How the mapping works

A mapping file defines:

- `fields`: single-value mappings by segment and element
- `segmentRules`: conditional maps based on qualifier or values
- `extends`: inherit from a base mapping
- `overrides`: add or replace specific fields or rules

Example field mapping

```json
{
  "purchaseOrder.number": { "segment": "BEG", "element": 3 },
  "event.actual.date": {
    "segment": "DTM",
    "element": 2,
    "when": { "element": 1, "equals": "152" },
    "transform": "date_yyyymmdd"
  }
}
```

Example rule mapping

```json
{
  "segment": "R4",
  "whenAny": [
    { "element": 1, "equals": "5" },
    { "element": 1, "equals": "I" }
  ],
  "map": {
    "event.location.id": { "element": 3 },
    "event.location.city": { "element": 4 }
  }
}
```

Supported features

- `element` is 1-based (N7-11 means `element: 11`).
- `component` for composite elements (pass arrays in the parsed segment).
- `when` / `whenAny` to filter by qualifiers.
- `valueMap` to translate sender codes.
- `transform` for simple conversions (see `src/mapper.py`).
- `occurrence`: `first`, `last`, `all`, or an integer index for repeated segments.

Repeated segments

If a segment repeats (multiple N7, N9, etc.), control which one is used with `occurrence`.

```json
{
  "equipment.second.initial": {
    "segment": "N7",
    "element": 1,
    "occurrence": 2
  },
  "references.BN.all": {
    "segment": "N9",
    "element": 2,
    "when": { "element": 1, "equals": "BN" },
    "occurrence": "all"
  }
}
```

How to onboard a new client

1) Pick or create the base mapping for the transaction set:
   - Create `mapping/standards/<ts>.json` if it does not exist.
2) Create a client mapping file:
   - `mapping/clients/<client>/<ts>.json`
   - Set `extends` to the base mapping.
3) Add client-specific changes under `overrides`:
   - Update element positions
   - Add qualifier handling in `segmentRules`
   - Add value translation with `valueMap`
4) Run `src/demo.py` with a sample file to verify.

Example client mapping

```json
{
  "$schema": "../../schema.json",
  "client": "acme",
  "transactionSet": "850",
  "extends": "../../standards/850.json",
  "overrides": {
    "fields": {
      "buyer.id": {
        "segment": "N1",
        "element": 2,
        "when": { "element": 1, "equals": "BY" }
      }
    },
    "segmentRules": [
      {
        "segment": "N7",
        "when": { "element": 11, "in": ["CC", "CH", "CN"] },
        "map": {
          "equipment.type": {
            "element": 11,
            "valueMap": {
              "CC": "container_chassis",
              "CH": "chassis_only",
              "CN": "container_only"
            }
          }
        }
      }
    ]
  }
}
```

Using the mapper in code

```python
from pathlib import Path

from src.mapper import load_mapping, map_segments

mapping = load_mapping(Path("mapping/clients/acme/850.json"))
output = map_segments(segments, mapping)
```

Logic App integration

- Use the Logic App X12 connector (or another parser) to get segments.
- Pass the segments plus client/transaction set to a helper (Azure Function, API app, or inline code).
- Select the client mapping file and call `map_segments`.

Testing with the demo code

The demo uses a simple parser that expects `*` as element separator and `~` as segment terminator. Use the samples in `samples/` to validate mappings quickly.

```bash
python src/demo.py samples/322_repeat_demo.edi --mapping mapping/clients/real-sample/322_demo.json
```
