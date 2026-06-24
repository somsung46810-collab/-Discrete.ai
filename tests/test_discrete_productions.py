import pytest

from discrete_ai import (
    StatusUpdate,
    ToTriangulate,
    hexadecimal_to_bits,
    triangulate,
)


def test_repl_buckets_report_percentage_to_pool_completion() -> None:
    buckets = (
        ToTriangulate(
            {"mode": "dupe", "shared": 1},
            {"mode": "dedupe", "shared": 1},
        )
        .DiscreteChanges({"mode": "triangulated"})
        .ReplBuckets()
    )

    status = buckets.status()
    percentages = [item["percentage"] for item in status]

    assert percentages[0] == 0
    assert percentages == sorted(percentages)
    assert percentages[-1] == 100
    assert status[-1]["stage"] == "pool"
    assert status[-1]["condition"] == "continue"
    assert buckets.to_dict()["matched"][0]["key"] == "shared"
    assert buckets.to_dict()["changed"][0]["resolved_value"] == "triangulated"


def test_status_callback_receives_structured_pool_updates() -> None:
    updates: list[StatusUpdate] = []

    buckets = (
        triangulate(
            {"alpha": 1},
            {"alpha": 2},
            status_callback=updates.append,
        )
        .DiscreteChanges()
        .ReplBuckets()
    )

    assert updates == buckets.status_updates
    assert updates[-1].percentage == 100
    assert updates[-1].stage == "pool"
    assert updates[-1].condition == "continue"
    assert buckets.to_dict()["conflicts"][0]["resolved_value"] == 2


def test_empty_pipeline_finishes_at_100_percent_without_endif() -> None:
    buckets = ToTriangulate({}, {}).DiscreteChanges().ReplBuckets()

    assert buckets.status()[-1] == {
        "percentage": 100,
        "stage": "pool",
        "message": "REPL buckets ready for pooling",
        "condition": "continue",
    }


@pytest.mark.parametrize(
    ("hexadecimal", "bits"),
    [
        ("ff", "11111111"),
        ("0f", "00001111"),
        ("f0", "11110000"),
        ("0x0f", "00001111"),
    ],
)
def test_hexadecimal_to_bits_preserves_width(hexadecimal: str, bits: str) -> None:
    assert hexadecimal_to_bits(hexadecimal) == bits


def test_pool_records_hexadecimal_to_bits_metadata() -> None:
    buckets = (
        ToTriangulate({"shared": 1}, {"shared": 1})
        .DiscreteChanges()
        .ReplBuckets()
        .Pool("ff")
        .Pool("0f")
        .Pool("f0")
    )

    result = buckets.to_dict()

    assert result["bucket_stage"] == "pool"
    assert result["bucket_encoding"] == "hex->bits"
    assert [pool["bits"] for pool in result["pools"]] == [
        "11111111",
        "00001111",
        "11110000",
    ]
    assert all(pool["encoding"] == "hexadecimal->bits" for pool in result["pools"])


@pytest.mark.parametrize("value", ["", "0x", "gg", "12z"])
def test_hexadecimal_to_bits_rejects_invalid_input(value: str) -> None:
    with pytest.raises(ValueError):
        hexadecimal_to_bits(value)
