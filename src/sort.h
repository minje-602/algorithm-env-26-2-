/* sort.h - 세 정렬(퀵·병합·힙)을 하나의 공통 인터페이스로 묶는다.
 *
 * C에는 interface도 class도 없다. 대신 함수 포인터를 담은 구조체를 쓴다.
 * 비교 규약은 표준 라이브러리의 qsort와 똑같이 맞췄다.
 */
#ifndef SORT_H
#define SORT_H

#include <stddef.h>

/* 비교 함수. qsort와 같은 규약: a<b면 음수, a==b면 0, a>b면 양수.
 * 이 함수 포인터 덕분에 정렬이 원소의 타입을 몰라도 된다.
 * 원소 타입을 모른다는 것이 안정성 측정의 전제다. */
typedef int (*SortCompare)(const void *a, const void *b);

/* 한 번 정렬하는 동안 모인 측정값.
 * 시간은 여기 없다 - 시계는 bench가 인터페이스 바깥에서 든다.
 * 여기에는 시계와 무관하게 재현되는 값만 담는다. */
typedef struct SortStats {
    size_t compares;    /* 비교 함수를 부른 횟수 */
    size_t moves;       /* 원소를 복사한 횟수 (교환 한 번은 3) */
    size_t extraBytes;  /* 입력 배열 밖에 잡은 작업 공간의 최대 바이트 */
    size_t maxDepth;    /* 재귀 깊이의 최댓값. 반복문만 쓰면 1 */
} SortStats;

/* 정렬 한 가지. 이 구조체가 이 과제의 "인터페이스"다.
 * 뒤의 세 값은 구현이 스스로 내세우는 주장이고,
 * 유닛 테스트가 실측과 맞춰 보아 거짓말을 잡는다. */
typedef struct SortAlgorithm {
    const char *name;
    const char *timeComplexity;   /* 평균 시간복잡도 */
    const char *spaceComplexity;  /* 추가 메모리 */
    int stable;                   /* 안정 정렬이라고 주장하는 값 */
    /* base[0..n-1]을 제자리에서 오름차순 정렬한다. 원소 하나는 size 바이트다.
     * stats가 NULL이면 측정하지 않는다. */
    void (*sort)(void *base, size_t n, size_t size,
                 SortCompare cmp, SortStats *stats);
} SortAlgorithm;

void quickSort(void *base, size_t n, size_t size, SortCompare cmp, SortStats *stats);
void mergeSort(void *base, size_t n, size_t size, SortCompare cmp, SortStats *stats);
void heapSort (void *base, size_t n, size_t size, SortCompare cmp, SortStats *stats);

/* 퀵 정렬의 피벗 선택 전략. 기본은 median-of-3.
 * 피벗 실험이 여기에 다른 값을 넣어 최악의 경우를 재현한다. */
typedef enum QuickPivot {
    QUICK_PIVOT_LAST,      /* 마지막 원소 - 정렬된 입력에서 O(n^2) */
    QUICK_PIVOT_MEDIAN3,   /* 첫·중간·끝의 중앙값 */
    QUICK_PIVOT_RANDOM     /* 무작위 */
} QuickPivot;

extern QuickPivot quickSortPivot;
void quickSortSeed(unsigned long long seed);  /* 시드 고정 -> 실험 재현 */

/* 구현 셋을 담은 표. 호출하는 쪽은 이 표만 훑으면 된다. */
extern const SortAlgorithm SORT_ALGORITHMS[];
extern const size_t SORT_ALGORITHM_COUNT;

void sortStatsReset(SortStats *stats);
int  sortCompareInt(const void *a, const void *b);  /* int 배열용 기본 비교 */

#endif /* SORT_H */
