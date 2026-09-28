/* mergeSort.c - 위치 기반 분할 (Topic 03)
 *
 * 분할은 공짜다. 인덱스 한가운데를 그냥 자르면 되니까.
 * 대신 합치는 데서 일을 한다. 어떤 입력이 와도 정확히 절반으로 갈리므로
 * 재귀 깊이가 log n으로 고정되고, 최악의 경우에도 O(n log n)이 보장된다.
 * 그 대가가 O(n) 임시 배열이다.
 */
#include <stdlib.h>
#include "sortctx.h"

/* 정렬된 두 구간 [lo..mid], [mid+1..hi]를 buf에 합친 뒤 되돌려 쓴다. */
static void mergeRuns(const SortCtx *c, size_t lo, size_t mid, size_t hi, char *buf)
{
    size_t i = lo, j = mid + 1, k = lo;

    while (i <= mid && j <= hi) {
        /* <= 가 안정성의 핵심이다.
         * 값이 같으면 왼쪽(먼저 들어온 쪽)을 먼저 내보낸다.
         * < 로 바꾸면 오른쪽이 먼저 나가 원래 순서가 뒤집히는데,
         * 결과는 여전히 오름차순이라 눈으로는 보이지 않는다. */
        if (sortCompareAt(c, i, j) <= 0) {
            sortMove(c, buf + k * c->size, sortElemAt(c, i));
            i++;
        } else {
            sortMove(c, buf + k * c->size, sortElemAt(c, j));
            j++;
        }
        k++;
    }

    /* 한쪽이 먼저 바닥나면 남은 쪽은 비교 없이 그대로 복사한다.
     * 정렬된 입력에서 비교 횟수가 줄어드는 이유가 이 구간이다. */
    while (i <= mid) { sortMove(c, buf + k * c->size, sortElemAt(c, i)); i++; k++; }
    while (j <= hi)  { sortMove(c, buf + k * c->size, sortElemAt(c, j)); j++; k++; }

    for (k = lo; k <= hi; k++)
        sortMove(c, sortElemAt(c, k), buf + k * c->size);
}

static void mergeRec(const SortCtx *c, size_t lo, size_t hi, char *buf, size_t depth)
{
    size_t mid;

    sortNoteDepth(c, depth);
    if (lo >= hi) return;              /* 원소 하나는 이미 정렬된 상태 */

    /* (lo + hi) / 2 로 쓰면 인덱스가 클 때 덧셈이 넘칠 수 있다.
     * 구간 길이를 절반 낸 뒤 lo에 더하면 그 위험이 없다. */
    mid = lo + (hi - lo) / 2;

    mergeRec(c, lo, mid, buf, depth + 1);
    mergeRec(c, mid + 1, hi, buf, depth + 1);
    mergeRuns(c, lo, mid, hi, buf);
}

void mergeSort(void *base, size_t n, size_t size,
               SortCompare cmp, SortStats *stats)
{
    SortCtx c;
    char *buf;

    if (n < 2) return;
    if (!sortCtxInit(&c, base, size, cmp, stats)) return;

    /* 버퍼는 맨 위에서 한 번만 잡아 재귀에 물려 내려보낸다.
     * mergeRuns 안에서 매번 잡으면 호출이 O(n)번이라
     * 할당 비용이 알고리즘 비용을 덮어버린다. */
    buf = (char *)malloc(n * size);
    if (buf == NULL) { sortCtxFree(&c); return; }
    sortNoteExtra(&c, n * size);

    mergeRec(&c, 0, n - 1, buf, 1);

    free(buf);
    sortCtxFree(&c);
}
