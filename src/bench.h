/* bench.h - 입력 생성과 측정.
 *
 * 정렬 구현은 자기가 측정당하는 줄 모른다.
 * 시계는 여기서 들고, 정렬 인터페이스 바깥에 있다.
 */
#ifndef BENCH_H
#define BENCH_H

#include "sort.h"

/* 정렬 대상 원소.
 * key로 정렬하고 tag에는 입력에서의 순서를 새겨 둔다.
 * int 배열로는 3과 3을 구별할 수 없어 안정성을 볼 수 없다. */
typedef struct Record {
    int key;
    int tag;
} Record;

/* key만 본다. tag까지 넣으면 같은 값이 사라져 모든 정렬이 안정해 보인다. */
int recordCompare(const void *a, const void *b);

typedef enum InputShape {
    INPUT_RANDOM = 0,
    INPUT_SORTED,
    INPUT_REVERSE,
    INPUT_FEW_UNIQUE,
    INPUT_SHAPE_COUNT
} InputShape;

const char *inputShapeName(InputShape shape);

/* seed가 같으면 늘 같은 배열이 나온다 -> 세 정렬이 완전히 같은 입력을 본다. */
void makeInput(Record *a, size_t n, InputShape shape, unsigned long long seed);

typedef struct BenchResult {
    double    milliseconds;
    SortStats stats;
    int       sorted;   /* 결과가 오름차순인가 (정확성) */
    int       stable;   /* 1=안정, 0=불안정, -1=판정 불가(중복 없음) */
} BenchResult;

BenchResult benchRun(const SortAlgorithm *alg, size_t n, InputShape shape,
                     unsigned long long seed, int repeats);

#endif /* BENCH_H */
