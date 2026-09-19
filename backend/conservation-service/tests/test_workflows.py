def test_treatment_status_machine():
    transitions = {
        "PLANNED": {
            "IN_PROGRESS",
            "CANCELLED",
        },
        "IN_PROGRESS": {
            "COMPLETED",
            "CANCELLED",
        },
        "COMPLETED": set(),
        "CANCELLED": set(),
    }

    assert "IN_PROGRESS" in transitions["PLANNED"]
    assert "COMPLETED" not in transitions["PLANNED"]
    assert "COMPLETED" in transitions["IN_PROGRESS"]
