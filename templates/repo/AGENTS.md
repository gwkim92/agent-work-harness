# Repository Working Map

## Purpose

이 저장소의 목적은 `[PROJECT_NAME]`를 개발, 유지보수, 검증하는 것이다.

에이전트는 아래를 우선한다.

- 낙관보다 정확성
- 큰 수정보다 작고 검토 가능한 변경
- 완료 주장보다 검증 증거

## Repository Map

- 앱 코드: `[PATHS_TO_APP_CODE]`
- 테스트: `[PATHS_TO_TESTS]`
- 문서와 설계 노트: `[PATHS_TO_DOCS]`
- 스크립트와 툴링: `[PATHS_TO_SCRIPTS]`
- 민감하거나 고위험인 경로: `[PATHS_TO_PROTECT]`

## Core Commands

- 설치: `[INSTALL_COMMAND]`
- 개발 서버 또는 실행: `[DEV_COMMAND]`
- 테스트: `[TEST_COMMAND]`
- 린트: `[LINT_COMMAND]`
- 타입체크 또는 빌드: `[TYPECHECK_OR_BUILD_COMMAND]`
- E2E 또는 스모크: `[E2E_OR_SMOKE_COMMAND]`

## Boundaries

- 생성 파일은 명시적으로 요구될 때만 수정한다.
- 시크릿, 배포 설정, 과금 로직은 명시적 승인 없이 바꾸지 않는다.
- 각 작업은 자기 task directory 범위 안에서 상태를 관리한다.
- 위험한 기술 도입은 직접 치환보다 내부 어댑터와 파일럿 도입을 우선한다.

## Working Rules

- 현재 작업에 필요한 최소한의 문서만 읽는다.
- 멀티파일, 위험 작업, 장기 작업은 먼저 `docs/tasks/<task-slug>/contract.md`를 만든다.
- 세션을 끊기기 전 `docs/tasks/<task-slug>/handoff.md`를 갱신한다.
- 프로젝트 차원의 완료 기준은 `docs/verification-plan.md`로 판단한다.
- `docs/escalation-rules.md`가 있으면 planner, multi-agent, automation 승격 여부를 그 문서로 판단한다.
- UI 작업은 가능하면 실제 브라우저 경로로 검증한다.
- benchmark, schema, evaluation 기준을 건드리면 그 사실을 반드시 명시한다.

## Definition Of Done

작업은 아래가 모두 충족될 때만 완료다.

- 요청한 변화가 실제로 존재한다
- 필요한 검증이 수행되었다
- 남은 위험과 미검증 영역이 적혀 있다
- 현재 task directory가 다음 사람이 이어받을 수 있을 만큼 갱신되어 있다
