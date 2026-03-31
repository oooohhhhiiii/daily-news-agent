"""Daily News Agent 설정"""

# 네이버 뉴스 언론사 OID
PRESS_OIDS = {
    "매일경제": "009",
    "한국경제": "015",
    "서울경제": "011",
    "아시아경제": "277",
    "이데일리": "018",
    "헤럴드경제": "016",
    "파이낸셜뉴스": "014",
    "조선비즈": "366",
    "이투데이": "648",
    "한경비즈니스": "050",
}

# 뉴스레터 카테고리
CATEGORIES = ["매크로", "M&A", "PE", "VC", "주식"]
ARTICLES_PER_CATEGORY = 10

# 크롤링 설정
REQUEST_DELAY = 0.5  # 요청 간 딜레이 (초)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Telegram API
TELEGRAM_API_URL = "https://api.telegram.org"
