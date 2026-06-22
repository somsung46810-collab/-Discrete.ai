from discrete_ai import ToTriangulate, triangulate


def test_triangulation_buckets_match_conflict_and_one_sided_values():
    buckets = (
        ToTriangulate(
            {"shared": 1, "dupe_only": "a", "conflict": "left"},
            {"shared": 1, "dedupe_only": "b", "conflict": "right"},
        )
        .DiscreteChanges()
        .ReplBuckets()
        .to_dict()
    )

    assert [item["key"] for item in buckets["matched"]] == ["shared"]
    assert [item["key"] for item in buckets["dupe_only"]] == ["dupe_only"]
    assert [item["key"] for item in buckets["dedupe_only"]] == ["dedupe_only"]
    assert [item["key"] for item in buckets["conflicts"]] == ["conflict"]
    assert buckets["conflicts"][0]["resolved_value"] == "right"


def test_discrete_changes_override_resolution():
    buckets = (
        triangulate({"mode": "dupe"}, {"mode": "dedupe"})
        .DiscreteChanges({"mode": "triangulated"})
        .ReplBuckets()
    )

    assert buckets.to_dict()["changed"][0]["resolved_value"] == "triangulated"
    assert buckets.to_dict()["conflicts"] == []


def test_repl_replay_order_is_deterministic():
    replay = (
        triangulate(
            {"same": 1, "left": 2, "conflict": "a"},
            {"same": 1, "right": 3, "conflict": "b"},
        )
        .DiscreteChanges({"override": 4})
        .ReplBuckets()
        .replay()
    )

    assert [item["state"] for item in replay] == [
        "match",
        "changed",
        "dupe_only",
        "dedupe_only",
        "conflict",
    ]
