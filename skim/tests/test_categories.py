from datetime import datetime, timedelta, timezone

import pytest
from dateutil.relativedelta import relativedelta

from skim import categories, entries


async def test_top_categories_empty(skim_db):
    assert await categories.top_categories_by_month() == {}


@pytest.fixture
def today() -> datetime:
    today = datetime.today()
    return today.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)


@pytest.fixture
def current_month(today: datetime) -> tuple[datetime, datetime]:
    start_of_month = today.replace(day=1)
    return start_of_month, start_of_month + relativedelta(months=1)


@pytest.fixture
def previous_month(today: datetime) -> tuple[datetime, datetime]:
    start_of_month = today.replace(day=1)
    return start_of_month + relativedelta(months=-1), start_of_month


@pytest.fixture
async def some_entries(
    skim_db,
    current_month: tuple[datetime, datetime],
    previous_month: tuple[datetime, datetime],
):
    uninteresting = dict(
        feed='https://example.com/feed',
        title='Test Entry',
        link='https://example.com/1',
        body='Hiiiii',
        creators=None,
    )
    await entries.add(
        **uninteresting,
        id="one",
        timestamp=current_month[0] + timedelta(minutes=1),
        categories=['Cool'],
    )
    await entries.add(
        **uninteresting,
        id="two",
        timestamp=current_month[0] + timedelta(minutes=2),
        categories=['Cool'],
    )
    await entries.add(
        **uninteresting,
        id="three",
        timestamp=current_month[0] + timedelta(minutes=3),
        categories=['Beans'],
    )
    await entries.add(
        **uninteresting,
        id="four",
        timestamp=previous_month[0] + timedelta(minutes=4),
        categories=['Old'],
    )
    await entries.add(
        **uninteresting,
        id="five",
        timestamp=previous_month[0] + timedelta(minutes=5),
        categories=['Old'],
    )
    await entries.add(
        **uninteresting,
        id="six",
        timestamp=previous_month[0] + timedelta(minutes=6),
        categories=['Beans'],
    )


async def test_top_categories(
    some_entries,
    current_month: tuple[datetime, datetime],
    previous_month: tuple[datetime, datetime],
):
    assert await categories.top_categories_by_month() == {
        current_month: ['Cool', 'Beans'],
        previous_month: ['Old', 'Beans'],
    }
