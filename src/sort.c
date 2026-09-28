/* sort.c - 구현들이 공통으로 쓰는 도구와 알고리즘 레지스트리. */
#include <stdlib.h>
#include <string.h>
#include "sortctx.h"

int sortCtxInit(SortCtx *c, void *base, size_t size,
                SortCompare cmp, SortStats *stats)
{
    c->base  = (char *)base;
    c->size  = size;
    c->cmp   = cmp;
    c->stats = stats;
    c->tmp   = (char *)malloc(size);
    if (c->tmp == NULL) return 0;
    sortNoteExtra(c, size);   /* 임시 한 칸도 입력 배열 밖의 공간이다 */
    return 1;
}

void sortCtxFree(SortCtx *c)
{
    free(c->tmp);
    c->tmp = NULL;
}

void *sortElemAt(const SortCtx *c, size_t i)
{
    return c->base + i * c->size;
}

/* 비교는 반드시 이 함수를 거친다. 그래야 세 구현의 카운터가 같은 규칙으로 오른다. */
int sortCompareElem(const SortCtx *c, const void *a, const void *b)
{
    if (c->stats != NULL) c->stats->compares++;
    return c->cmp(a, b);
}

int sortCompareAt(const SortCtx *c, size_t i, size_t j)
{
    return sortCompareElem(c, sortElemAt(c, i), sortElemAt(c, j));
}

/* 타입을 모르므로 바이트 단위로 옮긴다.
 * tmp를 거쳐야 하므로 교환 한 번이 이동 3회다. */
void sortSwap(const SortCtx *c, size_t i, size_t j)
{
    char *a, *b;
    if (i == j) return;
    a = (char *)sortElemAt(c, i);
    b = (char *)sortElemAt(c, j);
    memcpy(c->tmp, a, c->size);
    memcpy(a, b, c->size);
    memcpy(b, c->tmp, c->size);
    if (c->stats != NULL) c->stats->moves += 3;
}

void sortMove(const SortCtx *c, void *dst, const void *src)
{
    memcpy(dst, src, c->size);
    if (c->stats != NULL) c->stats->moves++;
}

void sortNoteDepth(const SortCtx *c, size_t depth)
{
    if (c->stats != NULL && depth > c->stats->maxDepth)
        c->stats->maxDepth = depth;
}

void sortNoteExtra(const SortCtx *c, size_t bytes)
{
    if (c->stats != NULL) c->stats->extraBytes += bytes;
}

void sortStatsReset(SortStats *stats)
{
    if (stats != NULL) memset(stats, 0, sizeof(*stats));
}

int sortCompareInt(const void *a, const void *b)
{
    int x = *(const int *)a;
    int y = *(const int *)b;
    return (x > y) - (x < y);   /* 뺄셈은 오버플로우 위험이 있다 */
}

/* 구현 표. 뒤의 세 값은 구현이 내세우는 "주장"이고,
 * 유닛 테스트가 실측과 맞춰 보아 거짓이면 실패시킨다. */
const SortAlgorithm SORT_ALGORITHMS[] = {
    { "quickSort", "O(n log n)", "O(log n)", 0, quickSort },
    { "mergeSort", "O(n log n)", "O(n)",     1, mergeSort },
    { "heapSort",  "O(n log n)", "O(1)",     0, heapSort  },
};

const size_t SORT_ALGORITHM_COUNT =
    sizeof(SORT_ALGORITHMS) / sizeof(SORT_ALGORITHMS[0]);
