import pytest

from .fixtures import *  # noqa: F401, F403


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass
