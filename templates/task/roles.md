# Multi-Agent Roles

이 문서는 multi-agent 구성이 유효해졌을 때 역할과 책임을 정의하기 위한 템플릿이다.

기본 원칙:

- 역할은 적을수록 좋다
- 역할마다 ownership이 명확해야 한다
- 같은 파일을 여러 역할이 동시에 수정하지 않는다
- 역할은 패턴 위에서 고른다
- artifact handoff가 없는 역할은 만들지 않는다

필드 값이 길거나 여러 개면 다음 줄 bullet list로 적어도 된다.

## Why Multi-Agent

- 왜 single-agent로는 부족한가:
- 어떤 병목을 풀기 위해 역할을 나누는가:

## Chosen Pattern

- 선택한 패턴:
- 이 패턴이 맞는 이유:
- 다른 패턴을 쓰지 않은 이유:

## Shared Constraints

- 공통 목표:
- 공통 금지사항:
- 공통 verification 기준:
- 공통 source of truth:
- 공통 artifact 위치:
- 최종 decision maker:

## Role 1

- 이름:
- 타입:
  - planner
  - coordinator
  - generator
  - evaluator
  - specialist
  - integrator
- 책임:
- 성공 조건:
- 입력:
- 출력:
- 생성하거나 갱신할 artifact:
- 수정 가능한 범위:
- 수정 금지 범위:
- handoff 대상:
- escalation trigger:

## Role 2

- 이름:
- 타입:
- 책임:
- 성공 조건:
- 입력:
- 출력:
- 생성하거나 갱신할 artifact:
- 수정 가능한 범위:
- 수정 금지 범위:
- handoff 대상:
- escalation trigger:

## Role 3

- 이름:
- 타입:
- 책임:
- 성공 조건:
- 입력:
- 출력:
- 생성하거나 갱신할 artifact:
- 수정 가능한 범위:
- 수정 금지 범위:
- handoff 대상:
- escalation trigger:

## Recommended Role Packs

필요하면 아래 패턴 중 하나를 먼저 고른다.

### 1. planner -> generator -> evaluator

- 용도:
  - 순차 단계가 명확하고 verification gate가 중요한 작업
- 핵심:
  - planner는 구조를 고정하고
  - generator는 구현하고
  - evaluator는 pass/fail을 쥔다

### 2. coordinator + specialists

- 용도:
  - 서로 다른 도메인 분석이 필요한 작업
- 핵심:
  - coordinator는 분배와 우선순위를 맡고
  - specialists는 독립 artifact를 만든다

### 3. parallel specialists -> integrator

- 용도:
  - ownership이 분리된 병렬 구현
- 핵심:
  - specialists는 서로 다른 파일 영역을 맡고
  - integrator는 합치기와 최종 검증을 맡는다

### 4. researcher -> synthesizer -> reviewer

- 용도:
  - 조사, 비교, 문서화가 중심인 작업
- 핵심:
  - researcher는 자료를 모으고
  - synthesizer는 결론을 정리하고
  - reviewer는 과신과 누락을 본다

## Shared Artifact Contract

- 역할 간 handoff는 가능한 한 파일이나 명시적 artifact로 남긴다
- artifact가 없으면 "완료"가 아니라 "구두 상태"로 본다
- 공통 작업공간이 필요하면 task 아래 별도 폴더를 명시한다
  - 예: `docs/tasks/<task-slug>/artifacts/`

## Coordination Rules

- 각 역할은 자기 책임 범위를 넘지 않는다
- evaluator는 가능하면 generator와 분리한다
- integrator 없이 겹치는 수정이 생기면 다시 역할을 나눈다
- coordinator는 직접 구현보다 조정과 우선순위에 집중한다
- 한 역할이 blocker가 되면 topology를 다시 설계한다

## Anti-Patterns

- 이름만 다른 generator 둘을 두는 것
- coordinator가 모든 파일을 직접 수정하는 것
- evaluator가 generator와 같은 증거만 반복 확인하는 것
- artifact handoff 없이 채팅으로만 상태를 넘기는 것
