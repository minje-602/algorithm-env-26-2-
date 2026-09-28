/* sortctx.h - 정렬 구현들끼리만 쓰는 작업 문맥과 도구.
 *
 * sort.h에 두면 main.c까지 정렬의 내장을 보게 되므로 따로 갈랐다.
 * 이 헤더는 정렬 구현 파일들과 sort.c 만 포함한다.
 */
#ifndef SORTCTX_H
#define SORTCTX_H

#include "sort.h"

/* 정렬 한 번이 처음부터 끝까지 들고 다니는 문맥.
 * 원소 타입을 모르므로 모든 조작이 바이트 단위다. */
typedef struct SortCtx {
    char       *base;   /* 배열의 첫 바이트 */
    size_t      size;   /* 원소 한 개의 바이트 수 */
    SortCompare cmp;
    SortStats  *stats;  /* NULL이면 측정하지 않는다 */
    char       *tmp;    /* 원소 한 칸. 교환이 거쳐 가는 자리 */
} SortCtx;

/* 실패하면 0을 돌려준다 (tmp 할당 실패). */
int   sortCtxInit(SortCtx *c, void *base, size_t size,
                  SortCompare cmp, SortStats *stats);
void  sortCtxFree(SortCtx *c);

void *sortElemAt(const SortCtx *c, size_t i);
int   sortCompareAt(const SortCtx *c, size_t i, size_t j);
int   sortCompareElem(const SortCtx *c, const void *a, const void *b);
void  sortSwap(const SortCtx *c, size_t i, size_t j);   /* 이동 3회 */
void  sortMove(const SortCtx *c, void *dst, const void *src);  /* 이동 1회 */
void  sortNoteDepth(const SortCtx *c, size_t depth);
void  sortNoteExtra(const SortCtx *c, size_t bytes);

#endif /* SORTCTX_H */
