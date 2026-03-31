# Automation Loop Contract

이 문서는 반복 실행, 자동 연구, 정기 감사 같은 루프를 도입할 때 사용한다.

자동화는 검증된 루프에만 얹는다.

## Loop

- 이름:
- 목적:
- 주기 또는 트리거:

## Why This Can Be Automated

- 왜 반복 작업으로 볼 수 있는가:
- 왜 keep/discard 또는 pass/fail 판정이 가능한가:

## Mutable Surface

- 자동화가 만질 수 있는 범위:
- 자동화가 절대 만지면 안 되는 범위:

## Budget

- 실행 시간 한도:
- 실행 횟수 한도:
- 비용 한도:

## Success Criteria

- 어떤 결과면 keep 또는 pass인가:
- 어떤 결과면 discard 또는 fail인가:

## Verification

- 루프가 매번 통과해야 하는 체크:
- 로그, metric, artifact 확인 방법:

## Stop Conditions

- 즉시 중단해야 하는 조건:
- 사람 개입이 필요한 조건:

## Rollback

- 실패 시 되돌리는 방법:
- feature flag 또는 disable path:

## Observability

- 어디에 로그를 남기는가:
- 어떤 metric을 보는가:
- 누가 상태를 확인하는가:

## Human Review

- 사람이 반드시 확인해야 하는 구간:
