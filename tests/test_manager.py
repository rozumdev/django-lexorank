from unittest import mock

import pytest

from django_lexorank.lexorank import LexoRank

from .models import Board, Task, User


def test_creating_a_ranked_model_gives_it_a_rank():
    # when
    board = Board.objects.create(name="Board")

    # then
    assert board.rank


@pytest.mark.parametrize("default_rank_length", [5, 10])
def test_creating_a_ranked_model_gives_it_a_rank_of_default_length(default_rank_length):
    # when
    with mock.patch.object(LexoRank, "default_rank_length", default_rank_length):
        board = Board.objects.create(name="Board")

    # then
    assert len(board.rank) == default_rank_length


def test_creating_a_ranked_model_places_it_to_the_top_of_the_list_if_insert_to_bottom_is_set_to_false(  # noqa: E501
    board_factory,
):
    # given
    batch_size = 10
    board_factory.create_batch(batch_size)

    # when
    board = Board.objects.create(name="Board")

    # then
    assert Board.objects.count() == batch_size + 1
    assert Board.objects.order_by("rank").first() == board


def test_creating_a_ranked_model_places_it_to_the_bottom_of_the_list_if_insert_to_bottom_is_set_to_true(  # noqa: E501
    user_factory, team
):
    # given
    batch_size = 10
    user_factory.create_batch(batch_size)

    # when
    user = User.objects.create(name="Board", team=team)

    # then
    assert User.objects.count() == batch_size + 1
    assert User.objects.order_by("rank").last() == user


def test_creating_a_ranked_model_using_add_to_top_method_add_it_to_the_top_of_the_list(
    board_factory,
):
    # given
    batch_size = 10
    board_factory.create_batch(batch_size)

    # when
    board = Board.objects.add_to_top(name="Board")

    # then
    assert Board.objects.count() == batch_size + 1
    assert Board.objects.order_by("rank").first() == board


def test_creating_a_ranked_model_using_add_to_bottom_method_add_it_to_the_bottom_of_the_list(  # noqa: E501
    board_factory,
):
    # given
    batch_size = 10
    board_factory.create_batch(batch_size)

    # when
    board = Board.objects.add_to_bottom(name="Board")

    # then
    assert Board.objects.count() == batch_size + 1
    assert Board.objects.order_by("rank").last() == board


def test_creating_a_ranked_model_with_another_respect_field_place_it_to_a_separate_list(
    task_factory, board, user, board_factory
):
    # given
    tasks_on_board = task_factory.create_batch(10, board=board)
    another_board = board_factory.create()

    # when
    task = Task.objects.create(name="Task", assigned_to=user, board=another_board)

    # then
    assert tasks_on_board[0].rank == task.rank
