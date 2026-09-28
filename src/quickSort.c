/* quickSort.c - 값 기반 분할 (Topic 04)
 *
 * 병합 정렬과 정확히 반대의 시소다. 나누는 데서 일을 다 하고(파티션),
 * 합칠 때는 아무것도 하지 않는다. 대신 얼마나 균등하게 갈리느냐가
 * 피벗 선택에 달려 있어서, 피벗이 계속 한쪽 끝값이면 O(n^2)로 무너진다.
 *
 * 파티션 로직은 한 벌만 두고 피벗 선택 전략만 갈아끼운다.
 * 그래야 실험이 재는 것이 순수하게 "전략의 효과"가 된다.
 */
#include "sortctx.h"

/* 기본값은 median-of-3. 피벗 실험이 여기에 다른 값을 넣는다. */
QuickPivot quickSortPivot = QUICK_PIVOT_MEDIAN3;

/* xorshift 의사난수. 시드가 같으면 늘 같은 수열이 나오므로 실험이 재현된다.
 * 상태가 0이면 영원히 0만 내놓기 때문에 0은 기본값으로 되돌린다. */
static unsigned long long rngState = 88172645463325252ULL;

static unsigned long long nextRandom(void)
{
    rngState ^= rngState << 13;
    rngState ^= rngState >> 7;
    rngState ^= rngState << 17;
    return rngState;
}

void quickSortSeed(unsigned long long seed)
{
    rngState = (seed != 0) ? seed : 88172645463325252ULL;
}

/* 세 값 중 중앙값의 인덱스.
 * 정렬된 입력에서도 첫·중간·끝의 중앙값은 실제 중앙 근처라 한쪽 쏠림을 막는다. */
static size_t median3Index(const SortCtx *c, size_t lo, size_t mid, size_t hi)
{
    if (sortCompareAt(c, lo, mid) < 0) {
        if (sortCompareAt(c, mid, hi) < 0) return mid;
        return sortCompareAt(c, lo, hi) < 0 ? hi : lo;
    }
    if (sortCompareAt(c, lo, hi) < 0) return lo;
    return sortCompareAt(c, mid, hi) < 0 ? hi : mid;
}

/* 고른 피벗을 맨 뒤로 보내 둔다.
 * 그러면 이후 파티션은 전략과 무관하게 완전히 같은 코드가 된다. */
static void placePivot(const SortCtx *c, size_t lo, size_t hi)
{
    size_t p = hi;

    switch (quickSortPivot) {
    case QUICK_PIVOT_MEDIAN3:
        p = median3Index(c, lo, lo + (hi - lo) / 2, hi);
        break;
    case QUICK_PIVOT_RANDOM:
        p = lo + (size_t)(nextRandom() % (unsigned long long)(hi - lo + 1));
        break;
    case QUICK_PIVOT_LAST:
    default:
        break;   /* 이미 맨 뒤가 피벗 */
    }
    if (p != hi) sortSwap(c, p, hi);
}

/* Lomuto 파티션.
 * i는 "피벗보다 작다고 확정된 구간의 다음 빈 자리", j는 훑는 포인터.
 *
 * 교과서는 i = lo - 1 로 시작하지만 size_t는 부호가 없어
 * lo가 0이면 그 자리에서 거대한 수로 돌아간다. i의 의미를 한 칸 옮겨 피했다.
 *
 * 모든 비교는 "원소 vs 피벗" 하나뿐이고 원소끼리 직접 견주는 일은 없다.
 * 비교가 < 0 (엄격한 부등호)이므로 피벗과 **값이 같은** 원소는 모두
 * 오른쪽에 남는다. 중복이 많은 입력에서 한쪽으로 쏠리는 원인이며,
 * 이를 풀려면 3-way 파티션(Dutch national flag)이 필요하다. */
static size_t partition(const SortCtx *c, size_t lo, size_t hi)
{
    size_t i = lo;
    size_t j;

    for (j = lo; j < hi; j++) {
        if (sortCompareAt(c, j, hi) < 0) {
            sortSwap(c, i, j);
            i++;
        }
    }
    sortSwap(c, i, hi);
    return i;   /* 피벗의 최종 위치. 이 자리는 다시 건드리지 않는다. */
}

static void quickRec(const SortCtx *c, size_t lo, size_t hi, size_t depth)
{
    size_t p;

    sortNoteDepth(c, depth);
    if (lo >= hi) return;

    placePivot(c, lo, hi);
    p = partition(c, lo, hi);

    /* p가 lo면 왼쪽이 비어 있다. p - 1을 그냥 쓰면 size_t가 되돌아간다. */
    if (p > lo) quickRec(c, lo, p - 1, depth + 1);
    quickRec(c, p + 1, hi, depth + 1);
}

void quickSort(void *base, size_t n, size_t size,
               SortCompare cmp, SortStats *stats)
{
    SortCtx c;

    if (n < 2) return;
    if (!sortCtxInit(&c, base, size, cmp, stats)) return;
    quickRec(&c, 0, n - 1, 1);
    sortCtxFree(&c);
}
