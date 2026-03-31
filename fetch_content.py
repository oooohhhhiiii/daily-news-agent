"""Stage 2: 선별된 기사의 본문 수집"""

import requests
from bs4 import BeautifulSoup
import json
import sys
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from config import HEADERS, REQUEST_DELAY


def get_article_content(url):
    """네이버 뉴스 기사 본문 추출 (inspect_naver.py 기반)"""
    try:
        time.sleep(REQUEST_DELAY)
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        # JS 리다이렉트 처리
        if "top.location.href" in response.text:
            match = re.search(r"top\.location\.href='(.*?)';", response.text)
            if match:
                return get_article_content(match.group(1))

        soup = BeautifulSoup(response.text, 'html.parser')

        # 본문 추출 (여러 셀렉터 시도)
        content = soup.select_one('#dic_area')
        if not content:
            content = soup.select_one('#articeBody')
        if not content:
            content = soup.select_one('.news_end')
        if not content:
            content = soup.select_one('.articleCont')

        if content:
            text = content.get_text(strip=True)
            # 본문 500자 제한 (Claude 요약용으로 충분)
            return text[:500] if len(text) > 500 else text

        return ""
    except Exception as e:
        print(f"  본문 수집 실패 [{url}]: {e}")
        return ""


def main():
    # URL 목록을 인자로 받음
    if len(sys.argv) < 2:
        print("Usage: python fetch_content.py --urls 'url1,url2,...'")
        sys.exit(1)

    if sys.argv[1] == '--urls':
        urls = sys.argv[2].split(',')
    elif sys.argv[1] == '--file':
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            data = json.load(f)
            urls = [a['link'] for a in data]
    else:
        print("Usage: python fetch_content.py --urls 'url1,url2,...'")
        print("       python fetch_content.py --file selected.json")
        sys.exit(1)

    urls = [u.strip() for u in urls if u.strip()]
    print(f"총 {len(urls)}개 기사 본문 수집 시작...")

    articles = []
    for i, url in enumerate(urls, 1):
        print(f"  [{i}/{len(urls)}] {url[:60]}...")
        content = get_article_content(url)
        articles.append({
            "link": url,
            "content": content,
        })

    # JSON 저장
    date_str = (datetime.utcnow() + timedelta(hours=9) - timedelta(days=1)).strftime('%Y%m%d')
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"articles_{date_str}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"articles": articles}, f, ensure_ascii=False, indent=2)

    print(f"\n{len(articles)}개 기사 본문 → {output_file}")


if __name__ == "__main__":
    main()
