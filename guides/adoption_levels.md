# 하네스 도입 레벨

이 문서는 새 프로젝트에 얼마만큼의 Codex 하네스를 심어야 하는지 결정하기 위한 가이드다.

## 기본 원칙

처음부터 큰 시스템을 넣지 않는다.

다음 순서로 확장한다.

1. repo-level 맵
2. repo-level 검증
3. task contract
4. task handoff
5. evaluator artifact
6. planner
7. multi-agent
8. automation

## Level 0: Bare Single-Agent

### 언제 쓰는가

- 프로젝트가 작다
- 작업이 짧다
- 실패 비용이 낮다

### 넣을 것

- repo-level `AGENTS.md`
- repo-level `docs/verification-plan.md`
- repo-level `docs/tasks/README.md`

### 넣지 말 것

- planner
- multi-agent
- 장기 자동화

### 위험

- 멀티파일 작업에서 범위가 쉽게 퍼진다
- 세션이 끊기면 상태 복구가 약하다

## Level 1: Guided Single-Agent

### 언제 쓰는가

- 랜덤한 새 프로젝트의 기본값
- 작업이 여러 파일에 걸친다
- 세션을 나눠 진행할 수 있다
- 완료 기준을 밖에 적어야 한다

### 넣을 것

- repo-level `AGENTS.md`
- repo-level `docs/verification-plan.md`
- repo-level `docs/tasks/README.md`
- 선택적으로 repo-level `docs/escalation-rules.md`
- task-level `docs/tasks/<task-slug>/contract.md`
- task-level `docs/tasks/<task-slug>/handoff.md`

### 장점

- 과하지 않다
- 대부분의 프로젝트에서 바로 쓸 수 있다
- 품질과 속도의 균형이 좋다

## Level 2: Generator + Evaluator

### 언제 쓰는가

- 에이전트가 완료를 너무 낙관적으로 말한다
- 회귀가 자주 난다
- UI나 런타임 동작이 중요하다

### Level 1에 추가할 것

- task-level `review.md` 또는 `qa.md`
- 브라우저 검증 또는 로그/실행 산출물 검증
- 평가 체크리스트

### 장점

- "코드는 그럴듯한데 동작이 다르다" 문제를 줄인다

### 주의

- generator가 evaluator 역할까지 동시에 하지 않게 해야 한다

## Level 3: Planner + Generator + Evaluator

### 언제 쓰는가

- 작업이 크다
- milestone 관리가 필요하다
- 작업이 하루 이상 이어진다

### Level 2에 추가할 것

- task-level `plan.md`
- milestone 기준
- 더 엄격한 handoff

### 장점

- 긴 작업에서 문맥 손실을 줄인다

### 주의

- 작업이 작으면 오버헤드가 커진다

## Level 4: Planner + Generator + Evaluator + Multi-Agent

### 언제 쓰는가

- 역할 분리가 명확하다
- 병렬 가능한 흐름이 있다
- ownership을 나누지 않으면 충돌이 난다
- review 관점을 별도 역할로 떼야 한다

### Level 3에 추가할 것

- task-level `roles.md`
- task-level `topology.md`

### 주의

- 문서 승격과 실행 승격을 구분해야 한다
- 실제 multi-agent 실행은 호스트 정책을 따른다

## Level 5: Long-Running Loop

### 언제 쓰는가

- 반복 실험
- 정기 감사
- 자동 연구 루프
- 파일럿 rollout 모니터링

### Level 4에 추가할 것

- bounded budget
- keep/discard 기준
- rollback 조건
- 관측성
- task-level `loop_contract.md`

### 주의

- 자동화는 검증된 루프에만 얹는다
- 불안정한 평가 기준 위에 자동화를 얹으면 오히려 망가진다

## 권장 선택표

### 웹앱

- 기본: Level 2
- 이유: 사용자 동작 검증이 필요하기 때문

### 백엔드/API

- 기본: Level 1
- 상황에 따라 Level 2

### 연구/ML

- 기본: Level 1
- 단, repo-level verification-plan을 매우 강하게

### 새 라이브러리 도입

- 기본: Level 1
- adapter, pilot, oracle 비교를 task contract에 넣는다
