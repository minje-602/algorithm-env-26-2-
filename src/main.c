/* main.c - 실험 수행.
 *
 * 측정은 한 번만 하고, 그 결과를 어디로 내보낼지(사람이 읽는 표 / CSV)만
 * 함수 포인터로 갈아끼운다. SortAlgorithm에서 정렬을 갈아끼운 것과 같은 수다.
 * 덕분에 차트 스크립트가 사람 읽는 표를 파싱하지 않아도 된다.
 *
 *   ./src/main.out          사람이 읽는 표
 *   ./src/main.out --csv    같은 측정을 CSV로
 */
#include <stdio.h>
#include <string.h>
#include "bench.h"

#define SEED 20260930ULL

static int csvMode = 0;

/* 한 행을 내보내는 방법. 표 또는 CSV. */
typedef void (*RowSink)(const char *experiment, const char *label,
                        const char *shape, size_t n, BenchResult r);

static void rowTable(const char *experiment, const char *label,
                     const char *shape, size_t n, BenchResult r)
{
    (void)experiment;
    printf("  %-11s %-11s %7zu %9.3f %12zu %12zu %7zu %9zu   %-3s %-3s\n",
           label, shape, n, r.milliseconds,
           r.stats.compares, r.stats.moves, r.stats.maxDepth, r.stats.extraBytes,
           r.sorted ? "OK" : "X",
           r.stable < 0 ? "-" : (r.stable ? "Y" : "N"));
}

static void rowCsv(const char *experiment, const char *label,
                   const char *shape, size_t n, BenchResult r)
{
    printf("%s,%s,%s,%zu,%.6f,%zu,%zu,%zu,%zu,%d,%d\n",
           experiment, label, shape, n, r.milliseconds,
           r.stats.compares, r.stats.moves, r.stats.maxDepth, r.stats.extraBytes,
           r.sorted, r.stable);
}

static void section(const char *title)
{
    if (csvMode) return;
    printf("\n%s\n\n", title);
    printf("  %-11s %-11s %7s %9s %12s %12s %7s %9s   %-3s %-3s\n",
           "algorithm", "shape", "n", "time(ms)", "compares", "moves",
           "depth", "extra(B)", "srt", "stb");
    printf("  ");
    { int i; for (i = 0; i < 100; i++) putchar('-'); }
    putchar('\n');
}

static void blank(void)
{
    if (!csvMode) putchar('\n');
}

static const SortAlgorithm *findAlgorithm(const char *name)
{
    size_t i;
    for (i = 0; i < SORT_ALGORITHM_COUNT; i++)
        if (strcmp(SORT_ALGORITHMS[i].name, name) == 0)
            return &SORT_ALGORITHMS[i];
    return NULL;
}

/* 실험 1: 입력 모양이 바뀌면 누가 흔들리는가 */
static void experimentShapes(size_t n, int repeats, RowSink sink)
{
    int shape;
    size_t i;

    section("[1] 입력 모양별 비교");
    for (shape = 0; shape < INPUT_SHAPE_COUNT; shape++) {
        for (i = 0; i < SORT_ALGORITHM_COUNT; i++) {
            BenchResult r = benchRun(&SORT_ALGORITHMS[i], n,
                                     (InputShape)shape, SEED, repeats);
            sink("shapes", SORT_ALGORITHMS[i].name,
                 inputShapeName((InputShape)shape), n, r);
        }
        blank();
    }
}

/* 실험 2: n을 키우면 어떤 비율로 자라는가 */
static void experimentGrowth(int repeats, RowSink sink)
{
    static const size_t sizes[] = { 1000, 2000, 4000, 8000, 16000, 32000 };
    const size_t count = sizeof(sizes) / sizeof(sizes[0]);
    size_t i, s;

    section("[2] 입력 크기에 따른 변화 (random)");
    for (i = 0; i < SORT_ALGORITHM_COUNT; i++) {
        for (s = 0; s < count; s++) {
            BenchResult r = benchRun(&SORT_ALGORITHMS[i], sizes[s],
                                     INPUT_RANDOM, SEED, repeats);
            sink("growth", SORT_ALGORITHMS[i].name, "random", sizes[s], r);
        }
        blank();
    }
}

/* 실험 3: 피벗 전략이 최악의 경우를 없애는가 (Topic 04) */
static void experimentPivot(size_t n, int repeats, RowSink sink)
{
    static const struct { QuickPivot mode; const char *label; } modes[] = {
        { QUICK_PIVOT_LAST,    "quick:last" },
        { QUICK_PIVOT_MEDIAN3, "quick:med3" },
        { QUICK_PIVOT_RANDOM,  "quick:rand" }
    };
    const size_t count = sizeof(modes) / sizeof(modes[0]);
    const SortAlgorithm *quick = findAlgorithm("quickSort");
    QuickPivot saved = quickSortPivot;
    size_t i;

    if (quick == NULL) return;

    section("[3] 피벗 전략 비교 (정렬된 입력 = 퀵 정렬의 최악)");
    for (i = 0; i < count; i++) {
        BenchResult r;
        quickSortPivot = modes[i].mode;
        r = benchRun(quick, n, INPUT_SORTED, SEED, repeats);
        sink("pivot", modes[i].label, "sorted", n, r);
    }
    quickSortPivot = saved;   /* 실험이 전역 상태를 남기지 않게 되돌린다 */
    blank();
}

int main(int argc, char **argv)
{
    const size_t n = 8000;
    const size_t pivotN = 4000;
    const int repeats = 5;
    RowSink sink;

    if (argc > 1 && strcmp(argv[1], "--csv") == 0) csvMode = 1;
    sink = csvMode ? rowCsv : rowTable;

    if (csvMode) {
        printf("experiment,algorithm,shape,n,ms,compares,moves,depth,"
               "extra_bytes,sorted,stable\n");
    } else {
        printf("정렬 비교: 퀵 / 병합 / 힙\n");
        printf("seed = %llu, 반복 %d회 중 최솟값\n", SEED, repeats);
    }

    experimentShapes(n, repeats, sink);
    experimentGrowth(repeats, sink);
    experimentPivot(pivotN, repeats, sink);

    return 0;
}
