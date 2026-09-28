"""crosscheck.py - C 구현과 Python 구현의 카운터를 대조한다.

알고리즘이 하는 일의 양(비교·이동 횟수, 재귀 깊이)은 언어와 무관해야 한다.
두 구현의 이 값이 어긋나면, 둘 중 하나가 다른 알고리즘을 돌리고 있다는 뜻이다.

시간과 메모리는 언어에 종속되므로 대조하지 않고 참고로만 보여준다.
표준 모듈만 쓴다.

    python3 tools/crosscheck.py
"""
import csv
import io
import subprocess
import sys

COMPARED = ["compares", "moves", "depth"]   # 언어와 무관해야 하는 값들


def run_csv(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write("실행 실패: %s\n%s\n" % (" ".join(cmd), proc.stderr))
        sys.exit(1)
    return list(csv.DictReader(io.StringIO(proc.stdout)))


def row_key(row):
    return (row["experiment"], row["algorithm"], row["shape"], int(row["n"]))


def main():
    c_rows = run_csv(["./src/main.out", "--csv"])
    py_rows = run_csv([sys.executable, "src/main.py", "--csv"])

    c_map = {row_key(r): r for r in c_rows}
    py_map = {row_key(r): r for r in py_rows}

    only_c = sorted(set(c_map) - set(py_map))
    only_py = sorted(set(py_map) - set(c_map))
    common = sorted(set(c_map) & set(py_map))

    mismatches = []
    for k in common:
        for field in COMPARED:
            if c_map[k][field] != py_map[k][field]:
                mismatches.append((k, field, c_map[k][field], py_map[k][field]))

    print("C · Python 카운터 대조")
    print("  대조 가능한 행: %d" % len(common))
    if only_c:
        print("  C에만 있는 행: %d" % len(only_c))
    if only_py:
        print("  Python에만 있는 행: %d" % len(only_py))
    print()

    if mismatches:
        print("  불일치 %d건:" % len(mismatches))
        for (exp, alg, shape, n), field, cv, pv in mismatches:
            print("    %s/%s/%s n=%d  %s: C=%s Python=%s"
                  % (exp, alg, shape, n, field, cv, pv))
    else:
        print("  비교·이동·깊이가 %d개 행에서 모두 일치" % len(common))

    # 참고: 언어 종속 지표. 대조 대상이 아니다.
    print("\n  참고 - 실행 시간 비 (Python / C), shapes 실험")
    for k in common:
        if k[0] != "shapes":
            continue
        cms = float(c_map[k]["ms"])
        pms = float(py_map[k]["ms"])
        ratio = (pms / cms) if cms > 0 else float("inf")
        print("    %-10s %-11s  C %8.3f ms   Python %9.3f ms   x%6.1f"
              % (k[1], k[2], cms, pms, ratio))

    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
