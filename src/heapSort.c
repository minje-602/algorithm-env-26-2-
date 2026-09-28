/* heapSort.c - 수업에서 다루지 않은 정렬 (Wikipedia: Heapsort)
 *
 * 선택 정렬의 "남은 것 중 최대값을 찾아 뒤로 보낸다"를 그대로 따르되,
 * 최대값 탐색을 선형 스캔 O(n) 대신 최대 힙 O(log n)으로 바꾼 것이다.
 * 그래서 O(n^2)이 O(n log n)이 된다.
 *
 * 배열을 트리로 읽는 규칙: 인덱스 i의 자식은 2i+1, 2i+2.
 * 포인터도 노드 객체도 없으므로 추가 메모리가 필요 없다.
 */
#include "sortctx.h"

/* root에 있는 값을 자식들과 견주며 제자리까지 끌어내린다.
 * 전제: root의 두 서브트리는 이미 힙이다.
 *
 * 재귀 대신 반복문으로 쓴 이유 - 재귀면 호출 스택이 O(log n) 쌓여
 * 이 정렬이 내세우는 "추가 공간 O(1)" 주장이 거짓이 된다. */
static void siftDown(const SortCtx *c, size_t root, size_t n)
{
    while (2 * root + 1 < n) {
        size_t child = 2 * root + 1;

        /* 두 자식 중 큰 쪽을 고른다.
         * 작은 쪽과 바꾸면 올라간 값이 반대편 자식보다 작아져 힙이 다시 깨진다. */
        if (child + 1 < n && sortCompareAt(c, child, child + 1) < 0)
            child++;

        if (sortCompareAt(c, root, child) >= 0)
            return;                       /* 이미 부모가 크거나 같으면 끝 */

        sortSwap(c, root, child);
        root = child;
    }
}

void heapSort(void *base, size_t n, size_t size,
              SortCompare cmp, SortStats *stats)
{
    SortCtx c;
    size_t i, end;

    if (n < 2) return;
    if (!sortCtxInit(&c, base, size, cmp, stats)) return;
    sortNoteDepth(&c, 1);   /* 반복 구현이므로 재귀 깊이는 늘 1 */

    /* 1단계: 힙 구성.
     * 뒤쪽 절반은 잎 노드라 이미 힙이므로 마지막 부모(n/2-1)부터 거꾸로 간다.
     * 아래쪽 노드일수록 끌어내릴 거리가 짧아 전체가 O(n log n)이 아니라 O(n)이다.
     *
     * size_t는 부호가 없어 i가 0에서 더 줄면 거대한 수로 돌아간다.
     * `i-- > 0` 관용구가 그 함정을 피한다. */
    for (i = n / 2; i-- > 0; )
        siftDown(&c, i, n);

    /* 2단계: 최대값(루트)을 확정된 자리로 보내고 힙을 하나 줄인다.
     *
     * 아래 교환은 두 값이 같은지 **따지지 않는 무조건 교환**이다.
     * 멀리 떨어진 두 원소를 맞바꾸므로 같은 값의 원래 순서가 깨진다 -
     * 힙 정렬이 불안정한 이유가 이 한 줄이고, 최소 반례는 n=2다.
     * (레지스트리의 stable = 0 이 가리키는 근거) */
    for (end = n - 1; end > 0; end--) {
        sortSwap(&c, 0, end);
        siftDown(&c, 0, end);
    }

    sortCtxFree(&c);
}
