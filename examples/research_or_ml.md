# 연구 또는 ML 프로젝트 이식 예시

## 추천 레벨

Level 1

단, verification-plan을 일반 소프트웨어 프로젝트보다 훨씬 강하게 둔다.

## 이유

가장 큰 위험은 성능 개선이 아니라 평가 기준을 흔드는 것이다.

## 먼저 할 일

1. repo-level 기본 문서를 설치한다
2. `research` profile로 task를 생성한다

예:

```bash
KIT=/absolute/path/to/agent-work-harness
REPO=/absolute/path/to/repo

"$KIT/scripts/scaffold.sh" default "$REPO"
"$KIT/scripts/new-task.sh" research "$REPO" optimizer-ablation
```

## repo-level `AGENTS.md`에 꼭 채울 것

- 수정 금지 평가 파일
- 수정 가능한 실험 파일
- 학습 또는 평가 명령
- keep/discard를 가르는 metric

## repo-level `verification-plan.md`에 꼭 채울 것

- 고정 metric 명령
- 시간 또는 budget 제한
- 결과 기록 형식
- revert 조건

## 좋은 contract 예시

- `docs/tasks/<task-slug>/contract.md`에서 `train.py` 또는 하나의 experiment config만 수정 가능
- evaluation script와 dataset split은 frozen

## 좋은 handoff 예시

- `docs/tasks/<task-slug>/handoff.md`에 baseline 수치
- 이번 실험 diff 범위
- keep인지 discard인지 판정 상태
- 다음 실험에서 바꿀 변수 한두 개만 명시
