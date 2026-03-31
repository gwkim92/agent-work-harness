# Multi-Agent Pattern Guide

이 문서는 `revfactory/harness`에서 참고할 만한 멀티에이전트 개념만 추려서, Agent Work Harness의 철학에 맞게 재구성한 가이드다.

중요한 전제:

- 우리는 multi-agent를 기본값으로 두지 않는다
- vendor-specific 구조를 source of truth로 삼지 않는다
- 패턴 이름과 handoff 규칙만 가져오고, Claude 전용 구조는 그대로 복사하지 않는다

## 무엇을 가져올까

가져올 개념:

- 역할을 자유형이 아니라 패턴으로 부르는 방식
- coordinator, specialist, reviewer, integrator 같은 역할 vocabulary
- pipeline, fan-out/fan-in, reviewer gate 같은 topology vocabulary
- artifact handoff를 명시하는 방식
- 팀을 만들기 전에 "왜 이 topology인가"를 먼저 설명하는 방식

가져오지 않을 개념:

- team-first 기본값
- Claude 전용 폴더 구조를 canonical로 두는 방식
- 모델 설정을 문서 구조와 결합하는 방식

## 권장 패턴 카탈로그

### 1. planner -> generator -> evaluator

언제 쓰나:

- 구현 전에 구조를 먼저 잠가야 할 때
- generator와 evaluator를 논리적으로 분리해야 할 때
- 완료 조건이 강하게 중요할 때

장점:

- pass/fail gate가 선명하다
- overclaim을 줄이기 쉽다

주의:

- planner가 과도하게 길어지면 오히려 병목이 된다

### 2. coordinator + specialists

언제 쓰나:

- 여러 도메인 분석이 분리 가능할 때
- 한 역할이 전체를 다 이해하려고 해서 비효율이 날 때

장점:

- coordinator가 우선순위와 흐름을 잡고
- specialists는 자기 artifact에 집중할 수 있다

주의:

- coordinator가 직접 구현까지 맡기 시작하면 구조가 무너진다

### 3. parallel specialists -> integrator

언제 쓰나:

- 수정 영역이 서로 명확히 분리될 때
- 병렬 구현이 실제로 시간을 줄일 수 있을 때

장점:

- ownership이 명확하면 가장 효율적인 패턴이 된다

주의:

- integrator 없이 병렬 구현만 있으면 마지막에 혼란이 커진다

### 4. researcher -> synthesizer -> reviewer

언제 쓰나:

- 리서치, 비교, 문서화 중심 작업
- 근거와 결론을 분리하고 싶을 때

장점:

- 조사와 주장 사이를 한 번 더 정리할 수 있다

주의:

- synthesizer가 출처와 해석을 섞지 않도록 주의해야 한다

## 패턴 선택 규칙

먼저 이 질문에 답한다.

- 병목이 순차적인가, 병렬적인가
- 문제는 구현인가, 조사인가, 검증인가
- 최종 gate는 누가 쥐어야 하는가
- 공유 artifact가 필요한가, 아니면 ownership 분리가 더 중요한가

그 다음 가장 단순한 패턴 하나를 고른다.

패턴을 섞는 것은 가능하지만:

- 먼저 기본 패턴 하나를 정하고
- 예외 구간만 추가하는 편이 좋다

## Artifact Handoff 규칙

역할 간 handoff는 가급적 파일이나 명시적 산출물로 남긴다.

좋은 handoff:

- 입력 artifact가 명확하다
- 출력 artifact가 명확하다
- 다음 역할이 무엇을 기다리는지 명확하다
- pass/fail 또는 ready/not-ready 조건이 있다

나쁜 handoff:

- "거의 됨"
- "이제 네가 이어서"
- 채팅에만 남는 상태

## 최종 원칙

- multi-agent는 패턴을 채택할 때만 시작한다
- 각 역할은 ownership과 artifact를 가져야 한다
- evaluator 또는 reviewer gate는 가능한 한 분리한다
- topology는 문서로 먼저 설계하고 나중에 실행한다
