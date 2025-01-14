from unittest import mock

import pytest

from django_lexorank.lexorank import LexoRank

from .models import Board, Task, User


def test_placing_ranked_model_after_another_change_it_rank_respectively(board_factory):
    # given
    board_factory.create_batch(10)
    boards = Board.objects.order_by("rank")
    after_board = boards[3]
    before_board = boards[4]

    # when
    board = boards[0].place_after(after_obj=after_board)

    # then
    assert board.rank > after_board.rank
    assert board.rank < before_board.rank


def test_placing_ranked_model_before_another_change_it_rank_respectively(board_factory):
    # given
    board_factory.create_batch(10)
    boards = Board.objects.order_by("rank")
    after_board = boards[3]
    before_board = boards[4]

    # when
    board = boards[0].place_before(before_obj=before_board)

    # then
    assert board.rank > after_board.rank
    assert board.rank < before_board.rank


def test_placing_ranked_model_on_top_makes_it_rank_first(board_factory):
    # given
    boards = board_factory.create_batch(10)

    # when
    board = boards[5].place_on_top()

    # then
    assert Board.objects.order_by("rank").first() == board


def test_placing_ranked_model_on_bottom_makes_it_rank_last(board_factory):
    # given
    boards = board_factory.create_batch(10)

    # when
    board = boards[5].place_on_bottom()

    # then
    assert Board.objects.order_by("rank").last() == board


def test_placing_ranked_model_after_another_object_when_there_is_no_space_left_increments_the_rank_length(  # noqa: E501
    board_factory,
):
    # given
    previous_board = board_factory.create(rank="bbbbbb")
    next_board = board_factory.create(rank="bbbbbc")
    board = board_factory.create()

    # when
    board = board.place_after(after_obj=previous_board)

    # then
    assert board.rank > previous_board.rank
    assert board.rank < next_board.rank
    assert board.rank == previous_board.rank + "m"


def test_placing_ranked_model_before_another_object_when_there_is_no_space_left_increments_the_rank_length(  # noqa: E501
    board_factory,
):
    # given
    previous_board = board_factory.create(rank="bbbbbb")
    next_board = board_factory.create(rank="bbbbbc")
    board = board_factory.create()

    # when
    board = board.place_before(before_obj=next_board)

    # then
    assert board.rank > previous_board.rank
    assert board.rank < next_board.rank
    assert board.rank == previous_board.rank + "m"


def test_rebalancing_ranked_model_updates_the_ranks_according_to_the_order(
    board_factory,
):
    # given
    previous_board = board_factory.create(rank="bbbbbb")
    next_board = board_factory.create(rank="bbbbbc")
    last_board = board_factory.create(rank="cccccc")

    initial_previous_board_rank = previous_board.rank
    initial_next_board_rank = next_board.rank
    initial_last_board_rank = last_board.rank

    # when
    previous_board.rebalance()

    # then
    previous_board.refresh_from_db()
    next_board.refresh_from_db()
    last_board.refresh_from_db()

    assert previous_board.rank < next_board.rank
    assert next_board.rank < last_board.rank

    assert previous_board.rank != initial_previous_board_rank
    assert next_board.rank != initial_next_board_rank
    assert last_board.rank != initial_last_board_rank

    assert len(previous_board.rank) == LexoRank.default_rank_length
    assert len(next_board.rank) == LexoRank.default_rank_length
    assert len(last_board.rank) == LexoRank.default_rank_length


def test_rebalancing_ranked_model_does_not_affect_objects_in_another_list(task_factory):
    # given
    task = task_factory.create(rank="aaa")
    another_task = task_factory.create(rank="bbb")

    task_rank = task.rank
    another_task_rank = another_task.rank

    # when
    task.rebalance()

    # then
    task.refresh_from_db()
    another_task.refresh_from_db()

    assert task.rank != task_rank
    assert another_task.rank == another_task_rank

    assert len(task.rank) == LexoRank.default_rank_length
    assert len(another_task.rank) != LexoRank.default_rank_length


def test_moving_ranked_model_to_another_list_updates_place_it_on_top_when_insert_to_bottom_is_set_to_false(  # noqa: E501
    task_factory, task, board
):
    # given
    task_factory.create_batch(10, board=board)
    initial_rank = task.rank
    initial_board = task.board

    # when
    task.board = board
    task.save()

    # then
    assert task.board != initial_board
    assert task.rank != initial_rank
    assert Task.objects.order_by("rank").first() == task


def test_moving_ranked_model_to_another_list_updates_place_it_on_the_bottom_when_insert_to_bottom_is_set_to_true(  # noqa: E501
    user_factory, team, user
):
    # given
    user_factory.create_batch(10, team=team)
    initial_rank = user.rank
    initial_team = user.team

    # when
    user.team = team
    user.save()

    # then
    assert user.team != initial_team
    assert user.rank != initial_rank
    assert User.objects.order_by("rank").last() == user


@pytest.mark.parametrize("rebalancing_length", [100, 128])
def test_rebalancing_required_return_true_for_any_object_when_rank_length_is_exceeded(
    rebalancing_length, board_factory
):
    # given
    boards = board_factory.create_batch(10)
    board_factory.create(rank="d" * (rebalancing_length + 1))

    # when
    with mock.patch.object(LexoRank, "rebalancing_length", rebalancing_length):
        for board in boards:
            assert board.rebalancing_required()


@pytest.mark.parametrize("rebalancing_length", [100, 128])
def test_rebalancing_required_return_true_only_for_objects_in_a_list_when_length_is_exceeded(  # noqa: E501
    rebalancing_length, task_factory, board
):
    # given
    tasks_on_board = task_factory.create_batch(10, board=board)
    another_task = task_factory.create(rank="d" * (rebalancing_length + 1))

    # when
    with mock.patch.object(LexoRank, "rebalancing_length", rebalancing_length):
        for task in tasks_on_board:
            assert not board.rebalancing_required()

        assert another_task.rebalancing_required()


@pytest.mark.parametrize("rebalancing_length", [100, 128])
def test_rebalancing_required_return_false_for_any_object_when_rank_length_is_not_exceeded(  # noqa: E501
    rebalancing_length, board_factory
):
    # given
    boards = board_factory.create_batch(10)
    board_factory.create(rank="d" * (rebalancing_length - 1))

    # when
    with mock.patch.object(LexoRank, "rebalancing_length", rebalancing_length):
        for board in boards:
            assert not board.rebalancing_required()


def test_rebalancing_scheduled_return_false_if_no_rebalancing_were_scheduled(
    task_factory,
):
    # given
    tasks = task_factory.create_batch(10)

    # when
    for task in tasks:
        assert not task.rebalancing_scheduled()


def test_rebalancing_scheduled_return_false_if_rebalancing_was_scheduled_for_another_group(  # noqa: E501
    task_factory,
    board,
    scheduled_rebalancing_factory,
):
    # given
    tasks_on_board = task_factory.create_batch(3, board=board)
    another_tasks = task_factory.create_batch(5)

    scheduled_rebalancing_factory.create(
        with_respect_to=board.pk, model=tasks_on_board[0]._meta.model_name
    )

    # when
    for task in tasks_on_board:
        assert task.rebalancing_scheduled()

    # # when
    for task in another_tasks:
        assert not task.rebalancing_scheduled()


def test_rebalancing_is_scheduled_for_a_list_if_rank_length_exceeds_the_limit(
    task_factory, board
):
    # given
    tasks_on_board = task_factory.create_batch(3, board=board)
    another_tasks = task_factory.create_batch(5)

    # when
    with mock.patch.object(LexoRank, "rebalancing_length", 1):
        tasks_on_board[0].place_on_bottom()

    # then
    for task in tasks_on_board:
        assert task.rebalancing_scheduled()

    for task in another_tasks:
        assert not task.rebalancing_scheduled()


def test_rebalancing_is_scheduled_for_a_whole_list_if_it_dont_have_respected_object(
    board_factory,
):
    # given
    boards = board_factory.create_batch(5)

    # when
    with mock.patch.object(LexoRank, "rebalancing_length", 1):
        boards[0].place_on_bottom()

    # then
    for board in boards:
        assert board.rebalancing_scheduled()


def test_field_value_has_changed_method_with_no_changes(board):
    # then
    assert not board.field_value_has_changed("name")


def test_field_value_has_changed_method(board):
    # when
    board.name = "new name"

    # then
    assert board.field_value_has_changed("name")


def test_field_value_has_changed_method_foreign_key_no_changes(task, board_factory):
    # then
    assert not task.field_value_has_changed("board")


def test_field_value_has_changed_method_foreign_key(task, board_factory):
    # given
    new_board = board_factory.create()

    # when
    task.board = new_board

    # then
    assert task.field_value_has_changed("board")
