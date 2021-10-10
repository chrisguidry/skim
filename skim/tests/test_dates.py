from datetime import datetime, timezone

from skim import dates


def test_from_iso():
    assert dates.from_iso('2021-02-03T04:05:06Z') == datetime(
        2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc
    )
    assert dates.from_iso('2021-02-03T04:05:06.123456Z') == datetime(
        2021, 2, 3, 4, 5, 6, 123456, tzinfo=timezone.utc
    )
