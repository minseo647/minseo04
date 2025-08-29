
import json
import time
from datetime import datetime
import feedparser
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import requests
from bs4 import BeautifulSoup

# news_collector.py에서 가져온 피드 목록
FEEDS = [
    # --- Korea (ko) ---
    {"feed_url": "https://it.donga.com/feeds/rss/",            "source": "IT동아",              "category": "IT",           "lang": "ko"},
    {"feed_url": "https://rss.etnews.com/Section902.xml",      "source": "전자신문_속보",         "category": "IT",           "lang": "ko"},
    {"feed_url": "https://rss.etnews.com/Section901.xml",      "source": "전자신문_오늘의뉴스",     "category": "IT",           "lang": "ko"},
    {"feed_url": "https://zdnet.co.kr/news/news_xml.asp",      "source": "ZDNet Korea",         "category": "IT",           "lang": "ko"},
    {"feed_url": "https://www.itworld.co.kr/rss/all.xml",      "source": "ITWorld Korea",       "category": "IT",           "lang": "ko"},
    {"feed_url": "https://www.ciokorea.com/rss/all.xml",       "source": "CIO Korea",           "category": "IT",           "lang": "ko"},
    {"feed_url": "https://www.bloter.net/feed",                "source": "Bloter",              "category": "IT",           "lang": "ko"},
    {"feed_url": "https://byline.network/feed/",               "source": "Byline Network",      "category": "IT",           "lang": "ko"},
    {"feed_url": "https://platum.kr/feed",                     "source": "Platum",              "category": "Startup",      "lang": "ko"},
    {"feed_url": "https://www.boannews.com/media/news_rss.xml","source": "보안뉴스",             "category": "Security",     "lang": "ko"},
    {"feed_url": "https://it.chosun.com/rss.xml",              "source": "IT조선",              "category": "IT",           "lang": "ko"},
    {"feed_url": "https://www.ddaily.co.kr/news_rss.php",      "source": "디지털데일리",           "category": "IT",           "lang": "ko"},
    {"feed_url": "https://www.kbench.com/rss.xml",             "source": "KBench",              "category": "IT",           "lang": "ko"},
    {"feed_url": "https://www.sedaily.com/rss/IT.xml",         "source": "서울경제 IT",           "category": "IT",           "lang": "ko"},
    {"feed_url": "https://www.hankyung.com/feed/it",           "source": "한국경제 IT",            "category": "IT",           "lang": "ko"},

    # --- Global (en) ---
    {"feed_url": "https://techcrunch.com/feed/",               "source": "TechCrunch",          "category": "Tech",         "lang": "en"},
    {"feed_url": "https://www.eetimes.com/feed/",              "source": "EE Times",            "category": "Electronics",  "lang": "en"},
    {"feed_url": "https://spectrum.ieee.org/rss/fulltext",     "source": "IEEE Spectrum",       "category": "Engineering",  "lang": "en"},
    {"feed_url": "http://export.arxiv.org/rss/cs",             "source": "arXiv CS",            "category": "Research",     "lang": "en"},
    {"feed_url": "https://www.nature.com/nel/atom.xml",        "source": "Nature Electronics",  "category": "Research",     "lang": "en"},
    {"feed_url": "https://www.technologyreview.com/feed/",     "source": "MIT Tech Review",     "category": "Tech",         "lang": "en"},
    {"feed_url": "https://www.theverge.com/rss/index.xml",     "source": "The Verge",           "category": "Tech",         "lang": "en"},
    {"feed_url": "https://www.wired.com/feed/rss",             "source": "WIRED",               "category": "Tech",         "lang": "en"},
    {"feed_url": "https://www.engadget.com/rss.xml",           "source": "Engadget",            "category": "Tech",         "lang": "en"},
    {"feed_url": "https://venturebeat.com/category/ai/feed/",  "source": "VentureBeat AI",      "category": "AI",           "lang": "en"},
]

# --- 웹 스크래핑을 위한 설정 ---
HEADERS = {"User-Agent": "Mozilla/5.0 (NewsAgent/1.0)"}
SESSION = requests.Session()
ADAPTER = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=1)
SESSION.mount("http://", ADAPTER)
SESSION.mount("https://", ADAPTER)
CONNECT_TIMEOUT = 6.0
READ_TIMEOUT = 10.0

def extract_main_text(url: str) -> str:
    try:
        r = SESSION.get(url, headers=HEADERS, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        art = soup.find("article")
        if art and art.get_text(strip=True):
            return art.get_text("\n", strip=True)
        candidates = soup.select(
            "div[id*='content'], div[class*='content'], "
            "div[id*='article'], div[class*='article'], "
            "section[id*='content'], section[class*='content'], "
            "div[id*='news'], div[class*='news']"
        )
        best = max((c for c in candidates), key=lambda c: len(c.get_text(strip=True)), default=None)
        if best and len(best.get_text(strip=True)) > 200:
            return best.get_text("\n", strip=True)
        md = soup.find("meta", attrs={"name":"description"}) or soup.find("meta", attrs={"property":"og:description"})
        if md and md.get("content"):
            return md["content"]
    except Exception:
        pass
    return ""

def struct_time_to_datetime(st):
    if st is None:
        return None
    return datetime.fromtimestamp(time.mktime(st))

def canonicalize_link(url: str) -> str:
    try:
        u = urlparse(url)
        scheme = (u.scheme or "https").lower()
        netloc = (u.netloc or "").lower()
        path = (u.path or "").rstrip("/")
        drop = {"utm_source","utm_medium","utm_campaign","utm_term","utm_content","utm_id","utm_name",
                "gclid","fbclid","igshid","spm","ref","ref_src","cmpid"}
        qs = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True) if k.lower() not in drop]
        query = urlencode(qs, doseq=True)
        return urlunparse((scheme, netloc, path, u.params, query, ""))
    except Exception:
        return url

def expand_paged_feed_urls(feed_url: str, pages: int) -> list[str]:
    urls = [feed_url]
    if re.search(r"/feed/?$", feed_url, re.IGNORECASE):
        for i in range(2, max(2, pages + 1)):
            sep = "&" if "?" in feed_url else "?"
            urls.append(f"{feed_url}{sep}paged={i}")
    return urls

START_DATE = datetime(2024, 8, 29)
END_DATE = datetime(2025, 8, 29, 23, 59, 59)

def fetch_historical_news_for_feed(feed_info):
    feed_url = feed_info["feed_url"]
    source = feed_info["source"]
    
    urls = expand_paged_feed_urls(feed_url, pages=50)
    
    print(f"Fetching {source} with {len(urls)} pages...")
    
    articles_for_feed = []
    
    for url in urls:
        try:
            feed = feedparser.parse(url)
            if not hasattr(feed, "entries"):
                continue
            
            for entry in feed.entries:
                published_dt = struct_time_to_datetime(getattr(entry, 'published_parsed', None))
                
                if published_dt and START_DATE <= published_dt <= END_DATE:
                    title = getattr(entry, "title", "").strip()
                    link = canonicalize_link(getattr(entry, "link", "").strip())

                    if not title or not link:
                        continue

                    summary = getattr(entry, "summary", "")
                    
                    # 본문 스크래핑
                    raw_text = extract_main_text(link)

                    articles_for_feed.append({
                        "title": title,
                        "link": link,
                        "published": published_dt.strftime('%Y-%m-%d %H:%M:%S'),
                        "source": source,
                        "summary": summary,
                        "raw_text": raw_text
                    })
        except Exception as e:
            print(f"  Error processing {url}: {e}")
            
    return articles_for_feed

if __name__ == "__main__":
    all_historical_articles = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_feed = {executor.submit(fetch_historical_news_for_feed, feed): feed for feed in FEEDS}
        for future in as_completed(future_to_feed):
            feed = future_to_feed[future]
            try:
                articles = future.result()
                print(f"  -> Found {len(articles)} articles for {feed['source']} in the date range.")
                all_historical_articles.extend(articles)
            except Exception as exc:
                print(f"{feed['source']} generated an exception: {exc}")

    print(f"\nTotal articles collected: {len(all_historical_articles)}")

    seen_links = set()
    unique_articles = []
    for article in all_historical_articles:
        if article['link'] not in seen_links:
            unique_articles.append(article)
            seen_links.add(article['link'])
            
    print(f"Total unique articles: {len(unique_articles)}")

    unique_articles.sort(key=lambda x: x['published'], reverse=True)

    output_filename = 'news_data_2024_2025.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(unique_articles, f, ensure_ascii=False, indent=2)
        
    print(f"\nSuccessfully saved {len(unique_articles)} articles to {output_filename}")
