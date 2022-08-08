from typing import Callable, Dict, Optional, OrderedDict, Tuple, Union

from sortedcontainers import SortedDict

from operator import add, sub


class Result:
    _probs: SortedDict[int, float]
    _num_meas: int

    def __init__(
        self,
        probs: SortedDict[int, float],
        num_meas: int,
    ) -> None:
        self._probs = probs
        self._num_meas = num_meas

    def __getitem__(self, state: Union[int, str]) -> float:
        if isinstance(state, str):
            base = 2
            if state.startswith("0x"):
                base = 16
            state = int(state, base)
        return self._probs[state]

    def __add__(self, other: "Result") -> "Result":
        return self._apply_op(other, add)

    def __sub__(self, other: "Result") -> "Result":
        return self._apply_op(other, sub)

    @staticmethod
    def from_counts(counts: Dict[str, int]) -> "Result":
        base = 2
        some_state = list(counts.keys())[0]
        if some_state.startswith("0x"):
            base = 16
        shots = sum(counts.values())
        probs = SortedDict(
            {int(state, base): count / shots for state, count in counts.items()}
        )
        num_meas = len(some_state)
        return Result(probs, num_meas)

    def without_first_bit(self) -> Tuple["Result", "Result"]:
        cmp = 1 << (self._num_meas - 1)
        strip = cmp - 1
        probs1 = SortedDict({})
        probs2 = SortedDict({})
        for state, prob in self._probs.items():
            if state & cmp:
                probs2[state & strip] = prob
            else:
                probs1[state & strip] = prob
        return Result(probs1, self._num_meas), Result(probs2, self._num_meas)

    def _apply_op(
        self, other: "Result", op: Callable[[float, float], float]
    ) -> "Result":
        if self._num_meas != other._num_meas:
            raise Exception("The number of measurements must be the same")
        first = list(self._probs.items())
        second = list(other._probs.items())
        res_probs = SortedDict({})
        i, j = 0, 0
        while i < len(first) and j < len(second):
            if first[i][0] < second[j][0]:
                res_probs[first[i][0]] = first[i][1]
                i += 1
            elif first[i][0] > second[j][0]:
                res_probs[second[j][0]] = second[j][1]
                j += 1
            elif first[i][0] == second[j][0]:
                res_probs[first[i][0]] = op(first[i][1], second[j][1])
                i += 1
                j += 1
        return Result(res_probs, self._num_meas)
