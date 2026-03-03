# SeenThis Crawler

정부/스타트업 지원사업 공고를 자동 크롤링하여 Slack으로 알림을 보내주는 도구.

## 크롤링 대상

| 보드 | URL | 설명 |
|------|-----|------|
| kstartup | https://seenthis.kr/kstartup | 스타트업 지원사업 |
| bizinfo | https://seenthis.kr/bizinfo | 정부 지원사업 |

## 동작 방식

1. 각 보드의 최근 3페이지를 크롤링하여 공고 목록 수집
2. `seen_posts.json`과 비교하여 신규 공고만 필터링
3. 신규 공고의 상세 내용을 가져와 200자로 요약
4. Slack Webhook으로 **한 번에 일괄 전송** (공고별 개별 알림 아님)
5. `seen_posts.json` 업데이트 (보드당 최대 200건 유지)

## 설정

| 환경변수 | 설명 |
|----------|------|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL |

## 실행

```bash
pip install -r requirements.txt
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..." python3 crawler.py
```

## 자동 실행 (GitHub Actions)

- 매 정시(1시간 간격) 자동 실행
- self-hosted runner 사용
- `SLACK_WEBHOOK_URL`은 GitHub Secrets에 등록

## TODO

- [ ] AI(LLM) 기반 지원사업 큐레이팅 기능 추가
  - 회사 정보(업종, 규모, 지역 등)를 기준으로 관련성 높은 공고만 필터링
  - 공고 내용에서 핵심 정보(접수기간, 지원대상, 지원금액 등)를 구조화하여 정리
  - 지원 적합도 판단 및 요약 제공
