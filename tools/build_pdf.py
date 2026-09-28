"""report/REPORT.md -> report/REPORT.pdf

pandoc으로 HTML 조각을 만들고, 자체 CSS로 감싼 뒤 헤드리스 크로미움으로 인쇄한다.
pandoc의 기본 standalone 템플릿을 쓰지 않는 이유는 그 제목 스타일이 한글 글꼴을
덮어써서 제목만 두부(tofu)로 깨지기 때문이다.

전제 조건 - 이 강의 컨테이너에는 아래가 없으므로 컨테이너 밖에서 실행해야 한다.
  - pandoc
  - 헤드리스 크로미움 (경로는 아래 상수를 환경에 맞게 고칠 것)
  - 한글 글꼴 (Noto Sans CJK KR). 없으면 본문이 전부 두부로 깨진다.

이 보고서의 PDF도 컨테이너 밖에서 위 도구로 생성했다.
측정 자체는 모두 컨테이너 안에서 수행했으므로 실험 결과에는 영향이 없다.

저장소 루트에서 실행한다:  python3 tools/build_pdf.py
"""
import subprocess, sys, pathlib

CSS = """
@page { size: A4; margin: 14mm 13mm 13mm 13mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Noto Sans CJK KR", sans-serif; font-size: 8.9pt;
       line-height: 1.46; color: #16150f; margin: 0; }
h1 { font-family: "Noto Sans CJK KR", sans-serif;
     font-size: 15pt; margin: 0 0 3pt; letter-spacing: -0.2pt; }
h2 { font-size: 11.6pt; margin: 13pt 0 5pt; padding-top: 4pt;
     border-top: 1.4px solid #16150f; break-after: avoid; }
h3 { font-size: 10pt; margin: 10pt 0 4pt; break-after: avoid; }
h4 { font-size: 9.2pt; margin: 8pt 0 3pt; color: #3a382e; break-after: avoid; }
p { margin: 0 0 5pt; }
ul { margin: 0 0 6pt; padding-left: 14pt; }
li { margin-bottom: 2pt; }
hr { border: none; border-top: 1px solid #d8d6cc; margin: 9pt 0; }
a { color: #1f5fa8; text-decoration: none; }
table { border-collapse: collapse; width: 100%; margin: 5pt 0 8pt;
        font-size: 7.7pt; break-inside: avoid; }
th, td { border: 1px solid #ccc9bd; padding: 2pt 4pt; text-align: left; }
th { background: #f2f1ec; font-weight: 600; }
td[align="right"], th[align="right"] { text-align: right; }
td[align="center"], th[align="center"] { text-align: center; }
code { font-family: "DejaVu Sans Mono", "Noto Sans Mono CJK KR", monospace;
       font-size: 7.8pt; background: #f2f1ec; padding: 0.4pt 2pt; border-radius: 2px; }
pre { background: #f7f6f2; border: 1px solid #e2e0d6; border-radius: 3px;
      padding: 4.5pt 6pt; margin: 4pt 0 7pt; break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 7.1pt; line-height: 1.34; }
blockquote { margin: 6pt 0; padding: 5pt 8pt; background: #f7f6f2;
             border-left: 2.5px solid #b9b6a8; font-size: 8.3pt; break-inside: avoid; }
blockquote p:last-child { margin-bottom: 0; }
img { display: block; width: 133mm; max-width: 100%; height: auto;
      margin: 4pt auto 7pt; break-inside: avoid; }
strong { font-weight: 600; }
"""

HTML = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<title>%s</title><style>%s</style></head><body>
%s
</body></html>"""


def main():
    src = pathlib.Path("report/REPORT.md")
    frag = subprocess.run(
        ["pandoc", str(src), "-f", "gfm", "-t", "html5", "--embed-resources"],
        capture_output=True, text=True, check=True).stdout
    html = HTML % ("정렬 비교 보고서", CSS, frag)
    pathlib.Path("report/.report.html").write_text(html, encoding="utf-8")

    subprocess.run([
        "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
        "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
        "--print-to-pdf=report/REPORT.pdf", "file://" + str(pathlib.Path("report/.report.html").resolve()),
    ], capture_output=True, check=True)

    from pypdf import PdfReader
    print("페이지 수:", len(PdfReader("report/REPORT.pdf").pages))


if __name__ == "__main__":
    main()
