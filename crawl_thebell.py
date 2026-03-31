"""더벨(TheBell) 전날 무료 공개 기사 크롤링 - 제목+본문요약 수집"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from config import HEADERS, REQUEST_DELAY

THEBELL_BASE_URL = "https://www.thebell.co.kr/front/NewsList.asp"
THEBELL_CATEGORIES = {
    "Deal": "0100",
    "금융": "0200",
    "투자": "0300",
    "산업": "0400",
}

# 무료 공개 기사 없이 연속 N페이지면 해당 카테고리 종료
MAX_EMPTY_PAGES = 5
# 게시일이 target_date보다 이 일수 이상 오래되면 종료
MAX_DAYS_BACK = 14


def get_yesterday_date_kst():
    """KST(UTC+9) 기준 전날 날짜 반환"""
    kst_now = datetime.utcnow() + timedelta(hours=9)
    yesterday = kst_now - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d'), yesterday.strftime('%Y%m%d')


def fetch_article_detail(url):
    """무료 기사 상세 페이지에서 무료 공개일과 본문 추출

    Returns:
        (free_date, summary) or (None, None) if not a free article
        free_date: 'YYYY-MM-DD' 형식
        summary: 본문 앞부분 요약 (2~3문장)
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"    상세 페이지 접속 실패: {e}")
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')

    # 무료 공개일 추출: "이 기사는 YYYY년 MM월 DD일 HH:MM에 무료로 공개된 기사입니다"
    free_date = None
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        match = re.search(r'이 기사는\s*(\d{4})년\s*(\d{2})월\s*(\d{2})일\s*\d{2}:\d{2}에\s*무료로 공개된 기사입니다', text)
        if match:
            free_date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
            break

    if not free_date:
        return None, None

    # 본문 추출: div.viewSection 내 p 태그들
    summary = ""
    view_section = soup.find('div', class_='viewSection')
    if view_section:
        paragraphs = []
        for p in view_section.find_all('p'):
            text = p.get_text(strip=True)
            # 무료 공개 안내 문구, 빈 문단, 기자 이메일 등 제외
            if not text:
                continue
            if '무료로 공개된 기사입니다' in text:
                continue
            if re.match(r'^[\w.-]+@[\w.-]+\.\w+$', text):
                continue
            if len(text) < 10:
                continue
            paragraphs.append(text)

        # 앞부분 2~3문장으로 요약
        if paragraphs:
            combined = ' '.join(paragraphs[:3])
            if len(combined) > 200:
                combined = combined[:200] + '...'
            summary = combined

    return free_date, summary


def crawl_category(category_name, code, target_date):
    """특정 카테고리에서 전날 무료 공개된 기사 수집"""
    articles = []
    page = 1
    empty_pages = 0
    cutoff_date = (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=MAX_DAYS_BACK)).strftime('%Y-%m-%d')

    while True:
        url = f"{THEBELL_BASE_URL}?Code={code}&page={page}"
        print(f"  [{category_name}] page {page}: {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"  [{category_name}] 페이지 접속 실패: {e}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        listbox = soup.find("div", class_="listBox")

        if not listbox:
            print(f"  [{category_name}] listBox 없음")
            break

        li_list = listbox.find_all("li")
        if not li_list:
            print(f"  [{category_name}] 기사 목록 없음")
            break

        found_any_free = False   # 페이지에서 time_icon 기사 존재 여부 (날짜 무관)
        oldest_date_on_page = None

        for li in li_list:
            # 날짜 추출
            date_tag = li.find("span", class_="date")
            if not date_tag:
                continue
            date_text = date_tag.get_text(strip=True)
            date_match = re.match(r'(\d{4}-\d{2}-\d{2})', date_text)
            if not date_match:
                continue

            article_date = date_match.group(1)
            oldest_date_on_page = article_date

            # cutoff 이전 기사면 스킵 (종료 판단용으로만 기록)
            if article_date < cutoff_date:
                continue

            # 무료 기사 여부 확인: time_icon.png 이미지 존재 여부
            a_tag = li.find("a", href=re.compile(r"newsview\.asp"))
            if not a_tag:
                continue

            is_free = False
            for img in li.find_all("img"):
                src = img.get("src", "")
                if "time_icon" in src:
                    is_free = True
                    break

            if not is_free:
                continue

            found_any_free = True

            # 무료 기사 발견 → 상세 페이지에서 공개일 확인
            href = a_tag.get("href", "")
            link = "https://www.thebell.co.kr" + href if href.startswith("/") else href

            # 기사 key 추출 (중복 제거용)
            key_match = re.search(r'key=(\d+)', href)
            article_key = key_match.group(1) if key_match else href

            # 제목 추출
            dt_tags = a_tag.find_all("dt")
            title = ""
            for dt in dt_tags:
                if "photo" not in (dt.get("class") or []):
                    title = dt.get_text(strip=True)
                    break
            if not title or len(title) < 5:
                continue

            # 기자명 추출
            reporter_tag = li.find("span", class_="user")
            journalist = reporter_tag.get_text(strip=True).replace('\xa0', ' ') if reporter_tag else ""

            # 목록 페이지의 요약 (fallback용)
            dd_tag = a_tag.find("dd")
            list_summary = dd_tag.get_text(strip=True) if dd_tag else ""

            print(f"    무료 기사 발견: {title[:40]}...")
            time.sleep(REQUEST_DELAY)

            # 상세 페이지에서 무료 공개일 및 본문 추출
            free_date, detail_summary = fetch_article_detail(link)

            if not free_date:
                print(f"    -> 무료 공개일 확인 불가, 스킵")
                continue

            if free_date != target_date:
                print(f"    -> 공개일 {free_date} (대상: {target_date}), 스킵")
                continue

            summary = detail_summary if detail_summary else list_summary

            articles.append({
                "press": "더벨",
                "title": title,
                "link": link,
                "summary": summary,
                "journalist": journalist,
                "date": date_text,
                "free_date": free_date,
                "thebell_category": category_name,
                "_key": article_key,
            })
            print(f"    -> 수집 완료 (공개일: {free_date})")

        # 종료 조건 체크
        if oldest_date_on_page and oldest_date_on_page < cutoff_date:
            print(f"  [{category_name}] cutoff 도달 ({oldest_date_on_page} < {cutoff_date})")
            break

        if found_any_free:
            empty_pages = 0
        else:
            empty_pages += 1
            if empty_pages >= MAX_EMPTY_PAGES:
                print(f"  [{category_name}] 연속 {MAX_EMPTY_PAGES}페이지 무료 기사 없음, 종료")
                break

        page += 1
        time.sleep(REQUEST_DELAY)

    print(f"  [{category_name}] {len(articles)}개 무료 공개 기사 수집")
    return articles


def main():
    target_date, date_str = get_yesterday_date_kst()
    print(f"수집 대상: {target_date}에 무료 공개된 기사 (KST 기준 전날)")

    all_articles = []
    seen_keys = set()

    for category_name, code in THEBELL_CATEGORIES.items():
        articles = crawl_category(category_name, code, target_date)
        for article in articles:
            key = article["_key"]
            if key not in seen_keys:
                seen_keys.add(key)
                article_clean = {k: v for k, v in article.items() if k != "_key"}
                all_articles.append(article_clean)
        time.sleep(REQUEST_DELAY)

    # JSON 저장
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"thebell_{date_str}.json"

    result = {
        "date": target_date,
        "crawled_at": (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%dT%H:%M:%S+09:00'),
        "source": "thebell",
        "total": len(all_articles),
        "headlines": all_articles,
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n총 {len(all_articles)}개 무료 공개 기사 → {output_file}")


if __name__ == "__main__":
    main()
