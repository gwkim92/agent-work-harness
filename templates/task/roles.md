# Multi-Agent Roles

이 문서는 multi-agent 구성이 유효해졌을 때 역할과 책임을 정의하기 위한 템플릿이다.

기본 원칙:

- 역할은 적을수록 좋다
- 역할마다 ownership이 명확해야 한다
- 같은 파일을 여러 역할이 동시에 수정하지 않는다

## Why Multi-Agent

- 왜 single-agent로는 부족한가:
- 어떤 병목을 풀기 위해 역할을 나누는가:

## Shared Constraints

- 공통 목표:
- 공통 금지사항:
- 공통 verification 기준:

## Role 1

- 이름:
- 책임:
- 입력:
- 출력:
- 수정 가능한 범위:
- 수정 금지 범위:

## Role 2

- 이름:
- 책임:
- 입력:
- 출력:
- 수정 가능한 범위:
- 수정 금지 범위:

## Role 3

- 이름:
- 책임:
- 입력:
- 출력:
- 수정 가능한 범위:
- 수정 금지 범위:

## Default Role Patterns

필요하면 아래 패턴을 사용한다.

- planner
  - 작업 분해와 milestone 설계
- generator
  - 실제 구현
- evaluator
  - 검증, QA, adversarial review
- specialist
  - 특정 도메인 분석
- integrator
  - 충돌 정리와 최종 통합

## Coordination Rules

- 각 역할은 자기 책임 범위를 넘지 않는다
- evaluator는 가능하면 generator와 분리한다
- integrator 없이 겹치는 수정이 생기면 다시 역할을 나눈다
