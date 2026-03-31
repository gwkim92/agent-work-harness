# Claude Adapter Draft

이 문서는 Agent Work Harness의 canonical 구조를 유지한 채 Claude 생태계로 export하는 어댑터 초안이다.

핵심 원칙:

- source of truth는 계속 repo-local harness 파일이다
- Claude 전용 파일은 파생 산출물이다
- adapter는 본체를 대체하지 않고 번역만 한다

## 왜 adapter가 필요한가

`revfactory/harness`를 보면 Claude 환경에서는:

- `.claude/agents/`
- `.claude/skills/`
- `CLAUDE.md`

같은 구조가 매우 유용하다.

하지만 Agent Work Harness의 목표는 범용성이므로, 이 구조를 canonical로 둘 수는 없다.

따라서 필요한 것은:

- 본체는 그대로 두고
- Claude가 잘 읽는 구조로 export하는 thin adapter

다.

## Adapter Scope

초기 범위:

- `AGENTS.md` -> `CLAUDE.md`
- `docs/verification-plan.md` -> Claude용 운영 메모 일부
- `docs/tasks/<task-slug>/roles.md` + `topology.md` -> `.claude/agents/*.md`

초기 범위 밖:

- 모델 선택 자동화
- Claude 전용 런타임 설정 강제
- 본체보다 더 많은 의미를 Claude 파일에만 저장하는 것

## Proposed Command

```bash
awh export claude --repo /path/to/repo
awh export claude --repo /path/to/repo --task bootstrap-api
```

## Output Shape

### Repo-Level

- `CLAUDE.md`
  - `AGENTS.md`의 축약 또는 import-oriented mirror
  - verification-plan 핵심 경계
  - task artifact 위치 안내

### Task-Level Multi-Agent Export

- `.claude/agents/<task-slug>-coordinator.md`
- `.claude/agents/<task-slug>-reviewer.md`
- `.claude/agents/<task-slug>-specialist-*.md`

이 파일들은 `roles.md`와 `topology.md`에서 파생된다.

## Mapping Rules

### `roles.md` -> Claude agent card

매핑할 필드:

- 이름
- 타입
- 책임
- 성공 조건
- 입력
- 출력
- 수정 가능한 범위
- 수정 금지 범위
- handoff 대상

### `topology.md` -> orchestration hint

매핑할 필드:

- topology type
- execution order
- handoff edges
- file ownership
- final verification owner

## Safety Rules

- generated Claude files는 언제든 다시 생성 가능해야 한다
- 수동 편집이 필요하면 canonical 문서에 먼저 반영한다
- Claude-specific 지시가 canonical 원칙과 충돌하면 canonical 쪽을 우선한다

## Why This Matters

이 방식이면:

- 본체는 범용으로 유지하고
- Claude 사용자 경험은 개선하고
- vendor lock-in은 피할 수 있다

즉, adapter는 배포 채널을 늘리지만 철학은 바꾸지 않는다.
