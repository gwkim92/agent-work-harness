# Codex Project Transplant Kit

이 폴더는 "아무 새 프로젝트에나 Codex 작업 하네스를 이식하기 위한 독립 패키지"다.

핵심 목표는 세 가지다.

- repo-level 규칙과 task-level 상태를 분리한다
- generator와 evaluator를 문서 아티팩트로도 분리한다
- planner, multi-agent, automation 승격을 임의 감이 아니라 규칙으로 다룬다

이 패키지는 아래 로컬 리서치를 바탕으로 압축했다.

- `하네스_엔지니어링_통합_가이드.md`
- `gstack_agent_reference.md`
- `ADK_에이전트_설계_가이드.md`
- `agentscope_detailed_report.md`
- `karpathy_autoresearch_상세분석_및_활용가이드.md`
- `pretext-adoption-report.md`

## 패키지 모델

이 패키지는 두 층으로 나뉜다.

### Repo-Level

프로젝트에 한 번만 설치하는 문서다.

- `AGENTS.md`
- `docs/verification-plan.md`
- `docs/escalation-rules.md`
- `docs/tasks/README.md`

### Task-Level

각 작업마다 별도 디렉터리를 만들어 누적하는 문서다.

경로:

```text
docs/tasks/<task-slug>/
```

대표 문서:

- `contract.md`
- `handoff.md`
- `plan.md`
- `review.md`
- `qa.md`
- `roles.md`
- `topology.md`
- `loop_contract.md`

즉, 예전처럼 `docs/contract.md` 하나를 덮어쓰는 구조가 아니다.

## 이 패키지에 들어 있는 것

- `guides/principles.md`
  - 리서치에서 추출한 이식 가능한 핵심 원칙
- `guides/adoption_levels.md`
  - 프로젝트 복잡도에 따라 어떤 수준의 하네스를 심을지 결정하는 가이드
- `guides/escalation_rules.md`
  - 언제 planner, multi-agent, automation으로 승격할지 판단하는 가이드
- `templates/repo/`
  - repo-level 템플릿
- `templates/task/`
  - task-level 템플릿
- `scripts/scaffold.sh`
  - repo-level 문서를 설치하는 스크립트
- `scripts/new-task.sh`
  - task 디렉터리를 생성하는 스크립트
- `examples/`
  - 웹앱, 백엔드, 연구/ML, dependency adoption 예시

## 기본 사용 흐름

1. repo-level 문서를 한 번 설치한다
2. 작업이 생기면 `docs/tasks/<task-slug>/`를 생성한다
3. task artifact를 채우며 진행한다
4. 필요하면 해당 task에서만 plan, review, qa, multi-agent, automation 문서를 추가한다

기본값은 여전히 guided single-agent다.

처음부터 planner, multi-agent, automation을 깔아두는 것이 아니라:

- 루트 맵을 짧게 만든다
- repo-level verification을 고정한다
- task별 contract와 handoff를 누적한다
- evaluator artifact는 필요할 때 task에 붙인다

## Repo-Level 설치

설치 스크립트:

- `scripts/scaffold.sh`

프로파일:

- `minimal`
  - `AGENTS.md`
  - `docs/verification-plan.md`
  - `docs/tasks/README.md`
- `default`
  - `minimal` +
  - `docs/escalation-rules.md`

사용법:

```bash
KIT=/absolute/path/to/codex_project_transplant_kit
REPO=/absolute/path/to/repo

"$KIT/scripts/scaffold.sh" minimal "$REPO"
"$KIT/scripts/scaffold.sh" default "$REPO"
```

이 스크립트는 preflight를 먼저 수행한다.

- 충돌 파일이 하나라도 있으면 아무것도 복사하지 않는다
- `--force`가 있을 때만 덮어쓴다

## Task 생성

task 생성 스크립트:

- `scripts/new-task.sh`

기본 프로파일:

- `general`
  - `contract.md`
  - `handoff.md`
- `web`
  - `general` +
  - `review.md`
  - `qa.md`
- `backend`
  - `general` +
  - `review.md`
- `research`
  - `general` +
  - `review.md`
- `dependency`
  - `general` +
  - `plan.md`
  - `review.md`

사용법:

```bash
KIT=/absolute/path/to/codex_project_transplant_kit
REPO=/absolute/path/to/repo

"$KIT/scripts/new-task.sh" general "$REPO" feature-x
"$KIT/scripts/new-task.sh" web "$REPO" checkout-redesign
```

선택 플래그:

- `--with-plan`
- `--with-review`
- `--with-qa`
- `--with-roles`
- `--with-topology`
- `--with-loop-contract`
- `--only-missing`
- `--force`

예:

```bash
KIT=/absolute/path/to/codex_project_transplant_kit
REPO=/absolute/path/to/repo

"$KIT/scripts/new-task.sh" web "$REPO" checkout-redesign --with-plan
"$KIT/scripts/new-task.sh" general "$REPO" migration-audit --with-roles --with-topology
"$KIT/scripts/new-task.sh" general "$REPO" migration-audit --with-plan --only-missing
```

기존 task에 승격 문서만 추가하려면:

- `--only-missing`을 사용한다
- 기존 파일은 건드리지 않고 없는 파일만 추가한다

## 어떤 문서가 언제 필요한가

repo-level:

- `AGENTS.md`
  - 짧은 작업장 맵
- `docs/verification-plan.md`
  - 프로젝트 차원의 기본 검증 기준
- `docs/escalation-rules.md`
  - 승격 규칙

task-level:

- `contract.md`
  - 범위, mutable surface, 완료 조건
- `handoff.md`
  - 다음 세션 복구용 상태 스냅샷
- `plan.md`
  - milestone과 단계 순서가 필요한 작업
- `review.md`
  - 코드/변경 관점 evaluator artifact
- `qa.md`
  - 실제 동작 관점 evaluator artifact
- `roles.md`, `topology.md`
  - multi-agent 승격 문서
- `loop_contract.md`
  - automation 승격 문서

## 왜 이렇게 만들었나

이 구조는 리서치의 핵심 결론을 그대로 반영한다.

1. 루트 문서는 짧은 맵이어야 한다
2. 긴 작업 상태는 task artifact로 남겨야 한다
3. 생성과 평가는 문서 수준에서도 분리되어야 한다
4. planner, multi-agent, automation은 기본값이 아니라 승격이어야 한다
5. 승격은 자의가 아니라 규칙과 문서 scaffold를 통해 이뤄져야 한다

## 언제 이 패키지가 특히 유효한가

- 작업이 여러 파일로 퍼지는 프로젝트
- 세션이 자주 끊기는 환경
- UI 검증이나 실제 런타임 검증이 중요한 프로젝트
- 새 라이브러리, 새 프레임워크, 새 연구 루프를 자주 실험하는 팀
- "에이전트가 일을 했는데 왜 결과가 들쭉날쭉한지" 설명이 필요한 팀

## 언제 과할 수 있는가

- 매우 짧은 단일 파일 수정만 하는 경우
- 실패 비용이 거의 없는 개인 장난감 프로젝트
- 검증 자체가 필요 없을 정도로 범위가 작은 작업

그 경우에는 `minimal` repo 설치만 먼저 하고, task artifact는 필요할 때만 생성해도 된다.
