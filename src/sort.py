"""sort.py - 세 정렬(퀵·병합·힙)의 Python 구현.

C 구현과 같은 알고리즘을 같은 계측 규칙으로 옮긴 것이다.
같은 입력에 대해 비교·이동 횟수가 C와 정확히 일치해야 한다.
일치하지 않으면 두 구현 중 하나가 다른 알고리즘을 돌리고 있다는 뜻이다.

이름은 언어 관례를 따른다 (C: quickSort -> Python: quick_sort).
다만 레지스트리의 name 문자열은 C와 똑같이 둔다 - 그것은 Python 식별자가
아니라 출력 라벨이고, 두 언어의 결과를 나란히 놓고 비교하기 위한 것이다.

표준 모듈만 쓴다.
"""


class SortStats:
    """한 번 정렬하는 동안 모이는 측정값.

    시간은 여기 없다. 시계는 bench 쪽에서 인터페이스 바깥에 둔다.
    extra_slots는 C의 extra_bytes와 직접 비교하지 않는다 -
    Python은 원소 하나의 바이트 수가 고정이 아니기 때문이다.
    """

    def __init__(self):
        self.compares = 0
        self.moves = 0
        self.extra_slots = 0   # 입력 배열 밖에 잡은 원소 칸 수
        self.max_depth = 0

    def reset(self):
        self.__init__()


class SortCtx:
    """정렬 한 번이 들고 다니는 작업 문맥. C의 SortCtx와 같은 역할이다.

    비교와 이동은 반드시 이 객체를 거친다.
    그래야 세 구현의 카운터가 같은 규칙으로 오른다.
    """

    def __init__(self, a, cmp, stats):
        self.a = a
        self.cmp = cmp
        self.stats = stats

    def compare_at(self, i, j):
        if self.stats is not None:
            self.stats.compares += 1
        return self.cmp(self.a[i], self.a[j])

    def swap(self, i, j):
        """교환은 임시 한 칸을 거치므로 이동 3회로 센다 (C와 같은 규칙)."""
        if i == j:
            return
        self.a[i], self.a[j] = self.a[j], self.a[i]
        if self.stats is not None:
            self.stats.moves += 3

    def note_move(self, count=1):
        if self.stats is not None:
            self.stats.moves += count

    def note_depth(self, depth):
        if self.stats is not None and depth > self.stats.max_depth:
            self.stats.max_depth = depth

    def note_extra(self, slots):
        if self.stats is not None:
            self.stats.extra_slots += slots


def compare_key(x, y):
    """기본 비교 함수. (key, tag) 쌍에서 key만 본다.

    tag까지 넣으면 같은 값이 사라져 모든 정렬이 안정해 보인다.
    """
    return (x[0] > y[0]) - (x[0] < y[0])


# ---------------------------------------------------------------- 힙 정렬

def _sift_down(ctx, root, n):
    """root의 값을 자식들과 견주며 제자리까지 끌어내린다.

    재귀 대신 반복문 - 재귀면 호출 스택이 O(log n) 쌓여
    "추가 공간 O(1)"이라는 주장이 거짓이 된다.
    """
    while 2 * root + 1 < n:
        child = 2 * root + 1
        # 두 자식 중 큰 쪽. 작은 쪽과 바꾸면 힙 성질이 다시 깨진다.
        if child + 1 < n and ctx.compare_at(child, child + 1) < 0:
            child += 1
        if ctx.compare_at(root, child) >= 0:
            return
        ctx.swap(root, child)
        root = child


def heap_sort(a, cmp=compare_key, stats=None):
    """C의 heapSort와 같다."""
    n = len(a)
    ctx = SortCtx(a, cmp, stats)
    ctx.note_depth(1)          # 반복 구현이므로 재귀 깊이는 늘 1
    if n < 2:
        return

    # 1단계: 힙 구성. 뒤쪽 절반은 잎이라 이미 힙이므로 n//2-1 부터 거꾸로.
    for i in range(n // 2 - 1, -1, -1):
        _sift_down(ctx, i, n)

    # 2단계: 루트(최대값)를 확정된 자리로.
    # 아래 교환은 값이 같은지 따지지 않는 무조건 교환이다 - 불안정성의 원인.
    for end in range(n - 1, 0, -1):
        ctx.swap(0, end)
        _sift_down(ctx, 0, end)


# ---------------------------------------------------------------- 병합 정렬

def _merge_runs(ctx, lo, mid, hi, buf):
    i, j, k = lo, mid + 1, lo

    while i <= mid and j <= hi:
        # <= 가 안정성의 핵심. 값이 같으면 왼쪽(먼저 들어온 쪽)을 먼저 내보낸다.
        if ctx.compare_at(i, j) <= 0:
            buf[k] = ctx.a[i]
            i += 1
        else:
            buf[k] = ctx.a[j]
            j += 1
        ctx.note_move()
        k += 1

    # 한쪽이 먼저 바닥나면 남은 쪽은 비교 없이 복사한다.
    while i <= mid:
        buf[k] = ctx.a[i]
        ctx.note_move()
        i += 1
        k += 1
    while j <= hi:
        buf[k] = ctx.a[j]
        ctx.note_move()
        j += 1
        k += 1

    for k in range(lo, hi + 1):
        ctx.a[k] = buf[k]
        ctx.note_move()


def _merge_rec(ctx, lo, hi, buf, depth):
    ctx.note_depth(depth)
    if lo >= hi:
        return
    # Python 정수는 자릿수 제한이 없어 (lo+hi)//2 도 안전하지만,
    # C 구현과 같은 식을 쓴다.
    mid = lo + (hi - lo) // 2
    _merge_rec(ctx, lo, mid, buf, depth + 1)
    _merge_rec(ctx, mid + 1, hi, buf, depth + 1)
    _merge_runs(ctx, lo, mid, hi, buf)


def merge_sort(a, cmp=compare_key, stats=None):
    """C의 mergeSort와 같다."""
    n = len(a)
    if n < 2:
        return
    ctx = SortCtx(a, cmp, stats)
    buf = [None] * n           # 버퍼는 한 번만 잡아 재귀에 물려 내려보낸다
    ctx.note_extra(n)
    _merge_rec(ctx, 0, n - 1, buf, 1)


# ---------------------------------------------------------------- 퀵 정렬

PIVOT_LAST = "last"
PIVOT_MEDIAN3 = "median3"
PIVOT_RANDOM = "random"

quick_sort_pivot = PIVOT_MEDIAN3     # 피벗 실험이 여기에 다른 값을 넣는다

_MASK64 = 0xFFFFFFFFFFFFFFFF
_rng_state = 88172645463325252


def quick_sort_seed(seed):
    """시드가 같으면 늘 같은 수열이 나온다 -> 실험이 재현된다."""
    global _rng_state
    _rng_state = seed if seed != 0 else 88172645463325252


def _next_random():
    """C와 같은 xorshift. Python 정수는 무한 자릿수라 64비트로 잘라 준다."""
    global _rng_state
    s = _rng_state
    s ^= (s << 13) & _MASK64
    s ^= s >> 7
    s ^= (s << 17) & _MASK64
    _rng_state = s
    return s


def _median3_index(ctx, lo, mid, hi):
    if ctx.compare_at(lo, mid) < 0:
        if ctx.compare_at(mid, hi) < 0:
            return mid
        return hi if ctx.compare_at(lo, hi) < 0 else lo
    if ctx.compare_at(lo, hi) < 0:
        return lo
    return hi if ctx.compare_at(mid, hi) < 0 else mid


def _place_pivot(ctx, lo, hi):
    """고른 피벗을 맨 뒤로. 그러면 이후 파티션은 전략과 무관하게 같은 코드가 된다."""
    p = hi
    if quick_sort_pivot == PIVOT_MEDIAN3:
        p = _median3_index(ctx, lo, lo + (hi - lo) // 2, hi)
    elif quick_sort_pivot == PIVOT_RANDOM:
        p = lo + _next_random() % (hi - lo + 1)
    if p != hi:
        ctx.swap(p, hi)


def _partition(ctx, lo, hi):
    """Lomuto 파티션. i는 "피벗보다 작다고 확정된 구간의 다음 빈 자리".

    비교가 엄격한 부등호(< 0)이므로 피벗과 값이 같은 원소는 모두 오른쪽에 남는다.
    중복이 많은 입력에서 한쪽으로 쏠리는 원인이다.
    """
    i = lo
    for j in range(lo, hi):
        if ctx.compare_at(j, hi) < 0:
            ctx.swap(i, j)
            i += 1
    ctx.swap(i, hi)
    return i


def _quick_rec(ctx, lo, hi, depth):
    ctx.note_depth(depth)
    if lo >= hi:
        return
    _place_pivot(ctx, lo, hi)
    p = _partition(ctx, lo, hi)
    if p > lo:
        _quick_rec(ctx, lo, p - 1, depth + 1)
    _quick_rec(ctx, p + 1, hi, depth + 1)


def quick_sort(a, cmp=compare_key, stats=None):
    """C의 quickSort와 같다."""
    n = len(a)
    if n < 2:
        return
    ctx = SortCtx(a, cmp, stats)
    _quick_rec(ctx, 0, n - 1, 1)


# ---------------------------------------------------------------- 레지스트리

class SortAlgorithm:
    """C의 SortAlgorithm 구조체에 대응. 뒤의 세 값은 구현이 내세우는 주장이고,
    유닛 테스트가 실측과 맞춰 본다."""

    def __init__(self, name, time_complexity, space_complexity, stable, sort):
        self.name = name
        self.time_complexity = time_complexity
        self.space_complexity = space_complexity
        self.stable = stable
        self.sort = sort


SORT_ALGORITHMS = [
    SortAlgorithm("quickSort", "O(n log n)", "O(log n)", False, quick_sort),
    SortAlgorithm("mergeSort", "O(n log n)", "O(n)",     True,  merge_sort),
    SortAlgorithm("heapSort",  "O(n log n)", "O(1)",     False, heap_sort),
]
