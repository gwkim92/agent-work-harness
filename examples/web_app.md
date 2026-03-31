# 웹앱 이식 예시

## 추천 레벨

Level 2

이유:

- 코드가 맞아도 실제 브라우저 동작이 다를 수 있다
- 사용자 상호작용 검증이 필요하다

## 먼저 할 일

1. repo-level 기본 문서를 설치한다
2. `web` profile로 task를 생성한다

예:

```bash
KIT=/absolute/path/to/codex_project_transplant_kit
REPO=/absolute/path/to/repo

"$KIT/scripts/scaffold.sh" default "$REPO"
"$KIT/scripts/new-task.sh" web "$REPO" checkout-redesign
```

## repo-level `AGENTS.md`에 꼭 채울 것

- 개발 서버 명령
- 테스트 명령
- 린트와 타입체크 명령
- 라우트, 컴포넌트, e2e 테스트 위치
- "UI 완료 주장은 브라우저 검증이 필요하다" 규칙

## repo-level `verification-plan.md`에 꼭 채울 것

- lint
- typecheck
- 관련 단위 테스트
- 브라우저 smoke path
- 시각 변경이면 스크린샷 또는 상호작용 증거

## 좋은 contract 예시

- `docs/tasks/<task-slug>/contract.md`에서 edit scope는 특정 route group과 공유 UI token까지만
- auth, billing, analytics는 out of scope

## 좋은 handoff 예시

- `docs/tasks/<task-slug>/handoff.md`에 현재 페이지에서 재현되는지 여부
- 어떤 브라우저 경로까지 확인했는지
- stale state인지 fresh load인지

## evaluator artifact

- 코드/구현 관점은 `review.md`
- 실제 동작 관점은 `qa.md`

기존 task에 `plan.md`만 추가하려면:

```bash
KIT=/absolute/path/to/codex_project_transplant_kit
REPO=/absolute/path/to/repo

"$KIT/scripts/new-task.sh" web "$REPO" checkout-redesign --with-plan --only-missing
```
