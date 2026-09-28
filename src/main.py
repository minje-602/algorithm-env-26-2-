"""main.py - 실험 수행 (Python 쪽).

main.c와 같은 실험을 같은 시드로 돌린다.
비교·이동 횟수는 C와 정확히 일치해야 한다 - 알고리즘이 하는 일의 양은
언어와 무관하기 때문이다. 반대로 시간과 메모리는 언어에 종속된다.

    python3 src/main.py          사람이 읽는 표
    python3 src/main.py --csv    같은 측정을 CSV로
"""
import sys
import time

import sort as sortmod
from sort import SORT_ALGORITHMS, SortStats, compare_key, quick_sort_seed

SEED = 20260930
REPEATS = 1   # 카운터는 반복해도 같은 값이다. Python은 느리므로 1회로 충분하다.
MASK64 = 0xFFFFFFFFFFFFFFFF

SHAPES = ["random", "sorted", "reverse", "few_unique"]

# ------------------------------------------------------------ 입력 생성
# bench.c의 makeInput을 그대로 옮긴 것이다.
# 왼쪽 시프트를 64비트로 자르지 않으면 C의 오버플로우 동작과 달라져
# 같은 시드인데 다른 수열이 나온다 - 그러면 대조가 무의미해진다.

_input_state = 0


def _input_random():
    global _input_state
    s = _input_state
    s ^= (s << 13) & MASK64
    s ^= s >> 7
    s ^= (s << 17) & MASK64
    _input_state = s
    return s


def make_input(n, shape, seed):
    global _input_state
    _input_state = seed if seed != 0 else 0x9E3779B97F4A7C15

    a = []
    for i in range(n):
        if shape == "sorted":
            key = i
        elif shape == "reverse":
            key = n - i
        elif shape == "few_unique":
            key = _input_random() % 8
        else:
            key = _input_random() % 1000000
        a.append((key, i))     # tag = 입력 순서. 안정성 판정의 근거
    return a


# ------------------------------------------------------------ 검증
def is_sorted(a):
    return all(a[i - 1][0] <= a[i][0] for i in range(1, len(a)))


def has_duplicates(a):
    return any(a[i - 1][0] == a[i][0] for i in range(1, len(a)))


def is_stable(a):
    return all(not (a[i - 1][0] == a[i][0] and a[i - 1][1] > a[i][1])
               for i in range(1, len(a)))


# ------------------------------------------------------------ 측정
class BenchResult:
    def __init__(self):
        self.milliseconds = 0.0
        self.stats = SortStats()
        self.sorted = 0
        self.stable = -1


def bench_run(alg, n, shape, seed, repeats):
    r = BenchResult()
    origin = make_input(n, shape, seed)
    work = []

    best = None
    for _ in range(repeats):
        work = list(origin)          # 복사는 측정 구간 밖
        r.stats.reset()
        quick_sort_seed(seed)

        t0 = time.perf_counter()
        alg.sort(work, compare_key, r.stats)
        t1 = time.perf_counter()

        ms = (t1 - t0) * 1000.0
        if best is None or ms < best:
            best = ms               # 방해는 시간을 늘리기만 하므로 최솟값을 쓴다

    r.milliseconds = best if best is not None else 0.0
    r.sorted = 1 if is_sorted(work) else 0
    # 중복이 없으면 안정성 검사가 무조건 통과한다. 판정 불가로 구분한다.
    r.stable = (1 if is_stable(work) else 0) if has_duplicates(work) else -1
    return r


# ------------------------------------------------------------ 출력
csv_mode = False


def row_table(experiment, label, shape, n, r):
    print("  %-11s %-11s %7d %9.3f %12d %12d %7d %9d   %-3s %-3s" % (
        label, shape, n, r.milliseconds,
        r.stats.compares, r.stats.moves, r.stats.max_depth, r.stats.extra_slots,
        "OK" if r.sorted else "X",
        "-" if r.stable < 0 else ("Y" if r.stable else "N")))


def row_csv(experiment, label, shape, n, r):
    print("%s,%s,%s,%d,%.6f,%d,%d,%d,%d,%d,%d" % (
        experiment, label, shape, n, r.milliseconds,
        r.stats.compares, r.stats.moves, r.stats.max_depth,
        r.stats.extra_slots, r.sorted, r.stable))


def section(title):
    if csv_mode:
        return
    print("\n%s\n" % title)
    print("  %-11s %-11s %7s %9s %12s %12s %7s %9s   %-3s %-3s" % (
        "algorithm", "shape", "n", "time(ms)", "compares", "moves",
        "depth", "extra(칸)", "srt", "stb"))
    print("  " + "-" * 100)


def blank():
    if not csv_mode:
        print()


# ------------------------------------------------------------ 실험
def experiment_shapes(n, repeats, sink):
    section("[1] 입력 모양별 비교")
    for shape in SHAPES:
        for alg in SORT_ALGORITHMS:
            r = bench_run(alg, n, shape, SEED, repeats)
            sink("shapes", alg.name, shape, n, r)
        blank()


def experiment_growth(repeats, sink):
    sizes = [1000, 2000, 4000, 8000, 16000, 32000]
    section("[2] 입력 크기에 따른 변화 (random)")
    for alg in SORT_ALGORITHMS:
        for n in sizes:
            r = bench_run(alg, n, "random", SEED, repeats)
            sink("growth", alg.name, "random", n, r)
        blank()


def experiment_pivot(n, repeats, sink):
    """피벗이 마지막 원소면 정렬된 입력에서 재귀 깊이가 n까지 간다.

    Python 기본 재귀 한도는 1000이라 그대로는 RecursionError가 난다.
    C에서는 같은 깊이가 아무 조치 없이 돌았다 - 언어가 거는 제약이지
    알고리즘의 성질이 아니므로, 한도를 올려 같은 n으로 맞춘다.
    """
    quick = next(a for a in SORT_ALGORITHMS if a.name == "quickSort")
    modes = [(sortmod.PIVOT_LAST,    "quick:last"),
             (sortmod.PIVOT_MEDIAN3, "quick:med3"),
             (sortmod.PIVOT_RANDOM,  "quick:rand")]

    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old_limit, n + 2000))
    saved = sortmod.quick_sort_pivot

    section("[3] 피벗 전략 비교 (정렬된 입력 = 퀵 정렬의 최악)")
    try:
        for mode, label in modes:
            sortmod.quick_sort_pivot = mode
            r = bench_run(quick, n, "sorted", SEED, repeats)
            sink("pivot", label, "sorted", n, r)
    except RecursionError:
        if not csv_mode:
            print("  (재귀 한도 초과 - Python에서는 이 깊이를 끝까지 갈 수 없다)")
    finally:
        sortmod.quick_sort_pivot = saved
        sys.setrecursionlimit(old_limit)
    blank()


def main():
    global csv_mode
    n, pivot_n = 8000, 4000

    # 퀵 정렬은 입력에 따라 재귀가 깊어진다.
    #   - 중복이 많은 입력(n=8000)에서 실측 깊이 1033  <- 파티션의 중복 쌓임
    #   - 피벗이 마지막 원소면 정렬된 입력에서 깊이가 n까지
    # Python 기본 한도는 1000이라 둘 다 RecursionError가 난다.
    # C에서는 같은 깊이가 아무 조치 없이 돌았다 - 알고리즘의 성질이 아니라
    # 언어가 거는 제약이므로, 한도를 올려 C와 같은 조건으로 맞춘다.
    sys.setrecursionlimit(50000)

    csv_mode = len(sys.argv) > 1 and sys.argv[1] == "--csv"
    sink = row_csv if csv_mode else row_table

    if csv_mode:
        print("experiment,algorithm,shape,n,ms,compares,moves,depth,"
              "extra_slots,sorted,stable")
    else:
        print("정렬 비교 (Python): 퀵 / 병합 / 힙")
        print("seed = %d, 반복 %d회 중 최솟값" % (SEED, REPEATS))

    experiment_shapes(n, REPEATS, sink)
    experiment_growth(REPEATS, sink)
    experiment_pivot(pivot_n, REPEATS, sink)


if __name__ == "__main__":
    main()
