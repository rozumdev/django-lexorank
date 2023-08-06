import math
import string
from typing import List, Optional, Tuple


class LexoRank:
    default_rank_length = 6
    rebalancing_length = 128
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
    def parse_rank(cls, rank: str) -> List[int]:
        return [cls.char_to_int(char) for char in rank]

    @classmethod
    def format_rank(cls, rank: List[int]) -> str:
        return "".join(map(cls.int_to_char, rank))

    @classmethod
    def align_ranks(cls, previous_rank: str, next_rank: str) -> Tuple[str, str]:
        max_len = max(len(previous_rank), len(next_rank))

        if max_len > cls.max_rank_length:
            raise ValueError("Rebalancing Required")

        previous_rank = previous_rank.ljust(max_len, cls.first_symbol)
        next_rank = next_rank.ljust(max_len, cls.last_symbol)

        return previous_rank, next_rank

    @classmethod
    def get_lexorank_in_between(
        cls,
        previous_rank: Optional[str],
        next_rank: Optional[str],
        objects_count: int,
        force_reorder: bool = False,
    ) -> str:
        if not previous_rank:
            previous_rank = cls.get_min_rank(objects_count=objects_count)

        if not next_rank:
            next_rank = cls.get_max_rank(objects_count=objects_count)

        previous_rank, next_rank = cls.align_ranks(previous_rank, next_rank)

        if force_reorder:
            previous_rank, next_rank = sorted([previous_rank, next_rank])
        else:
            if not previous_rank < next_rank:
                raise ValueError("Previous rank must go before than next rank.")

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

        middle_rank_parts = []  # type: ignore[var-annotated]

        offset = 0
        for i, previous_rank_part in enumerate(reversed(previous_rank_parts)):
            to_add = total_diff / 2 / cls.base**i % cls.base
            middle_rank_part = previous_rank_part + to_add + offset
            offset = 0

            if middle_rank_part > cls.base:
                offset = 1
                middle_rank_part -= cls.base

            middle_rank_parts.insert(0, math.floor(middle_rank_part))

        if offset:
            middle_rank_parts.insert(0, cls.char_to_int(cls.first_symbol))

        if middle_rank_parts == previous_rank_parts:
            middle_rank_parts.append(
                (cls.char_to_int(cls.last_symbol) - cls.char_to_int(cls.first_symbol))
                // 2
            )

        return cls.format_rank(middle_rank_parts)

    @classmethod
    def get_min_rank(cls, objects_count: int) -> str:
        rank_length = cls.get_rank_length(objects_count)
        return cls.format_rank([0] * rank_length)

    @classmethod
    def get_max_rank(cls, objects_count: int) -> str:
        rank_length = cls.get_rank_length(objects_count)
        return cls.format_rank([cls.char_to_int(cls.last_symbol)] * rank_length)

    @classmethod
    def get_rank_step(cls, objects_count: int) -> int:
        rank_length = cls.get_rank_length(objects_count=objects_count)
        return int(cls.base**rank_length / objects_count - 0.5)

    @classmethod
    def get_rank_length(cls, objects_count: int) -> int:
        if objects_count == 0:
            length_required_to_place_all_objects = 1
        else:
            length_required_to_place_all_objects = math.ceil(
                math.log(objects_count, cls.base)
            )
        return min(
            cls.max_rank_length,
            max(length_required_to_place_all_objects * 2, cls.default_rank_length),
        )

    @classmethod
    def increment_rank(cls, rank: str, objects_count: int) -> str:
        step = cls.get_rank_step(objects_count=objects_count)
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
