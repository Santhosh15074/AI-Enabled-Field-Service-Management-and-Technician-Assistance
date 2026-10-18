from app.report_extraction import extract_fields


def test_extracts_all_four_fields_from_a_typical_report():
    report = (
        "The compressor was tripping on overload. Found a seized bearing on the motor shaft "
        "causing excess current draw. Replaced the bearing and tested the unit under load. "
        "Took about 1 hour 15 minutes total."
    )

    result = extract_fields(report)

    assert result.issue == "Found a seized bearing on the motor shaft causing excess current draw."
    assert result.action_taken == "Replaced the bearing and tested the unit under load."
    assert result.parts_used == "bearing"
    assert result.time_spent_minutes == 75


def test_falls_back_to_the_first_sentence_when_no_diagnostic_language_is_present():
    result = extract_fields("The pump wouldn't start. Tightened the loose terminal and it powered up fine.")

    assert result.issue == "The pump wouldn't start."


def test_fields_are_none_when_nothing_matches():
    result = extract_fields("Visited site, equipment was fine, no action needed.")

    assert result.action_taken is None
    assert result.parts_used is None
    assert result.time_spent_minutes is None


def test_minutes_only_duration():
    result = extract_fields("Cleaned the filter. Took 20 minutes.")

    assert result.time_spent_minutes == 20


def test_hours_only_duration_converts_to_minutes():
    result = extract_fields("Repaired the wiring. Took 2 hours.")

    assert result.time_spent_minutes == 120


def test_empty_report_returns_all_none():
    result = extract_fields("   ")

    assert result == extract_fields("")
    assert result.issue is None
