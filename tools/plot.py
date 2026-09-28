"""plot.py - report/results.csv 를 읽어 SVG 그래프를 그린다.

외부 라이브러리를 쓰지 않는다 (컨테이너에 matplotlib 이 없다).
표준 모듈만으로 SVG 를 직접 찍는다.

같은 자료를 선형 축과 로그 축으로 각각 그린다. 하나로는 절반씩 놓치기 때문이다.
  선형 - 격차의 크기를 보여주고, 작은 값을 바닥에 묻는다
  로그 - 작은 값과 증가율을 보여주고, 격차의 크기를 눌러 감춘다

로그 축에서는 막대 대신 점을 쓴다. 막대는 길이가 값을 뜻하는데
로그 축에서는 길이의 비가 값의 비와 달라져 눈을 속이기 때문이다.
점은 위치만으로 값을 나타내므로 로그 축에서도 정직하다.

차트 안의 글자는 모두 ASCII 로 둔다 - PDF 변환 시 한글 글꼴 문제를 피하기 위해서다.
"""
import csv
import math
import os

DATA = os.path.join("report", "results.csv")
OUT = "report"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SOFT = "#52514e"
GRID = "#e6e5e1"

# dataviz 기본 팔레트의 앞 세 칸. 색각 이상 조건에서도 서로 구별된다.
SERIES = {
    "quickSort": "#2a78d6",
    "mergeSort": "#eb6834",
    "heapSort":  "#1baf7a",
    "quick:last": "#2a78d6",
    "quick:med3": "#2a78d6",
    "quick:rand": "#2a78d6",
}
ALGS = ["quickSort", "mergeSort", "heapSort"]
SHAPES = ["random", "sorted", "reverse", "few_unique"]

W, H = 780, 420
MARGIN = {"l": 74, "r": 26, "t": 80, "b": 64}
PW = W - MARGIN["l"] - MARGIN["r"]
PH = H - MARGIN["t"] - MARGIN["b"]


def load():
    with open(DATA, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["n"] = int(r["n"])
        r["ms"] = float(r["ms"])
        for k in ("compares", "moves", "depth", "extra_bytes"):
            r[k] = int(r[k])
    return rows


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt(v):
    """자릿수에 따라 유효숫자를 남긴다.

    7,998,000 을 "8M" 으로 뭉개면 그 값이 n(n-1)/2 와 정확히 같다는 사실이
    사라진다. 이 보고서에서는 그 일치가 결론의 근거이므로 자릿수를 지킨다.
    """
    if v >= 1e7:
        return "%.1fM" % (v / 1e6)
    if v >= 1e6:
        return "%.3fM" % (v / 1e6)
    if v >= 1e4:
        return "%.0fK" % (v / 1000)
    if v >= 1000:
        return "{:,}".format(int(round(v)))
    if v >= 100:
        return "%.0f" % v
    if v >= 1:
        return "%.1f" % v
    if v > 0:
        return "%.2f" % v
    return "0"


def nice_ticks(vmax, count=5):
    if vmax <= 0:
        return [0, 1]
    raw = vmax / float(count)
    mag = 10 ** math.floor(math.log10(raw))
    step = mag * 10
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            step = m * mag
            break
    return [i * step for i in range(int(math.ceil(vmax / step)) + 1)]


def log_ticks(vmin, vmax):
    lo = int(math.floor(math.log10(vmin)))
    hi = int(math.ceil(math.log10(vmax)))
    return [10 ** e for e in range(lo, hi + 1)]


def head(title, subtitle):
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" font-family="Helvetica,Arial,sans-serif">' % (W, H, W, H),
        '<rect width="%d" height="%d" fill="%s"/>' % (W, H, SURFACE),
        '<text x="%d" y="30" font-size="16" font-weight="600" fill="%s">%s</text>'
        % (MARGIN["l"], INK, esc(title)),
        '<text x="%d" y="50" font-size="11.5" fill="%s">%s</text>'
        % (MARGIN["l"], INK_SOFT, esc(subtitle)),
    ]


def legend(series):
    """계열이 둘 이상이면 범례는 늘 있어야 한다 - 색만으로 구분되지 않게."""
    out = []
    x = MARGIN["l"]
    for name in series:
        out.append('<rect x="%.1f" y="60" width="10" height="10" rx="2" fill="%s"/>'
                   % (x, SERIES[name]))
        out.append('<text x="%.1f" y="69" font-size="11" fill="%s">%s</text>'
                   % (x + 15, INK_SOFT, esc(name)))
        x += 24 + len(name) * 6.4
    return out


def axis_frame(ticks, ypos, unit, logscale=False):
    out = []
    for t in ticks:
        y = ypos(t)
        if y < MARGIN["t"] - 2 or y > MARGIN["t"] + PH + 2:
            continue
        out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1"/>'
                   % (MARGIN["l"], y, MARGIN["l"] + PW, y, GRID))
        out.append('<text x="%d" y="%.1f" font-size="10" fill="%s" text-anchor="end">%s</text>'
                   % (MARGIN["l"] - 8, y + 3.5, INK_SOFT, fmt(t)))
    out.append('<text x="%d" y="%d" font-size="10" fill="%s">%s</text>'
               % (MARGIN["l"] - 62, MARGIN["t"] - 12, INK_SOFT, esc(unit)))
    out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1"/>'
               % (MARGIN["l"], MARGIN["t"] + PH, MARGIN["l"] + PW,
                  MARGIN["t"] + PH, INK_SOFT))
    return out


def bar_path(x, y, w, h, r=4):
    """데이터 끝(위)만 둥글게. 아래는 기준선에 붙어야 길이가 값을 정직하게 나타낸다."""
    if h <= 0.5:
        return '<rect x="%.1f" y="%.1f" width="%.1f" height="1" />' % (x, y + h - 1, w)
    r = min(r, w / 2.0, h)
    return ('<path d="M%.1f,%.1f L%.1f,%.1f Q%.1f,%.1f %.1f,%.1f '
            'L%.1f,%.1f Q%.1f,%.1f %.1f,%.1f L%.1f,%.1f Z"'
            % (x, y + h, x, y + r, x, y, x + r, y,
               x + w - r, y, x + w, y, x + w, y + r, x + w, y + h))


def grouped_bar(path, title, subtitle, groups, series, value_of, unit, glabel=None):
    vals = [value_of(g, s) for g in groups for s in series]
    ticks = nice_ticks(max(vals) or 1)
    top = ticks[-1]

    def ypos(v):
        return MARGIN["t"] + PH - (v / top) * PH

    s = head(title, subtitle)
    if len(series) > 1:
        s += legend(series)
    s += axis_frame(ticks, ypos, unit)

    gw = PW / float(len(groups))
    bw = min(44.0, (gw - 26) / len(series))
    for gi, g in enumerate(groups):
        gx = MARGIN["l"] + gi * gw
        base = gx + (gw - (bw * len(series) + 2 * (len(series) - 1))) / 2.0
        for si, name in enumerate(series):
            v = value_of(g, name)
            x = base + si * (bw + 2)          # 막대 사이 2px 간격
            y = ypos(v)
            s.append(bar_path(x, y, bw, MARGIN["t"] + PH - y)
                     + ' fill="%s"/>' % SERIES[name])
            s.append('<text x="%.1f" y="%.1f" font-size="9.5" fill="%s" text-anchor="middle">%s</text>'
                     % (x + bw / 2, y - 5, INK_SOFT, fmt(v)))
        s.append('<text x="%.1f" y="%d" font-size="11.5" fill="%s" text-anchor="middle">%s</text>'
                 % (gx + gw / 2, MARGIN["t"] + PH + 20, INK,
                    esc(glabel(g) if glabel else g)))
    s.append('</svg>')
    open(path, "w").write("\n".join(s))


def grouped_dot(path, title, subtitle, groups, series, value_of, unit, glabel=None):
    """로그 축 버전. 막대 대신 점 - 로그에서 길이는 값의 비를 왜곡하지만
    점의 위치는 왜곡하지 않는다."""
    vals = [value_of(g, s) for g in groups for s in series if value_of(g, s) > 0]
    vmin, vmax = min(vals), max(vals)
    ticks = log_ticks(vmin, vmax)
    lo, hi = math.log10(ticks[0]), math.log10(ticks[-1])

    def ypos(v):
        v = max(v, ticks[0])
        return MARGIN["t"] + PH - (math.log10(v) - lo) / (hi - lo) * PH

    s = head(title, subtitle)
    if len(series) > 1:
        s += legend(series)
    s += axis_frame(ticks, ypos, unit)

    gw = PW / float(len(groups))
    for gi, g in enumerate(groups):
        gx = MARGIN["l"] + gi * gw
        span = min(120.0, gw - 40)
        for si, name in enumerate(series):
            v = value_of(g, name)
            x = gx + gw / 2 - span / 2 + (span / max(1, len(series) - 1)) * si \
                if len(series) > 1 else gx + gw / 2
            if v <= 0:
                s.append('<text x="%.1f" y="%.1f" font-size="9" fill="%s" '
                         'text-anchor="middle">0</text>'
                         % (x, MARGIN["t"] + PH - 4, INK_SOFT))
                continue
            y = ypos(v)
            s.append('<circle cx="%.1f" cy="%.1f" r="5" fill="%s" stroke="%s" stroke-width="2"/>'
                     % (x, y, SERIES[name], SURFACE))
            s.append('<text x="%.1f" y="%.1f" font-size="9.5" fill="%s" text-anchor="middle">%s</text>'
                     % (x, y - 10, INK_SOFT, fmt(v)))
        s.append('<text x="%.1f" y="%d" font-size="11.5" fill="%s" text-anchor="middle">%s</text>'
                 % (gx + gw / 2, MARGIN["t"] + PH + 20, INK,
                    esc(glabel(g) if glabel else g)))
    s.append('</svg>')
    open(path, "w").write("\n".join(s))


def line_chart(path, title, subtitle, xs, series, value_of, unit, logy=False):
    right = 96
    pw = W - MARGIN["l"] - right
    vals = [value_of(x, s) for x in xs for s in series]
    if logy:
        ticks = log_ticks(min(v for v in vals if v > 0), max(vals))
        lo, hi = math.log10(ticks[0]), math.log10(ticks[-1])

        def ypos(v):
            return MARGIN["t"] + PH - (math.log10(max(v, ticks[0])) - lo) / (hi - lo) * PH
    else:
        ticks = nice_ticks(max(vals) or 1)
        top = ticks[-1]

        def ypos(v):
            return MARGIN["t"] + PH - (v / top) * PH

    s = head(title, subtitle)
    s += legend(series)
    for t in ticks:
        y = ypos(t)
        if y < MARGIN["t"] - 2 or y > MARGIN["t"] + PH + 2:
            continue
        s.append('<line x1="%d" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1"/>'
                 % (MARGIN["l"], y, MARGIN["l"] + pw, y, GRID))
        s.append('<text x="%d" y="%.1f" font-size="10" fill="%s" text-anchor="end">%s</text>'
                 % (MARGIN["l"] - 8, y + 3.5, INK_SOFT, fmt(t)))
    s.append('<text x="%d" y="%d" font-size="10" fill="%s">%s</text>'
             % (MARGIN["l"] - 66, MARGIN["t"] - 12, INK_SOFT, esc(unit)))
    s.append('<line x1="%d" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="1"/>'
             % (MARGIN["l"], MARGIN["t"] + PH, MARGIN["l"] + pw,
                MARGIN["t"] + PH, INK_SOFT))

    def xpos(i):
        return MARGIN["l"] + (i / float(max(1, len(xs) - 1))) * pw

    for i, x in enumerate(xs):
        s.append('<text x="%.1f" y="%d" font-size="10.5" fill="%s" text-anchor="middle">%s</text>'
                 % (xpos(i), MARGIN["t"] + PH + 20, INK, "{:,}".format(x)))
    s.append('<text x="%.1f" y="%d" font-size="11" fill="%s" text-anchor="middle">'
             'input size n (doubling)</text>'
             % (MARGIN["l"] + pw / 2, MARGIN["t"] + PH + 42, INK_SOFT))

    for name in series:
        pts = [(xpos(i), ypos(value_of(x, name))) for i, x in enumerate(xs)]
        d = " ".join(("M" if i == 0 else "L") + "%.1f,%.1f" % p for i, p in enumerate(pts))
        s.append('<path d="%s" fill="none" stroke="%s" stroke-width="2" '
                 'stroke-linejoin="round" stroke-linecap="round"/>' % (d, SERIES[name]))
        for px, py in pts:
            s.append('<circle cx="%.1f" cy="%.1f" r="4.5" fill="%s" stroke="%s" stroke-width="2"/>'
                     % (px, py, SERIES[name], SURFACE))
        ex, ey = pts[-1]
        s.append('<text x="%.1f" y="%.1f" font-size="10.5" fill="%s">%s</text>'
                 % (ex + 9, ey + 4, INK_SOFT, esc(name)))
    s.append('</svg>')
    open(path, "w").write("\n".join(s))


def main():
    rows = load()
    shapes = {(r["algorithm"], r["shape"]): r for r in rows if r["experiment"] == "shapes"}
    growth = {(r["algorithm"], r["n"]): r for r in rows if r["experiment"] == "growth"}
    pivot = {r["algorithm"]: r for r in rows if r["experiment"] == "pivot"}
    ns = sorted({r["n"] for r in rows if r["experiment"] == "growth"})
    n0 = rows[0]["n"]

    sub = "n = %s, best of repeated runs" % "{:,}".format(n0)

    for metric, unit, label in (("ms", "time (ms)", "time"),
                                ("compares", "comparisons", "compares"),
                                ("moves", "moves", "moves")):
        grouped_bar("%s/shapes-%s.svg" % (OUT, label),
                    "Input shape vs %s" % unit, sub + " - linear axis",
                    SHAPES, ALGS, lambda g, a, m=metric: shapes[(a, g)][m], unit)
        grouped_dot("%s/shapes-%s-log.svg" % (OUT, label),
                    "Input shape vs %s" % unit, sub + " - log axis (dots: position encodes value)",
                    SHAPES, ALGS, lambda g, a, m=metric: shapes[(a, g)][m], unit)

    grouped_dot("%s/shapes-depth.svg" % OUT,
                "Input shape vs recursion depth",
                sub + " - log axis; heapSort is iterative so depth stays 1",
                SHAPES, ALGS, lambda g, a: shapes[(a, g)]["depth"], "max depth")

    line_chart("%s/growth-compares.svg" % OUT,
               "Comparisons as n grows", "random input - linear axis",
               ns, ALGS, lambda x, a: growth[(a, x)]["compares"], "comparisons")
    line_chart("%s/growth-compares-log.svg" % OUT,
               "Comparisons as n grows",
               "random input - log axis; parallel lines = same growth rate, different constant",
               ns, ALGS, lambda x, a: growth[(a, x)]["compares"], "comparisons", logy=True)
    line_chart("%s/growth-time.svg" % OUT,
               "Running time as n grows", "random input - linear axis",
               ns, ALGS, lambda x, a: growth[(a, x)]["ms"], "time (ms)")

    order = ["quick:last", "quick:med3", "quick:rand"]
    ratio = pivot["quick:last"]["compares"] / float(pivot["quick:med3"]["compares"])
    grouped_bar("%s/pivot-compares.svg" % OUT,
                "Pivot strategy on sorted input (quickSort worst case)",
                "n = %s - last-element pivot costs %.0fx more comparisons than median-of-3"
                % ("{:,}".format(pivot["quick:last"]["n"]), ratio),
                order, ["quick:med3"],
                lambda g, a: pivot[g]["compares"], "comparisons")

    print("charts written:", ", ".join(sorted(
        f for f in os.listdir(OUT) if f.endswith(".svg"))))


if __name__ == "__main__":
    main()
