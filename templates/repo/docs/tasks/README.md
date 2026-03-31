# Task Directories

이 디렉터리는 작업별 아티팩트를 누적하기 위한 위치다.

각 작업은 아래처럼 자기 디렉터리를 가진다.

```text
docs/tasks/<task-slug>/
  contract.md
  handoff.md
  plan.md
  review.md
  qa.md
  roles.md
  topology.md
  loop_contract.md
```

모든 파일이 항상 필요한 것은 아니다.

기본값:

- `contract.md`
- `handoff.md`

필요할 때 추가:

- `plan.md`
- `review.md`
- `qa.md`
- `roles.md`
- `topology.md`
- `loop_contract.md`

새 작업 디렉터리는 `scripts/new-task.sh`로 생성하는 것을 권한다.

이미 존재하는 task에 plan, review, qa 같은 문서를 나중에 추가하려면 `--only-missing`을 사용한다.
