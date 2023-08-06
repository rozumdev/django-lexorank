import pytest

from .factories import BoardFactory, TaskFactory, TeamFactory, UserFactory


@pytest.fixture
def team_factory():
    return TeamFactory


@pytest.fixture
def team(team_factory):
    return team_factory()


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def user(user_factory):
    return user_factory()


@pytest.fixture
def board_factory():
    return BoardFactory


@pytest.fixture
def board(board_factory):
    return board_factory()


@pytest.fixture
def task_factory():
    return TaskFactory


@pytest.fixture
def task(task_factory):
    return task_factory()
