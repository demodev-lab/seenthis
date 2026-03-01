import json
import os
import requests
from bs4 import BeautifulSoup

BOARDS = {
    "kstartup": "https://seenthis.kr/kstartup",
    "bizinfo": "https://seenthis.kr/bizinfo",
}

SEEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen_posts.json")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
CONTENT_MAX_LEN = 200
SEEN_MAX_PER_BOARD = 200
PAGES_PER_BOARD = 3

BOARD_LABELS = {
    "kstartup": "스타트업 지원사업",
    "bizinfo": "정부 지원사업",
}


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {"kstartup": [], "bizinfo": []}
        return data
    return {"kstartup": [], "bizinfo": []}


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)


def crawl_board(board_name, url):
    posts = []
    seen_urls = set()
    for page in range(1, PAGES_PER_BOARD + 1):
        page_url = f"{url}?page={page}"
        resp = requests.get(page_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for row in soup.select(".bl-list"):
            if "bl-notice" in row.get("class", []):
                continue
            link_tag = row.select_one(".bl-subj a")
            if not link_tag:
                continue
            href = link_tag.get("href", "")
            if not href.startswith("http"):
                href = f"https://seenthis.kr{href}"
            href = href.split("?")[0]
            if href in seen_urls:
                continue
            seen_urls.add(href)
            title = link_tag.get_text(strip=True)
            posts.append({"board": board_name, "title": title, "url": href})
    return posts


def fetch_content(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        con = soup.select_one(".board-view-con")
        if not con:
            return ""
        text = con.get_text(separator=" ", strip=True)
        if len(text) > CONTENT_MAX_LEN:
            text = text[:CONTENT_MAX_LEN] + "..."
        return text
    except Exception as e:
        print(f"[WARN] Failed to fetch content: {url} ({e})")
        return ""


def send_slack(posts):
    if not SLACK_WEBHOOK_URL:
        print("[SKIP] SLACK_WEBHOOK_URL not set")
        return

    for post in posts:
        label = BOARD_LABELS.get(post["board"], post["board"])
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*[{label}]*\n<{post['url']}|{post['title']}>",
                },
            },
        ]
        if post.get("content"):
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": post["content"]},
                    ],
                }
            )
        payload = {
            "text": f"[{label}] {post['title']}",
            "blocks": blocks,
        }
        resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        if resp.status_code != 200:
            print(f"[ERROR] Slack send failed ({resp.status_code}): {resp.text}")
        else:
            print(f"[SENT] {post['title']}")


def main():
    seen = load_seen()
    new_posts = []

    for board_name, url in BOARDS.items():
        print(f"[CRAWL] {board_name}: {url}")
        posts = crawl_board(board_name, url)
        print(f"  Found {len(posts)} posts")
        board_seen = seen.get(board_name, [])
        for post in posts:
            if post["url"] not in board_seen:
                new_posts.append(post)

    print(f"\nNew posts: {len(new_posts)}")

    if new_posts:
        for post in new_posts:
            print(f"[FETCH] {post['url']}")
            post["content"] = fetch_content(post["url"])

        send_slack(new_posts)

        for post in new_posts:
            board_name = post["board"]
            if board_name not in seen:
                seen[board_name] = []
            seen[board_name].append(post["url"])
        for board_name in seen:
            seen[board_name] = seen[board_name][-SEEN_MAX_PER_BOARD:]
        save_seen(seen)
        print("seen_posts.json updated")
    else:
        print("No new posts")


if __name__ == "__main__":
    main()
