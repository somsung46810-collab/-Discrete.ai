from discrete_ai import StatusUpdate, ToTriangulate, triangulate


def test_repl_buckets_report_percentage_to_endif() -> None:
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
    assert status[-1]["condition"] == "endif"
    assert buckets.to_dict()["matched"][0]["key"] == "shared"
    assert buckets.to_dict()["changed"][0]["resolved_value"] == "triangulated"


def test_status_callback_receives_structured_updates() -> None:
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
    assert updates[-1].condition == "endif"
    assert buckets.to_dict()["conflicts"][0]["resolved_value"] == 2


def test_empty_pipeline_finishes_at_100_percent() -> None:
    buckets = ToTriangulate({}, {}).DiscreteChanges().ReplBuckets()

    assert buckets.status()[-1] == {
        "percentage": 100,
        "stage": "print",
        "message": "REPL buckets complete",
        "condition": "endif",
    }
