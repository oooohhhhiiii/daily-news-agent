"""더벨 뉴스를 별도 Telegram 봇으로 HTML 파일 첨부 전송"""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from html_generator import generate_thebell_html

ENV_PATH = Path(__file__).parent / ".env"


def load_env():
    """환경 변수 로드"""
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()
    return env


def send_document(file_path, bot_token, chat_id, caption=None):
    """Telegram 파일 첨부 전송 (sendDocument API)"""
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    with open(file_path, 'rb') as f:
        files = {'document': (Path(file_path).name, f, 'text/html')}
        data = {'chat_id': chat_id}
        if caption:
            data['caption'] = caption
        response = requests.post(url, data=data, files=files)

    if response.status_code == 200:
        print(f"Document 전송 성공: {file_path}")
        return True
    else:
        print(f"Document 전송 실패: {response.status_code} {response.text}")
        return False



def main():
    env = load_env()
    bot_token = env.get('THEBELL_TELEGRAM_BOT_TOKEN')
    chat_id = env.get('THEBELL_TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("THEBELL_TELEGRAM_BOT_TOKEN 또는 THEBELL_TELEGRAM_CHAT_ID가 .env에 없습니다.")
        sys.exit(1)

    # --document 모드: 미리 생성된 HTML 파일을 직접 전송
    if len(sys.argv) >= 3 and sys.argv[1] == '--document':
        file_path = Path(sys.argv[2])
        if not file_path.exists():
            print(f"파일 없음: {file_path}")
            sys.exit(1)
        caption = sys.argv[3] if len(sys.argv) > 3 else None
        send_document(file_path, bot_token, chat_id, caption)
        return

    # 기본 모드: JSON에서 직접 HTML 생성 후 전송
    kst_now = datetime.utcnow() + timedelta(hours=9)
    yesterday = kst_now - timedelta(days=1)
    date_str = yesterday.strftime('%Y%m%d')
    date_display = yesterday.strftime('%Y-%m-%d')

    output_dir = Path(__file__).parent / "output"
    input_file = output_dir / f"thebell_{date_str}.json"

    if not input_file.exists():
        print(f"파일 없음: {input_file}")
        print("먼저 python crawl_thebell.py 를 실행하세요.")
        sys.exit(1)

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    headlines = data.get("headlines", [])
    if not headlines:
        print("전날 더벨 기사가 없습니다. 알림 전송 중...")
        msg = f"📰 더벨 뉴스 브리핑 ({date_display})\n\n오늘은 더벨 기사가 없습니다."
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        resp = requests.post(url, data={'chat_id': chat_id, 'text': msg})
        if resp.status_code == 200:
            print("알림 전송 완료")
        else:
            print(f"알림 전송 실패: {resp.status_code} {resp.text}")
        sys.exit(0)

    # 카테고리별 그룹핑
    articles_by_category = defaultdict(list)
    for article in headlines:
        category = article.get("thebell_category", "기타")
        articles_by_category[category].append(article)

    # 카테고리별 HTML 생성 및 전송
    print(f"더벨 기사 {len(headlines)}개, {len(articles_by_category)}개 카테고리 전송 시작")

    for category, articles in articles_by_category.items():
        html_content = generate_thebell_html(category, date_display, articles)
        date_short = yesterday.strftime('%y%m%d')
        html_file = output_dir / f"TheBell_{category}_{date_short}.html"
        html_file.write_text(html_content, encoding="utf-8")

        caption = f"📰 더벨 {category} ({date_display})"
        send_document(html_file, bot_token, chat_id, caption)

    print("더벨 뉴스레터 전송 완료")


if __name__ == "__main__":
    main()
