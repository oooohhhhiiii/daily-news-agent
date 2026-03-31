# Daily News Agent

10개 경제 언론사의 전날 뉴스를 수집하고 요약하여 Telegram으로 전달하는 자동화 에이전트.

## 대상 언론사
매일경제, 한국경제, 서울경제, 아시아경제, 이데일리, 헤럴드경제, 파이낸셜뉴스, 조선비즈, 이투데이, 한경비즈니스

## 일일 워크플로우 (매일 아침 6시 KST)

### Step 1: 뉴스 크롤링
```bash
python crawl_naver.py
```
- 10개 언론사의 전날(KST 기준) 기사 제목+링크를 수집
- 결과: `output/headlines_YYYYMMDD.json`

### Step 2: 기사 분류 및 선별
- `output/headlines_YYYYMMDD.json` 파일을 읽는다
- 기사 제목을 기반으로 5개 카테고리로 분류:
  - **매크로**: 금리, 환율, GDP, 물가, 통화정책, 국제경제, 무역 등 거시경제 이슈
  - **M&A**: 기업 인수합병, 경영권 분쟁, 합병 심사, 기업 매각, 구조조정 등
  - **PE**: 사모펀드, 바이아웃, PEF 투자·회수, 기업 구조조정 펀드 등
  - **VC**: 벤처캐피탈, 스타트업 투자, 시리즈 펀딩, 액셀러레이터, IPO 등
  - **주식**: 주식시장, 종목 분석, ETF, 시장 전망, 개인투자, 채권, 파생상품 등
- 카테고리당 가장 중요한 기사 10개를 아래 우선순위 기준으로 선별:
  1. 시장 영향력 큰 뉴스 (정책 변화, 대형 딜, 주요 지표 발표)
  2. 속보성·단독 기사
  3. 여러 언론사가 다루는 핵심 이슈
  4. 업계 트렌드 변화를 시사하는 기사
- 선별된 기사의 URL 목록을 생성

### Step 3: 본문 수집
```bash
python fetch_content.py --urls "url1,url2,url3,..."
```
- 선별된 ~50개 기사의 본문을 수집
- 결과: `output/articles_YYYYMMDD.json`

### Step 4: 뉴스레터 작성
- `output/articles_YYYYMMDD.json`을 읽는다
- 카테고리별로 기사를 제목 + 2~3줄 요약으로 정리
- 뉴스레터를 `output/msg_[카테고리].txt` 파일로 작성
- 뉴스레터 형식:

```
📰 [카테고리명] 뉴스 브리핑 (YYYY-MM-DD)

1. 기사 제목
[언론사] 요약 2~3줄
🔗 원문 링크

2. 기사 제목
...
```

### Step 5: HTML 변환 및 Telegram 전송
카테고리별로 txt → HTML 변환 후 파일 첨부 전송:
```bash
python html_generator.py --input output/msg_macro.txt --output output/NaverNews_macro_YYMMDD.html
python telegram_send.py --document output/NaverNews_macro_YYMMDD.html "📰 매크로 뉴스 브리핑"

python html_generator.py --input output/msg_ma.txt --output output/NaverNews_ma_YYMMDD.html
python telegram_send.py --document output/NaverNews_ma_YYMMDD.html "📰 M&A 뉴스 브리핑"

python html_generator.py --input output/msg_pe.txt --output output/NaverNews_pe_YYMMDD.html
python telegram_send.py --document output/NaverNews_pe_YYMMDD.html "📰 PE 뉴스 브리핑"

python html_generator.py --input output/msg_vc.txt --output output/NaverNews_vc_YYMMDD.html
python telegram_send.py --document output/NaverNews_vc_YYMMDD.html "📰 VC 뉴스 브리핑"

python html_generator.py --input output/msg_stock.txt --output output/NaverNews_stock_YYMMDD.html
python telegram_send.py --document output/NaverNews_stock_YYMMDD.html "📰 주식 뉴스 브리핑"
```

### Step 6: 더벨 뉴스 크롤링
기존 뉴스레터 전송 완료 후 즉시 실행:
```bash
python crawl_thebell.py
```
- 더벨 전날 무료 공개된 기사를 크롤링 (Deal, 금융, 투자, 산업 카테고리)
- 무료 기사의 상세 페이지에서 본문 요약 추출
- 결과: `output/thebell_YYYYMMDD.json`

### Step 7: 더벨 기사 분류
- `output/thebell_YYYYMMDD.json` 파일을 읽는다
- 기사를 더벨 고유 4개 카테고리로 분류 (`thebell_category` 필드 활용):
  - **Deal**: 채권, 주식, M&A, 프로젝트 파이낸스 등 딜 관련
  - **금융**: 은행, 증권, 보험, 저축은행, 핀테크 등 금융업
  - **투자**: IB, 자산운용, PEF/벤처캐피탈, 연기금 등 투자업
  - **산업**: 제조, 건설, 유통, 에너지, IT 등 산업 전반
- 선별 없이 **카테고리별 전체 기사**를 뉴스레터에 포함

### Step 8: 더벨 본문 수집
- 더벨 무료 공개 기사는 크롤링 시 이미 본문 요약이 수집되어 있으므로 별도 본문 수집 불필요
- `output/thebell_YYYYMMDD.json`의 `summary` 필드를 활용

### Step 9: 더벨 뉴스레터 작성
- `output/thebell_YYYYMMDD.json`을 읽는다
- 카테고리별 **전체 기사**를 제목 + 2~3줄 요약으로 정리
- 뉴스레터를 `output/msg_thebell_[카테고리].txt` 파일로 작성
- 뉴스레터 형식:

```
📰 더벨 [카테고리명] 뉴스 브리핑 (YYYY-MM-DD)

1. 기사 제목
[더벨] 요약 2~3줄
🔗 원문 링크

2. 기사 제목
...
```

### Step 10: 더벨 HTML 변환 및 Telegram 전송
카테고리별로 txt → HTML 변환 후 별도 텔레그램 봇(`THEBELL_TELEGRAM_BOT_TOKEN`)으로 파일 첨부 전송:
```bash
python html_generator.py --input output/msg_thebell_deal.txt --output output/TheBell_deal_YYMMDD.html
python send_thebell.py --document output/TheBell_deal_YYMMDD.html "📰 더벨 Deal 뉴스 브리핑"

python html_generator.py --input output/msg_thebell_finance.txt --output output/TheBell_finance_YYMMDD.html
python send_thebell.py --document output/TheBell_finance_YYMMDD.html "📰 더벨 금융 뉴스 브리핑"

python html_generator.py --input output/msg_thebell_invest.txt --output output/TheBell_invest_YYMMDD.html
python send_thebell.py --document output/TheBell_invest_YYMMDD.html "📰 더벨 투자 뉴스 브리핑"

python html_generator.py --input output/msg_thebell_industry.txt --output output/TheBell_industry_YYMMDD.html
python send_thebell.py --document output/TheBell_industry_YYMMDD.html "📰 더벨 산업 뉴스 브리핑"
```

### Step 11: Notion 아카이브 저장
Telegram 전송 완료 후, 생성된 HTML 파일 9개를 Notion 페이지에 업로드한다.

- `.env` 파일에서 `NOTION_PAGE_ID`를 읽는다
- Notion MCP 도구를 사용하여 해당 페이지에 HTML 파일을 업로드한다

#### 실행 절차:
1. Notion MCP의 `notion_append_block_children` 도구를 사용하여 NOTION_PAGE_ID 페이지에 토글 블록 생성:
   - **토글 블록 제목**: "YYYY-MM-DD Daily News" (날짜는 전날 기준)
2. 토글 블록 안에 HTML 파일 9개를 업로드:
   - 네이버 뉴스 (5개): `NaverNews_macro_YYMMDD.html`, `NaverNews_ma_YYMMDD.html`, `NaverNews_pe_YYMMDD.html`, `NaverNews_vc_YYMMDD.html`, `NaverNews_stock_YYMMDD.html`
   - 더벨 뉴스 (4개): `TheBell_deal_YYMMDD.html`, `TheBell_finance_YYMMDD.html`, `TheBell_invest_YYMMDD.html`, `TheBell_industry_YYMMDD.html`
3. Notion MCP의 파일 업로드 기능을 활용하여 각 HTML 파일을 Notion에 첨부

#### 주의사항:
- Notion 저장 실패 시 오류를 콘솔에 출력하되 전체 워크플로우는 중단하지 않음

## 주의사항
- 모든 스크립트는 프로젝트 루트 디렉토리에서 실행
- 뉴스레터 요약은 한국어로 작성
- 뉴스레터는 HTML 파일로 변환하여 Telegram document로 첨부 전송
- 크롤링 실패 시 오류 내용을 Telegram으로 알림
