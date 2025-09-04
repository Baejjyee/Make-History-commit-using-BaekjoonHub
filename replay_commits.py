import os, re, subprocess, sys
import unicodedata
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(".").resolve()
TARGET_ROOTS = ["백준"]  # 필요시 추가: ["백준","SWEA","프로그래머스"]

EXCLUDE_NAMES = {"replay_commits.py", ".gitignore"}
EXCLUDE_DIRS  = {".git", ".idea", ".venv", "__pycache__"}

LABEL_PATTERNS = (
    "제출 일자", "제출일자", "제출  일자", "제출 날짜", "제출날짜", "제출  날짜",
    "제출　일자", "제출　날짜"  # 전각 공백 대응
)

DATE_RE = re.compile(
    r"\s*(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*(\d{1,2})\s*:\s*(\d{2})\s*:\s*(\d{2})\s*"
)

def git(*args, check=True, env=None):
    return subprocess.run(["git", *args], check=check, env=env)

def find_readmes():
    files = []
    for base in TARGET_ROOTS:
        basep = ROOT / base
        if not basep.exists():
            continue
        files.extend(basep.rglob("README.md"))
    return files

def parse_date_from_lines(lines, start_idx):
    """
    라벨이 있는 줄 인덱스(start_idx) 기준:
      1) 같은 줄에 날짜가 붙어있으면 그걸 파싱
      2) 아래로 내려가며 빈 줄 스킵 후 첫 비어있지 않은 줄에서 날짜 파싱
    """
    # 1) 같은 줄에 날짜가 붙어있는 경우: "제출 일자: 2025년 ..."
    same_line = lines[start_idx]
    m = DATE_RE.search(same_line)
    if m:
        y, mo, d, h, mi, s = map(int, m.groups())
        return y, mo, d, h, mi, s

    # 2) 다음 줄들에서 찾기 (여러 개의 빈 줄 허용)
    j = start_idx + 1
    n = len(lines)
    while j < n and not lines[j].strip():
        j += 1
    if j < n:
        m2 = DATE_RE.search(lines[j].strip())
        if m2:
            y, mo, d, h, mi, s = map(int, m2.groups())
            return y, mo, d, h, mi, s
    return None

def parse_readme(p: Path):
    text = p.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    # 제목(H1) 추출: 앞 공백/샾 허용
    title = None
    for line in lines:
        if line.lstrip().startswith("# "):
            title = line.lstrip()[2:].strip()
            break
    if not title:
        title = p.parent.name

    # 라벨 줄 찾기(느슨하게)
    label_idx = None
    for i, line in enumerate(lines):
        norm = line.strip().lstrip("#").strip()  # "### 제출 일자" 같은 케이스 대비
        if any(lbl in norm for lbl in LABEL_PATTERNS):
            label_idx = i
            break
    if label_idx is None:
        # print(f"[PARSE FAIL: no label] {p}")
        return None

    got = parse_date_from_lines(lines, label_idx)
    if not got:
        # print(f"[PARSE FAIL: no date] {p}")
        return None

    y, mo, d, h, mi, s = got
    tz = timezone(timedelta(hours=9))
    dt = datetime(y, mo, d, h, mi, s, tzinfo=tz)
    return {"readme": p, "title": title, "dt": dt}

import unicodedata

def stage_folder(folder: Path):
    # 1) 폴더 절대경로를 NFC 정규화
    folder_abs = unicodedata.normalize("NFC", str(folder.resolve()))
    # 2) 저장소 루트 기준 상대 경로(POSIX)
    rel = folder.relative_to(ROOT).as_posix()

    # 3) 해당 폴더로 들어가서 현재 폴더(.) 강제 add
    subprocess.run(["git", "add", "-f", "--", "."], check=True, cwd=folder_abs)

    # 4) "그 폴더 하위에" 스테이징이 생겼는지, pathspec 한정으로 검사
    #    git diff --cached --quiet -- <pathspec>
    #    returncode == 1 이면 변화(=스테이징 있음)
    res = subprocess.run(["git", "diff", "--cached", "--quiet", "--", rel])
    has = (res.returncode == 1)

    print(f"[DEBUG] has_staged({rel}) = {has}")
    return has

def has_staged_changes():
    # 0: 없음, 1: 있음
    res = subprocess.run(["git", "diff", "--cached", "--quiet"])
    return res.returncode == 1

def main():
    readmes = find_readmes()
    entries = []
    for readme in readmes:
        meta = parse_readme(readme)
        if meta:
            entries.append(meta)

    entries.sort(key=lambda x: x["dt"])
    total = len(entries)

    for i, e in enumerate(entries, 1):
        folder = e["readme"].parent
        if not stage_folder(folder):
            print(f"[{i}/{total}] {folder} 스테이징할 파일 없음 → 스킵")
            continue

        # (여기선 전체 인덱스 기준으로도 한 번 더 확인)
        res2 = subprocess.run(
            ["git", "diff", "--cached", "--quiet", "--", folder.relative_to(ROOT).as_posix()]
        )
        has2 = (res2.returncode == 1)
        if not has2:
            git("reset")
            print(f"[{i}/{total}] {folder} 변경 없음 → 스킵")
            continue

        iso = e["dt"].strftime("%Y-%m-%d %H:%M:%S %z")
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = iso
        env["GIT_COMMITTER_DATE"] = iso
        git("commit", "-m", e["title"], env=env)
        print(f"[{i}/{total}] committed {folder} at {iso}")

if __name__ == "__main__":
    main()
