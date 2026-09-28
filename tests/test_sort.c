/* test_sort.c - 정확성과 "주장"의 검증.
 *
 * 벤치마크 숫자가 아무리 예뻐도 결과가 틀렸으면 의미가 없다.
 * 테스트도 레지스트리를 훑으므로, 정렬을 하나 더 넣으면
 * 그 순간부터 같은 검사를 받는다.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sort.h"
#include "bench.h"

static int passed = 0;
static int failed = 0;

static void check(int cond, const char *what)
{
    if (cond) passed++;
    else { failed++; printf("  [FAIL] %s\n", what); }
}

static int ascending(const Record *a, size_t n)
{
    size_t i;
    for (i = 1; i < n; i++)
        if (a[i - 1].key > a[i].key) return 0;
    return 1;
}

static int stableResult(const Record *a, size_t n)
{
    size_t i;
    for (i = 1; i < n; i++)
        if (a[i - 1].key == a[i].key && a[i - 1].tag > a[i].tag) return 0;
    return 1;
}

/* 표준 라이브러리 qsort와 값 수열이 일치하는지 본다.
 * 독립적으로 구현된 기준과 맞춰 보는 것이라, 내 구현이 통째로 틀려도 잡힌다. */
static int matchesQsort(const Record *sorted, const Record *input, size_t n)
{
    Record *ref = (Record *)malloc(sizeof(Record) * (n ? n : 1));
    size_t i;
    int ok = 1;

    memcpy(ref, input, sizeof(Record) * n);
    qsort(ref, n, sizeof(Record), recordCompare);
    for (i = 0; i < n; i++)
        if (ref[i].key != sorted[i].key) { ok = 0; break; }
    free(ref);
    return ok;
}

/* 1) 크기 0~200, 네 가지 입력 모양 전부에서 정확히 정렬되는가 */
static void testCorrectness(void)
{
    size_t a;

    for (a = 0; a < SORT_ALGORITHM_COUNT; a++) {
        const SortAlgorithm *alg = &SORT_ALGORITHMS[a];
        int allSorted = 1, allMatch = 1;
        char msg[160];
        size_t n;
        int shape;

        for (n = 0; n <= 200; n += 7) {
            for (shape = 0; shape < INPUT_SHAPE_COUNT; shape++) {
                Record *input = (Record *)malloc(sizeof(Record) * (n ? n : 1));
                Record *work  = (Record *)malloc(sizeof(Record) * (n ? n : 1));
                SortStats st;

                makeInput(input, n, (InputShape)shape, 12345ULL + n);
                memcpy(work, input, sizeof(Record) * n);
                sortStatsReset(&st);
                quickSortSeed(999ULL);
                alg->sort(work, n, sizeof(Record), recordCompare, &st);

                if (!ascending(work, n)) allSorted = 0;
                if (!matchesQsort(work, input, n)) allMatch = 0;

                free(input);
                free(work);
            }
        }
        snprintf(msg, sizeof(msg), "%s: n=0~200 / 4개 입력 모양 모두 오름차순", alg->name);
        check(allSorted, msg);
        snprintf(msg, sizeof(msg), "%s: qsort 결과와 일치", alg->name);
        check(allMatch, msg);
    }
}

/* 2) 경계 조건 */
static void testEdgeCases(void)
{
    size_t a;

    for (a = 0; a < SORT_ALGORITHM_COUNT; a++) {
        const SortAlgorithm *alg = &SORT_ALGORITHMS[a];
        SortStats st;
        char msg[160];
        Record one[1];
        Record same[64];
        size_t k;
        int ok;

        sortStatsReset(&st);
        alg->sort(NULL, 0, sizeof(Record), recordCompare, &st);
        snprintf(msg, sizeof(msg), "%s: 빈 배열에서 안전", alg->name);
        check(1, msg);

        one[0].key = 42; one[0].tag = 0;
        sortStatsReset(&st);
        alg->sort(one, 1, sizeof(Record), recordCompare, &st);
        snprintf(msg, sizeof(msg), "%s: 원소 1개 보존", alg->name);
        check(one[0].key == 42, msg);

        for (k = 0; k < 64; k++) { same[k].key = 7; same[k].tag = (int)k; }
        sortStatsReset(&st);
        quickSortSeed(999ULL);
        alg->sort(same, 64, sizeof(Record), recordCompare, &st);
        ok = 1;
        for (k = 0; k < 64; k++) if (same[k].key != 7) ok = 0;
        snprintf(msg, sizeof(msg), "%s: 전부 같은 값 처리", alg->name);
        check(ok, msg);

        /* stats가 NULL이면 측정하지 않고 그냥 정렬만 해야 한다 */
        {
            Record small[16];
            for (k = 0; k < 16; k++) { small[k].key = (int)(16 - k); small[k].tag = (int)k; }
            quickSortSeed(999ULL);
            alg->sort(small, 16, sizeof(Record), recordCompare, NULL);
            snprintf(msg, sizeof(msg), "%s: stats=NULL 에서 안전", alg->name);
            check(ascending(small, 16), msg);
        }
    }
}

/* 3) 레지스트리의 stable 주장이 실측과 일치하는가.
 *
 * 반드시 중복이 많은 입력에서 재야 한다.
 * 중복이 거의 없으면 불안정한 정렬도 우연히 안정한 결과를 내서,
 * 성질이 아니라 운을 측정하게 된다. */
static void testStabilityClaim(void)
{
    const size_t n = 500;
    size_t a;

    for (a = 0; a < SORT_ALGORITHM_COUNT; a++) {
        const SortAlgorithm *alg = &SORT_ALGORITHMS[a];
        Record *arr = (Record *)malloc(sizeof(Record) * n);
        SortStats st;
        char msg[160];
        int measured;

        makeInput(arr, n, INPUT_FEW_UNIQUE, 777ULL);
        sortStatsReset(&st);
        quickSortSeed(999ULL);
        alg->sort(arr, n, sizeof(Record), recordCompare, &st);
        measured = stableResult(arr, n);

        snprintf(msg, sizeof(msg),
                 "%s: stable 주장(%d)과 실측(%d) 일치",
                 alg->name, alg->stable, measured);
        check(measured == alg->stable, msg);
        free(arr);
    }
}

/* 4) 계측기 자체가 동작하는가 */
static void testInstrumentation(void)
{
    const size_t n = 256;
    Record *arr = (Record *)malloc(sizeof(Record) * n);
    SortStats st;
    size_t a;

    for (a = 0; a < SORT_ALGORITHM_COUNT; a++) {
        const SortAlgorithm *alg = &SORT_ALGORITHMS[a];
        char msg[160];

        makeInput(arr, n, INPUT_RANDOM, 555ULL);
        sortStatsReset(&st);
        quickSortSeed(999ULL);
        alg->sort(arr, n, sizeof(Record), recordCompare, &st);

        snprintf(msg, sizeof(msg), "%s: 비교·이동 카운터가 올라감", alg->name);
        check(st.compares > 0 && st.moves > 0, msg);
    }

    /* 공간 주장과 실측 대조 */
    makeInput(arr, n, INPUT_RANDOM, 555ULL);
    sortStatsReset(&st);
    mergeSort(arr, n, sizeof(Record), recordCompare, &st);
    check(st.extraBytes == sizeof(Record) * (n + 1),
          "mergeSort: 추가 공간이 O(n) (버퍼 n칸 + 임시 1칸)");
    check(st.maxDepth > 1, "mergeSort: 재귀 깊이가 기록됨");

    makeInput(arr, n, INPUT_RANDOM, 555ULL);
    sortStatsReset(&st);
    heapSort(arr, n, sizeof(Record), recordCompare, &st);
    check(st.extraBytes == sizeof(Record),
          "heapSort: 추가 공간이 임시 1칸뿐 (O(1))");
    check(st.maxDepth == 1, "heapSort: 반복 구현이라 재귀 없음");

    free(arr);
}

/* 5) 안정성 판정기가 실제로 위반을 잡는가.
 * 검사기가 고장나 있으면 3)의 통과가 아무것도 증명하지 못한다. */
static void testStabilityDetector(void)
{
    Record good[4] = { {1, 0}, {1, 1}, {2, 2}, {2, 3} };
    Record bad[4]  = { {1, 1}, {1, 0}, {2, 2}, {2, 3} };

    check(stableResult(good, 4) == 1, "판정기: 보존된 순서를 안정으로 판정");
    check(stableResult(bad, 4) == 0, "판정기: 뒤집힌 순서를 불안정으로 판정");
}

int main(void)
{
    printf("정렬 단위 테스트\n\n");

    testCorrectness();
    testEdgeCases();
    testStabilityClaim();
    testInstrumentation();
    testStabilityDetector();

    printf("\n%d checks, %d failures\n", passed + failed, failed);
    return failed ? 1 : 0;
}
