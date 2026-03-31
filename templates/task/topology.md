# Multi-Agent Topology

이 문서는 여러 역할이 어떤 순서와 연결 구조로 일할지 정의한다.

## Topology Type

- planner -> generator -> evaluator
- coordinator + specialists
- parallel specialists -> integrator
- researcher -> synthesizer -> reviewer
- other:

## Why This Topology

- 왜 이 구조가 필요한가:
- single-agent 대비 기대 이점:
- 어떤 병목을 직접 줄이는가:

## Topology Rules

- source of truth는 어디인가:
- 공통 artifact 위치는 어디인가:
- 누가 final gate를 쥐는가:
- 누가 topology 변경 권한을 갖는가:

## Node Definitions

### Node 1

- 이름:
- 역할:
- 입력:
- 출력:
- ownership:
- blocker:

### Node 2

- 이름:
- 역할:
- 입력:
- 출력:
- ownership:
- blocker:

### Node 3

- 이름:
- 역할:
- 입력:
- 출력:
- ownership:
- blocker:

## Execution Order

1. 첫 단계:
2. 둘째 단계:
3. 셋째 단계:

## Handoff Edges

- Edge 1:
  - from:
  - to:
  - handoff artifact:
  - handoff 조건:

- Edge 2:
  - from:
  - to:
  - handoff artifact:
  - handoff 조건:

## Parallelism

- 병렬 가능한 노드:
- 병렬 불가능한 이유:
- fan-out 이후 누가 fan-in을 담당하는가:

## File Ownership

- Node 1 ownership:
- Node 2 ownership:
- Node 3 ownership:

## Integration Rules

- 결과를 누가 합치는가:
- 충돌 시 누가 결정하는가:
- 최종 verification은 누가 책임지는가:

## Failure Handling

- 어떤 노드 실패가 전체를 막는가:
- 실패 시 어디로 되돌아가는가:
- topology를 단순화해야 하는 신호는 무엇인가:

## Escalation Or De-escalation

- 언제 다시 single-agent로 내려갈 수 있는가:
- 언제 역할을 더 쪼개야 하는가:

## Pattern Hints

### planner -> generator -> evaluator

- 구현 전 설계 잠금이 중요할 때
- evaluator gate를 강하게 유지하고 싶을 때

### coordinator + specialists

- 도메인별 조사나 설계가 나뉠 때
- coordinator가 라우팅과 우선순위를 잡아야 할 때

### parallel specialists -> integrator

- 파일 ownership이 분리된 병렬 구현일 때
- 마지막 통합과 충돌 해소가 별도 책임이어야 할 때

### researcher -> synthesizer -> reviewer

- 조사 결과를 한 번 더 정리하고 반론 검토해야 할 때
