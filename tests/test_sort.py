"""test_sort.py - Python 구현의 정확성과 "주장" 검증.

test_sort.c와 같은 항목을 같은 순서로 검사한다.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import sort as sortmod
from sort import SORT_ALGORITHMS, SortStats, compare_key, quick_sort_seed

sys.path.insert(0, os.path.dirname(__file__))
from main import make_input, is_sorted, is_stable   # noqa: E402

SHAPES = ["random", "sorted", "reverse", "few_unique"]


class TestCorrectness(unittest.TestCase):
    """크기 0~200, 네 가지 입력 모양 전부에서 정확히 정렬되는가."""

    def test_all_algorithms_sort(self):
        for alg in SORT_ALGORITHMS:
            for n in range(0, 201, 7):
                for shape in SHAPES:
                    data = make_input(n, shape, 12345 + n)
                    work = list(data)
                    quick_sort_seed(999)
                    alg.sort(work, compare_key, SortStats())
                    self.assertTrue(is_sorted(work),
                                    "%s: n=%d shape=%s" % (alg.name, n, shape))

    def test_matches_builtin_sorted(self):
        """표준 sorted()와 키 수열이 일치하는지 - 독립 기준과의 대조."""
        for alg in SORT_ALGORITHMS:
            for n in range(0, 201, 13):
                for shape in SHAPES:
                    data = make_input(n, shape, 4242 + n)
                    work = list(data)
                    quick_sort_seed(999)
                    alg.sort(work, compare_key, SortStats())
                    self.assertEqual([x[0] for x in work],
                                     sorted(x[0] for x in data),
                                     "%s: n=%d shape=%s" % (alg.name, n, shape))


class TestEdgeCases(unittest.TestCase):
    def test_empty(self):
        for alg in SORT_ALGORITHMS:
            a = []
            alg.sort(a, compare_key, SortStats())
            self.assertEqual(a, [])

    def test_single(self):
        for alg in SORT_ALGORITHMS:
            a = [(42, 0)]
            alg.sort(a, compare_key, SortStats())
            self.assertEqual(a, [(42, 0)])

    def test_all_same(self):
        for alg in SORT_ALGORITHMS:
            a = [(7, i) for i in range(64)]
            quick_sort_seed(999)
            alg.sort(a, compare_key, SortStats())
            self.assertTrue(all(x[0] == 7 for x in a), alg.name)

    def test_stats_none(self):
        """stats가 None이면 측정하지 않고 정렬만 해야 한다."""
        for alg in SORT_ALGORITHMS:
            a = [(16 - i, i) for i in range(16)]
            quick_sort_seed(999)
            alg.sort(a, compare_key, None)
            self.assertTrue(is_sorted(a), alg.name)


class TestStabilityClaim(unittest.TestCase):
    """레지스트리의 stable 주장이 실측과 맞는가.

    반드시 중복이 많은 입력에서 재야 한다. 중복이 거의 없으면
    불안정한 정렬도 우연히 안정한 결과를 내서 운을 측정하게 된다.
    """

    def test_claim_matches_measurement(self):
        for alg in SORT_ALGORITHMS:
            a = make_input(500, "few_unique", 777)
            quick_sort_seed(999)
            alg.sort(a, compare_key, SortStats())
            measured = is_stable(a)
            self.assertEqual(measured, alg.stable,
                             "%s: 주장=%s 실측=%s"
                             % (alg.name, alg.stable, measured))


class TestInstrumentation(unittest.TestCase):
    def test_counters_move(self):
        for alg in SORT_ALGORITHMS:
            a = make_input(256, "random", 555)
            st = SortStats()
            quick_sort_seed(999)
            alg.sort(a, compare_key, st)
            self.assertGreater(st.compares, 0, alg.name)
            self.assertGreater(st.moves, 0, alg.name)

    def test_space_claims(self):
        a = make_input(256, "random", 555)
        st = SortStats()
        sortmod.merge_sort(a, compare_key, st)
        self.assertEqual(st.extra_slots, 256, "mergeSort: 버퍼 n칸")
        self.assertGreater(st.max_depth, 1, "mergeSort: 재귀 깊이 기록")

        a = make_input(256, "random", 555)
        st = SortStats()
        sortmod.heap_sort(a, compare_key, st)
        self.assertEqual(st.extra_slots, 0, "heapSort: 추가 칸 없음")
        self.assertEqual(st.max_depth, 1, "heapSort: 반복 구현")


class TestStabilityDetector(unittest.TestCase):
    """판정기가 고장나 있으면 위의 통과가 아무것도 증명하지 못한다."""

    def test_detector_works(self):
        self.assertTrue(is_stable([(1, 0), (1, 1), (2, 2)]))
        self.assertFalse(is_stable([(1, 1), (1, 0), (2, 2)]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
