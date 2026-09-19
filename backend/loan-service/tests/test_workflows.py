def test_loan_status_machine():
    transitions = {
        "REQUESTED": {
            "UNDER_REVIEW",
            "CANCELLED",
        },
        "UNDER_REVIEW": {
            "APPROVED",
            "CANCELLED",
        },
        "APPROVED": {
            "ACTIVE",
            "CANCELLED",
        },
        "ACTIVE": {
            "RETURN_DUE",
        },
        "RETURN_DUE": {
            "RETURNED",
        },
    }

    assert "UNDER_REVIEW" in transitions["REQUESTED"]
    assert "APPROVED" in transitions["UNDER_REVIEW"]
    assert "ACTIVE" in transitions["APPROVED"]
    assert "RETURNED" not in transitions["ACTIVE"]
