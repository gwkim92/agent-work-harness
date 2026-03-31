# 새 라이브러리 도입 이식 예시

## 추천 레벨

Level 1

## 이유

이 경우 핵심 위험은 "효과가 입증되지 않았는데 전면 확장하는 것"이다.

## 먼저 할 일

1. repo-level 기본 문서를 설치한다
2. `dependency` profile로 task를 생성한다

예:

```bash
KIT=/absolute/path/to/agent-work-harness
REPO=/absolute/path/to/repo

"$KIT/scripts/scaffold.sh" default "$REPO"
"$KIT/scripts/new-task.sh" dependency "$REPO" pretext-pilot
```

## contract에 꼭 들어가야 할 것

- `docs/tasks/<task-slug>/contract.md` 기준으로:
- 내부 adapter 생성
- pilot surface 지정
- oracle comparison 계획
- fallback switch

## verification-plan에 꼭 들어가야 할 것

- repo-level `verification-plan.md`에는:
- 이 프로젝트 전반에 공통인 기본 검증 명령
- 공통 rollback 원칙

task-level 문서에는:

- `contract.md`에 pilot 범위와 fallback switch
- `review.md`에 기존 경로와 새 경로 비교 결과
- `qa.md`가 필요하면 브라우저, 로그, metric 증거

## 좋은 contract 예시

- 새 라이브러리는 internal wrapper 뒤에만 사용
- 파일럿 화면 또는 파일럿 endpoint 1개만 대상
- 직접 호출 금지

## 좋은 handoff 예시

- `docs/tasks/<task-slug>/handoff.md`에 어댑터는 어디까지 만들었는지
- 기존 경로와 차이가 난 샘플 케이스
- rollout 가능 여부를 무엇으로 판정할지
