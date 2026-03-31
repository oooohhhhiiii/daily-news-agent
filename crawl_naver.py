"""Stage 1: 네이버 뉴스 - 10개 언론사 전날 기사 제목+링크 수집"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from config import PRESS_OIDS, HEADERS, REQUEST_DELAY


def get_yesterday_date_kst():
    """KST(UTC+9) 기준 전날 날짜를 YYYYMMDD 형식으로 반환"""
    kst_now = datetime.utcnow() + timedelta(hours=9)
    yesterday = kst_now - timedelta(days=1)
    return yesterday.strftime('%Y%m%d'), yesterday.strftime('%Y-%m-%d')


def crawl_press_page(press_name, oid, date_str):
    """특정 언론사의 해당 날짜 기사 제목+링크 수집"""
    url = f"https://media.naver.com/press/{oid}?date={date_str}"
    print(f"  [{press_name}] {url}")

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  [{press_name}] 페이지 접속 실패: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    # 네이버 프레스 페이지에서 기사 링크 추출
    article_links = soup.select('a[href*="n.news.naver.com/article"]')

    seen = set()
    articles = []
    for a in article_links:
        href = a.get('href', '')
        if not href or href in seen:
            continue

        # 제목 추출: <strong> 태그 또는 직접 텍스트
        strong = a.select_one('strong')
        title = strong.get_text(strip=True) if strong else a.get_text(strip=True)

        # 제목이 너무 짧으면 스킵 (네비게이션 링크 등 필터)
        if not title or len(title) < 5:
            continue

        seen.add(href)
        articles.append({
            "press": press_name,
            "title": title,
            "link": href.split('?')[0],  # 쿼리 파라미터 제거
        })

    print(f"  [{press_name}] {len(articles)}개 기사 수집")
    return articles


def main():
    date_str, date_display = get_yesterday_date_kst()
    print(f"수집 대상 날짜: {date_display} (KST 기준 전날)")

    all_headlines = []

    for press_name, oid in PRESS_OIDS.items():
        articles = crawl_press_page(press_name, oid, date_str)
        all_headlines.extend(articles)
        time.sleep(REQUEST_DELAY)

    # JSON 저장
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"headlines_{date_str}.json"

    result = {
        "date": date_display,
        "crawled_at": (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%dT%H:%M:%S+09:00'),
        "total": len(all_headlines),
        "headlines": all_headlines,
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n총 {len(all_headlines)}개 기사 → {output_file}")


if __name__ == "__main__":
    main()
