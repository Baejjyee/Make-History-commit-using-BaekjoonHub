# Make-History-commit-using-BaekjoonHub

백준허브(또는 유사 툴)로 내려받은 **README.md의 제출 일자**를 파싱해, 실제 제출 시점으로 **커밋 타임스탬프를 재생**합니다.  
GitHub에서 “문제 푼 날짜대로 히스토리”를 확인할 수 있게 해줍니다.
zip파일로 백준허브에 올라간 모든 문제를 자동으로 올릴 수 있습니다.
해당 파일은 https://gameplace.tistory.com/57 블로그를 참조하여, 수정한것입니다.
해당 코드를 실행하면 원작자의 블로그를 확인할 수 있습니다.
replay_commits.py는 이 zip파일로 생성된 파일이나, 기존 백준허브를 이용하여 과거에 푼 문제지만 당일로 커밋이 되어 발생하는 스트릭을 채우기 위해 개발되었습니다.
---

## ✨ 기능
- 각 문제 폴더의 `README.md`에서 **제출 일자** 파싱
- 제출 시간 오름차순으로 커밋 생성  
  (환경변수 `GIT_AUTHOR_DATE`, `GIT_COMMITTER_DATE` 반영)
- 파일 내용은 그대로 두고, **Git 히스토리만** 과거로 복원
- 다중 루트 확장 가능: `TARGET_ROOTS = ["백준", "SWEA", "프로그래머스"]`

---

## ⚙️ 요구사항
- Python 3.9+
- Git 2.30+
- OS: Windows / macOS / Linux

## 🪟 Windows 권장 설정
```bash
git config core.longpaths true
git config core.quotepath false
git config status.showUntrackedFiles all
```

---

## 📂 사용법

## 0. 레포 준비
```bash
git clone https://github.com/<user>/<repo>.git
cd <repo>
```

## 1. 백업 브랜치 만들기 (선택)
```bash
git branch backup/main-before-replay origin/main
```

## 2. 작업용 브랜치 생성
```bash
git switch -c history-replay
```

## 3. 인덱스 비우기 (트래킹된 파일 제거, 워킹트리는 유지)
```bash
git read-tree --empty
```

## 4. 스크립트 실행
```bash
python replay_commits.py
```

## 5. 결과 확인
```bash
git log --pretty=format:"%ad %s" --date=iso -n 10
```

## 6. 푸시
```bash
git push -u origin history-replay
```

## 7. main에 반영 (필요 시)

### 7-1. 히스토리만 합치기 (내용 유지)
```bash
git checkout main
git merge -s ours --no-ff --allow-unrelated-histories history-replay
git push
```

### 7-2. history-replay로 main 덮어쓰기
```bash
git checkout main
git reset --hard history-replay
git push --force-with-lease
```

---

## 🔍 트러블슈팅

### 변경 없음 → 스킵만 나온다
- `git read-tree --empty` 실행했는지 확인

### Windows에서 경로가 깨진다
```bash
git config core.quotepath false
# 또는 literal pathspec으로 강제 추가
git add -f -- ":(top,literal)백준/Bronze/1008. A／B/"
```

### .gitignore에 걸려서 파일이 안 올라간다
- `.gitignore` 마지막에 예외 규칙 추가
```gitignore
!백준/**
```

### fatal: refusing to merge unrelated histories
- 병합 시 `--allow-unrelated-histories` 사용

---

## 📌 옵션/확장

- `TARGET_ROOTS = ["백준"]` → 필요 시 `["백준", "SWEA", "프로그래머스"]`로 확장
- `LABEL_PATTERNS`에 `"제출 날짜"`, `"제출일자"` 등 원하는 레이블을 자유롭게 추가

---

## 🧩 스크립트 핵심 (요약)

- `README.md`에서 **제출 일자**(예: `2025년 4월 1일 09:56:28`) 파싱
- 폴더 단위로 `git add -f -- <폴더>` 후, 날짜를 환경변수로 주고 `git commit -m "<제목>"`
- 커밋 순서는 제출 시간 오름차순

---

## 📜 라이선스
MIT License
