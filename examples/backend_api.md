# 백엔드 API 이식 예시

## 추천 레벨

기본은 Level 1

다만 런타임 상호작용이나 로그 검증이 중요하면 Level 2까지 올린다.

## 먼저 할 일

1. repo-level 기본 문서를 설치한다
2. `backend` profile로 task를 생성한다

예:

```bash
KIT=/absolute/path/to/codex_project_transplant_kit
REPO=/absolute/path/to/repo

"$KIT/scripts/scaffold.sh" default "$REPO"
"$KIT/scripts/new-task.sh" backend "$REPO" add-audit-endpoint
```

## repo-level `AGENTS.md`에 꼭 채울 것

- 앱 실행 명령
- 테스트 명령
- 마이그레이션 명령
- handler, service, schema, integration test 위치
- schema 변경 시 호환성 메모가 필요하다는 규칙

## repo-level `verification-plan.md`에 꼭 채울 것

- 단위 테스트
- 통합 테스트
- 로컬 요청 예시
- 마이그레이션 안전성 점검
- 롤백 경로

## 좋은 contract 예시

- `docs/tasks/<task-slug>/contract.md`에서 handler와 service layer만 in scope
- DB schema는 명시되지 않으면 out of scope

## 좋은 handoff 예시

- `docs/tasks/<task-slug>/handoff.md`에 어떤 endpoint 응답까지 확인했는지
- 로그에서 무엇을 봤는지
- schema를 건드리지 않았는지 또는 건드렸다면 왜인지
