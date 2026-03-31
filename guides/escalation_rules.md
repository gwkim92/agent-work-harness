# 승격 규칙 가이드

이 문서는 guided single-agent에서 planner, multi-agent, automation으로 올라갈 때의 판단 기준을 설명한다.

핵심 원칙:

- 기본값은 승격이 아니다
- 병목이 보이면 승격한다
- 승격은 실행 전에 먼저 문서로 scaffold한다

## 1. 언제 `docs/tasks/<task-slug>/plan.md`를 추가할까

아래 중 둘 이상이면 planner 문서를 추가하는 편이 좋다.

- 작업이 하루 이상 이어질 가능성이 있다
- milestone이 둘 이상이다
- 파일 변경이 다섯 개 이상으로 예상된다
- 순차 의존 단계가 명확하다
- 중간 체크포인트 없이 끝내기 위험하다
- 세션이 끊기면 상태 복구 비용이 크다

추가할 파일:

- `docs/tasks/<task-slug>/plan.md`

## 2. 언제 evaluator 분리를 더 강화할까

아래 중 하나라도 강하면 Level 2로 올리는 편이 좋다.

- agent가 완료를 자주 낙관적으로 말한다
- 테스트는 통과하지만 실제 동작이 자주 어긋난다
- UI나 런타임 상태가 중요하다
- 로그, trace, browser evidence가 필요하다

조치:

- QA 단계를 분리한다
- 브라우저, 로그, 실제 요청, artifact 확인을 verification에 넣는다

## 3. 언제 multi-agent를 고려할까

아래 중 둘 이상이면 multi-agent 문서를 추가 검토한다.

- 독립 작업 흐름이 둘 이상 병렬 가능하다
- 역할이 명확히 다르다
  - 예: planner, generator, evaluator, domain specialist
- 한 역할의 문맥이 다른 역할을 방해한다
- review나 adversarial check를 별도 관점으로 분리해야 한다
- 작업이 커서 ownership을 문서로 나누지 않으면 충돌이 난다

추가할 파일:

- `docs/tasks/<task-slug>/roles.md`
- `docs/tasks/<task-slug>/topology.md`

먼저 정할 것:

- 어떤 패턴을 쓸지
  - `planner -> generator -> evaluator`
  - `coordinator + specialists`
  - `parallel specialists -> integrator`
  - `researcher -> synthesizer -> reviewer`
- 어떤 artifact를 서로 주고받을지
- 어떤 역할이 최종 verification gate를 쥘지

참고:

- `guides/multi_agent_patterns.md`

주의:

- 역할 문서 생성은 agent가 스스로 해도 된다
- 실제 multi-agent 실행은 호스트의 권한 정책과 사용자 승인 규칙을 따른다

## 4. 언제 automation loop를 고려할까

아래 중 둘 이상이면 automation contract를 추가 검토한다.

- 같은 종류의 작업이 반복된다
- keep/discard 판단을 기계적으로 내릴 수 있다
- 시간 예산이나 실행 횟수를 명확히 제한할 수 있다
- 실패 시 되돌리거나 끌 수 있다
- 로그나 metric으로 상태를 관측할 수 있다

추가할 파일:

- `docs/tasks/<task-slug>/loop_contract.md`

주의:

- 검증 기준이 불안정하면 자동화하지 않는다
- rollback이 없으면 자동화하지 않는다

## 5. agent가 자율적으로 어디까지 해도 되나

기본 규칙은 다음과 같다.

- 승격 필요성을 감지하면 제안할 수 있다
- 관련 task 문서를 scaffold할 수 있다
- contract와 verification-plan에 승격 이유를 기록할 수 있다

다만 아래는 프로젝트나 호스트 정책을 따른다.

- 실제 multi-agent 실행
- 실제 자동화 활성화
- 권한 상승이 필요한 외부 액션

즉, "문서 승격"은 agent가 주도해도 되지만, "실행 승격"은 정책 확인이 필요할 수 있다.

## 6. 기본 승격 순서

1. repo-level `docs/escalation-rules.md`
2. task-level `docs/tasks/<task-slug>/plan.md`
3. evaluator 강화
4. task-level `roles.md`
5. task-level `topology.md`
6. task-level `loop_contract.md`

처음부터 4단계로 바로 뛰는 것보다, 한 단계씩 올리는 편이 안전하다.
