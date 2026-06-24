# Discrete Productions

**Discrete.ai is defined as Discrete Productions:** a deterministic local production pipeline for triangulating duplicate (`DUPE`) and canonical (`DEDUPE`) values through R.E.P.L. — Read, Evaluate, Pool, Loop — type buckets.

## Production flow

1. **Read** the DUPE source, DEDUPE source, and explicit production changes.
2. **Evaluate** every sorted key and classify it as `matched`, `changed`, `dupe_only`, `dedupe_only`, or `conflicts`.
3. **Pool** the classified entries into deterministic REPL buckets and convert hexadecimal values to bit strings when requested.
4. **Loop** by replaying the buckets in their fixed production order.

Explicit values supplied to `DiscreteChanges()` take precedence over DUPE and DEDUPE values. Unresolved conflicts use the DEDUPE value as the canonical result.

## Pool hexadecimal values into bits

```python
from discrete_ai import ToTriangulate

buckets = (
    ToTriangulate(
        {"mode": "dupe", "shared": 1},
        {"mode": "dedupe", "shared": 1},
    )
    .DiscreteChanges({"mode": "triangulated"})
    .ReplBuckets()
    .Pool("ff")
    .Pool("0f")
)

print(buckets.to_dict())
```

The pool records preserve hexadecimal width:

```json
{
  "bucket_stage": "pool",
  "bucket_encoding": "hex->bits",
  "pools": [
    {
      "source": "ff",
      "encoding": "hexadecimal->bits",
      "bits": "11111111"
    },
    {
      "source": "0f",
      "encoding": "hexadecimal->bits",
      "bits": "00001111"
    }
  ]
}
```

`Pool()` accepts hexadecimal strings with or without a `0x` prefix. Invalid or empty hexadecimal input raises `ValueError`.

## Percentage status updates

```python
from discrete_ai import StatusUpdate, ToTriangulate


def show_status(update: StatusUpdate) -> None:
    print(
        f"[{update.percentage:3d}%] "
        f"{update.stage}: {update.message} ({update.condition})"
    )


buckets = (
    ToTriangulate(
        {"mode": "dupe", "shared": 1},
        {"mode": "dedupe", "shared": 1},
        status_callback=show_status,
    )
    .DiscreteChanges({"mode": "triangulated"})
    .ReplBuckets()
)

print(buckets.to_dict())
print(buckets.replay())
print(buckets.status())
```

Status events are structured as:

```json
{
  "percentage": 100,
  "stage": "pool",
  "message": "Pooled 2 of 2 entries into REPL buckets",
  "condition": "continue"
}
```

Percentages are monotonic and clamped from `0` to `100`. Completion does not force an `endif` condition.
