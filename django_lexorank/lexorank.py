import math
import string
from typing import Optional


class LexoRank:
    max_rank_length = 200
    base_symbols = string.ascii_lowercase
    first_symbol = base_symbols[0]
    last_symbol = base_symbols[-1]
    base = len(base_symbols)

    @classmethod
    def char_to_int(cls, char: str) -> int:
        return ord(char) - ord(cls.first_symbol)

    @classmethod
    def int_to_char(cls, num: int) -> str:
        return chr(num + ord(cls.first_symbol))

    @classmethod
    def parse_rank(cls, rank: str) -> list[int]:
        return [cls.char_to_int(char) for char in rank]

    @classmethod
    def format_rank(cls, rank: list[int]) -> str:
        return "".join(map(cls.int_to_char, rank))

    @classmethod
    def align_ranks(cls, previous_rank: str, next_rank: str) -> tuple[str, str]:
        max_len = max(len(previous_rank), len(next_rank))

        if max_len > cls.max_rank_length:
            raise ValueError("Rebalancing Required")

        previous_rank = previous_rank.ljust(max_len, cls.first_symbol)
        next_rank = next_rank.ljust(max_len, cls.first_symbol)

        return previous_rank, next_rank

    @classmethod
    def get_lexorank_in_between(
        cls,
        previous_rank: Optional[str],
        next_rank: Optional[str],
        objects_count: int,
        default_rank_length: int,
        force_reorder: bool = False,
    ) -> str:
        if not previous_rank:
            previous_rank = cls.get_min_rank(
                objects_count=objects_count, default_rank_length=default_rank_length
            )

        if not next_rank:
            next_rank = cls.get_max_rank(
                objects_count=objects_count, default_rank_length=default_rank_length
            )

        if force_reorder:
            previous_rank, next_rank = sorted([previous_rank, next_rank])
        else:
            if not previous_rank < next_rank:
                raise ValueError("Previous rank must go before than next rank.")

        previous_rank, next_rank = cls.align_ranks(previous_rank, next_rank)

        previous_rank_parts = cls.parse_rank(previous_rank)
        next_rank_parts = cls.parse_rank(next_rank)

        total_diff = 0
        for i, previous_rank_part in enumerate(reversed(previous_rank_parts)):
            next_rank_part = next_rank_parts[len(next_rank_parts) - (i + 1)]
            if next_rank_part < previous_rank_part:
                next_rank_part += cls.base
                next_rank_parts[len(next_rank_parts) - (i + 1)] = next_rank_part
                next_rank_parts[len(next_rank_parts) - (i + 2)] -= 1

            diff = next_rank_part - previous_rank_part
            total_diff += diff * (cls.base**i)

        middle_rank_parts = []

        for i, previous_rank_part in enumerate(reversed(previous_rank_parts)):
            to_add = (
                total_diff
                / 2
                / cls.base ** (len(previous_rank_parts) - (i + 1))
                % cls.base
            )
            middle_rank_part = previous_rank_part + to_add
            middle_rank_parts.append(math.floor(middle_rank_part))

        if middle_rank_parts == previous_rank_parts:
            middle_rank_parts.append(
                (ord(cls.last_symbol) - ord(cls.first_symbol)) // 2
            )

        return cls.format_rank(middle_rank_parts)

    @classmethod
    def get_min_rank(cls, objects_count: int, default_rank_length: int) -> str:
        rank_length = cls.get_rank_length(objects_count, default_rank_length)
        return cls.format_rank([0] * rank_length)

    @classmethod
    def get_max_rank(cls, objects_count: int, default_rank_length: int) -> str:
        rank_length = cls.get_rank_length(objects_count, default_rank_length)
        return cls.format_rank([cls.base - 1] * rank_length)

    @classmethod
    def get_rank_step(cls, objects_count: int, default_rank_length: int) -> int:
        rank_length = cls.get_rank_length(
            objects_count=objects_count, default_rank_length=default_rank_length
        )
        return int(cls.base**rank_length / objects_count - 0.5)

    @classmethod
    def get_rank_length(cls, objects_count: int, default_rank_length: int) -> int:
        if objects_count == 0:
            length_required_to_place_all_objects = 1
        else:
            length_required_to_place_all_objects = math.ceil(
                math.log(objects_count, cls.base)
            )
        return min(
            cls.max_rank_length,
            max(length_required_to_place_all_objects * 2, default_rank_length),
        )

    @classmethod
    def increment_rank(
        cls, rank: str, objects_count: int, default_rank_length: int
    ) -> str:
        step = cls.get_rank_step(
            objects_count=objects_count, default_rank_length=default_rank_length
        )
        rank_parts = LexoRank.parse_rank(rank)

        for i in range(len(rank_parts) - 1, -1, -1):
            if step == 0:
                break

            total = rank_parts[i] + step
            rank_parts[i] = total % cls.base
            step = total // cls.base

        if step > 0:
            rank_parts = [step] + rank_parts

        return LexoRank.format_rank(rank_parts)
