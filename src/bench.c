#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "bench.h"

int recordCompare(const void *a, const void *b)
{
    int x = ((const Record *)a)->key;
    int y = ((const Record *)b)->key;
    return (x > y) - (x < y);   /* 뺄셈은 오버플로우 위험이 있다 */
}

const char *inputShapeName(InputShape shape)
{
    switch (shape) {
    case INPUT_RANDOM:     return "random";
    case INPUT_SORTED:     return "sorted";
    case INPUT_REVERSE:    return "reverse";
    case INPUT_FEW_UNIQUE: return "few_unique";
    default:               return "?";
    }
}

/* 입력 생성기도 고정 시드 난수를 쓴다.
 * 실행할 때마다 배열이 달라지면 비교·이동 횟수가 흔들려 재현이 안 된다. */
static unsigned long long inputState;

static unsigned long long inputRandom(void)
{
    inputState ^= inputState << 13;
    inputState ^= inputState >> 7;
    inputState ^= inputState << 17;
    return inputState;
}

void makeInput(Record *a, size_t n, InputShape shape, unsigned long long seed)
{
    size_t i;

    inputState = (seed != 0) ? seed : 0x9E3779B97F4A7C15ULL;

    for (i = 0; i < n; i++) {
        switch (shape) {
        case INPUT_SORTED:
            a[i].key = (int)i;
            break;
        case INPUT_REVERSE:
            a[i].key = (int)(n - i);
            break;
        /* 값의 가짓수를 8개로 묶어 중복을 대량으로 만든다.
         * 안정성 차이가 드러나는 것도, 퀵 정렬이 중복에 약한 것도 여기서 보인다. */
        case INPUT_FEW_UNIQUE:
            a[i].key = (int)(inputRandom() % 8);
            break;
        case INPUT_RANDOM:
        default:
            a[i].key = (int)(inputRandom() % 1000000);
            break;
        }
        a[i].tag = (int)i;   /* 입력 순서를 새겨 둔다 -> 안정성 판정의 근거 */
    }
}

static int isSorted(const Record *a, size_t n)
{
    size_t i;
    for (i = 1; i < n; i++)
        if (a[i - 1].key > a[i].key) return 0;
    return 1;
}

/* 정렬이 끝나면 같은 값이 인접하므로, 결과 배열만 훑어도 중복 유무를 알 수 있다. */
static int hasDuplicates(const Record *a, size_t n)
{
    size_t i;
    for (i = 1; i < n; i++)
        if (a[i - 1].key == a[i].key) return 1;
    return 0;
}

static int isStable(const Record *a, size_t n)
{
    size_t i;
    for (i = 1; i < n; i++)
        if (a[i - 1].key == a[i].key && a[i - 1].tag > a[i].tag) return 0;
    return 1;
}

BenchResult benchRun(const SortAlgorithm *alg, size_t n, InputShape shape,
                     unsigned long long seed, int repeats)
{
    BenchResult r;
    Record *origin, *work;
    double best = 0.0;
    int k;

    memset(&r, 0, sizeof(r));

    origin = (Record *)malloc(sizeof(Record) * (n ? n : 1));
    work   = (Record *)malloc(sizeof(Record) * (n ? n : 1));
    if (origin == NULL || work == NULL) { free(origin); free(work); return r; }

    makeInput(origin, n, shape, seed);

    for (k = 0; k < repeats; k++) {
        clock_t t0, t1;
        double ms;

        memcpy(work, origin, sizeof(Record) * n);   /* 복사는 측정 구간 밖 */
        sortStatsReset(&r.stats);
        quickSortSeed(seed);   /* 무작위 피벗도 매 반복 같은 수열을 쓰게 한다 */

        t0 = clock();
        alg->sort(work, n, sizeof(Record), recordCompare, &r.stats);
        t1 = clock();

        /* 최솟값을 쓴다. 방해는 시간을 늘리기만 하므로,
         * 가장 빠른 실행이 알고리즘 고유 비용에 가장 가깝다. */
        ms = (double)(t1 - t0) * 1000.0 / CLOCKS_PER_SEC;
        if (k == 0 || ms < best) best = ms;
    }

    r.milliseconds = best;
    r.sorted = isSorted(work, n);
    /* 중복이 없으면 안정성 검사가 무조건 통과한다.
     * 통과를 "안정적"이라 읽으면 거짓이 되므로 판정 불가로 구분한다. */
    r.stable = hasDuplicates(work, n) ? isStable(work, n) : -1;

    free(origin);
    free(work);
    return r;
}
