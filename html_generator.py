"""뉴스레터 HTML 파일 생성"""

import sys
import re
import html
from pathlib import Path


def _render_html(title, date, articles, source_label="Daily News Agent"):
    """공통 HTML 렌더링"""
    article_blocks = []
    for i, art in enumerate(articles, 1):
        summary_html = html.escape(art.get("summary", "")).replace("\n", "<br>")
        title_html = html.escape(art["title"])
        link = html.escape(art.get("link", ""))
        journalist = art.get("journalist", "")

        block = f"""      <div style="border-bottom:1px solid #eee; padding:16px 0;">
        <h2 style="margin:0 0 8px; font-size:16px; color:#1a1a2e; line-height:1.4;">{i}. {title_html}</h2>
        <p style="margin:0 0 8px; font-size:14px; color:#444; line-height:1.6;">{summary_html}</p>"""

        if journalist:
            block += f"""
        <p style="margin:0 0 6px; font-size:12px; color:#888;">{html.escape(journalist)}</p>"""

        if link:
            block += f"""
        <a href="{link}" style="font-size:13px; color:#4a90d9; text-decoration:none;">&#128279; 원문 보기</a>"""

        block += """
      </div>"""
        article_blocks.append(block)

    articles_html = "\n".join(article_blocks)
    title_html = html.escape(title)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_html}</title>
</head>
<body style="margin:0; padding:16px; background:#f5f5f5; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Noto Sans KR',sans-serif;">
  <div style="max-width:640px; margin:0 auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
    <div style="background:#1a1a2e; color:#fff; padding:20px 24px;">
      <h1 style="margin:0; font-size:20px;">&#128240; {title_html}</h1>
      <p style="margin:6px 0 0; font-size:14px; color:#aaa;">{html.escape(date)}</p>
    </div>
    <div style="padding:4px 24px 16px;">
{articles_html}
    </div>
    <div style="padding:12px 24px; text-align:center; font-size:12px; color:#999; border-top:1px solid #eee;">
      {html.escape(source_label)}
    </div>
  </div>
</body>
</html>"""


def parse_msg_file(text):
    """기존 msg_*.txt 형식을 파싱하여 (title, date, articles) 반환

    형식:
    📰 카테고리 뉴스 브리핑 (YYYY-MM-DD)

    1. 기사 제목
    [언론사] 요약 텍스트...
    🔗 https://...
    """
    lines = text.strip().split("\n")

    # 첫 줄에서 제목과 날짜 추출
    header = lines[0].strip()
    date_match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", header)
    date = date_match.group(1) if date_match else ""
    # 📰 제거하고 날짜 부분 제거
    title = header.replace("📰", "").strip()
    title = re.sub(r"\s*\(\d{4}-\d{2}-\d{2}\)\s*$", "", title).strip()

    articles = []
    current = None

    for line in lines[1:]:
        line_stripped = line.strip()

        # 번호로 시작하는 줄 = 새 기사
        num_match = re.match(r"^(\d+)\.\s+(.+)$", line_stripped)
        if num_match:
            if current:
                articles.append(current)
            current = {"title": num_match.group(2), "summary": "", "link": ""}
            continue

        # 링크 줄
        if line_stripped.startswith("🔗"):
            if current:
                current["link"] = line_stripped.replace("🔗", "").strip()
            continue

        # 빈 줄 무시
        if not line_stripped:
            continue

        # 그 외 = 요약 텍스트
        if current:
            if current["summary"]:
                current["summary"] += "\n" + line_stripped
            else:
                current["summary"] = line_stripped

    if current:
        articles.append(current)

    return title, date, articles


def generate_newsletter_html(category, date, articles):
    """메인 뉴스레터 HTML 생성"""
    title = f"{category} 뉴스 브리핑"
    return _render_html(title, date, articles)


def generate_thebell_html(category, date, articles):
    """더벨 뉴스레터 HTML 생성"""
    title = f"더벨 {category}"
    return _render_html(title, date, articles, source_label="더벨 (TheBell)")


def main():
    if len(sys.argv) < 5:
        print("Usage: python html_generator.py --input msg.txt --output msg.html")
        sys.exit(1)

    input_path = None
    output_path = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--input" and i + 1 < len(args):
            input_path = Path(args[i + 1])
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_path = Path(args[i + 1])
            i += 2
        else:
            i += 1

    if not input_path or not output_path:
        print("--input 과 --output 을 모두 지정하세요.")
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8")
    title, date, articles = parse_msg_file(text)

    if not articles:
        print("파싱된 기사가 없습니다.")
        sys.exit(1)

    html_content = _render_html(title, date, articles)
    output_path.write_text(html_content, encoding="utf-8")
    print(f"HTML 생성 완료: {output_path} ({len(articles)}개 기사)")


if __name__ == "__main__":
    main()
