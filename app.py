import streamlit as st
import requests, re, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Brand Text Collector", page_icon="🔎", layout="wide")

BRAND_KEYWORDS = [
    "about","brand","story","our-story","philosophy","mission","vision","values",
    "heritage","identity","concept","purpose",
    "소개","브랜드","스토리","철학","미션","비전","가치","정체성"
]
EXCLUDE_KEYWORDS = [
    "product","products","shop","store","collection","ingredient","ingredients",
    "review","reviews","news","press","event","faq","login","account","cart",
    "checkout","privacy","terms","product-detail","item",
    "제품","상품","성분","효능","사용법","리뷰","뉴스","이벤트","장바구니",
    "로그인","개인정보","약관"
]
UA = "AcademicBrandTextCollector/1.1 (+research-use)"
HEADERS = {"User-Agent": UA}

def norm_domain(u):
    return urlparse(u).netloc.lower().replace("www.","")

def clean_url(u):
    return urldefrag(u)[0].rstrip("/")

def allowed_by_robots(url):
    try:
        p = urlparse(url)
        robots = f"{p.scheme}://{p.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots)
        rp.read()
        return rp.can_fetch(UA, url)
    except Exception:
        return True

def fetch(url, timeout=15):
    if not allowed_by_robots(url):
        raise PermissionError("robots.txt에서 자동 수집을 허용하지 않습니다.")
    r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    if "text/html" not in r.headers.get("content-type",""):
        return None, "", r.url
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    return soup, title, r.url

def classify(url, title="", anchor=""):
    hay = f"{url} {title} {anchor}".lower()
    if any(k in hay for k in EXCLUDE_KEYWORDS):
        return "Excluded candidate"
    mapping = [
        ("Philosophy", ["philosophy","철학"]),
        ("Mission", ["mission","미션"]),
        ("Vision", ["vision","비전"]),
        ("Values", ["values","가치"]),
        ("Brand Story", ["our-story","story","스토리"]),
        ("Heritage", ["heritage"]),
        ("About", ["about","소개"]),
        ("Brand", ["brand","브랜드","identity","정체성","purpose","concept"]),
    ]
    for label, keys in mapping:
        if any(k in hay for k in keys):
            return label
    return "Homepage"

def candidate(url, text=""):
    hay = f"{url} {text}".lower()
    if any(k in hay for k in EXCLUDE_KEYWORDS):
        return False
    return any(k in hay for k in BRAND_KEYWORDS)

def extract_blocks(soup):
    for tag in soup(["script","style","noscript","svg","form"]):
        tag.decompose()
    for sel in ["nav","footer"]:
        for tag in soup.select(sel):
            tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    blocks, seen = [], set()
    for el in root.find_all(["h1","h2","h3","h4","p","li","blockquote"]):
        txt = re.sub(r"\s+", " ", " ".join(el.stripped_strings)).strip()
        if len(txt) < 15:
            continue
        key = txt.casefold()
        if key not in seen:
            seen.add(key)
            blocks.append(txt)
    return "\n".join(blocks)

def discover(base, max_pages):
    soup, title, final = fetch(base)
    if soup is None:
        return []
    found = {clean_url(final): ("Homepage", title)}
    for a in soup.find_all("a", href=True):
        u = clean_url(urljoin(final, a["href"]))
        txt = a.get_text(" ", strip=True)
        if not u.startswith(("http://","https://")):
            continue
        if norm_domain(u) != norm_domain(final):
            continue
        if candidate(u, txt):
            found[u] = (classify(u, anchor=txt), txt)
    ranked = sorted(found.items(), key=lambda x: (x[1][0] == "Homepage", x[0]))
    return ranked[:max_pages]

def crawl(brand, base, max_pages):
    rows = []
    day = datetime.now().strftime("%Y-%m-%d")
    for i, (url, (_, anchor)) in enumerate(discover(base, max_pages), 1):
        try:
            soup, title, final = fetch(url)
            if soup is None:
                continue
            ptype = classify(final, title, anchor)
            if ptype == "Excluded candidate":
                continue
            text = extract_blocks(soup)
            if len(text) < 50:
                continue
            rows.append({
                "Brand_ID": f"B{i:03d}",
                "Brand": brand,
                "Page_Type": ptype,
                "Page_Title": title,
                "Source_URL": final,
                "Collection_Date": day,
                "Original_Text": text,
                "Include": "",
                "Researcher_Note": ""
            })
            time.sleep(.15)
        except Exception as e:
            rows.append({
                "Brand_ID": f"B{i:03d}", "Brand": brand, "Page_Type": "ERROR",
                "Page_Title": "", "Source_URL": url, "Collection_Date": day,
                "Original_Text": "", "Include": 0,
                "Researcher_Note": f"{type(e).__name__}: {e}"
            })
    return pd.DataFrame(rows)

st.title("Brand Text Collector")
st.caption("K-코스메틱 공식 웹사이트 · 브랜드 관련 텍스트 수집 · 연구자 승인용")

st.markdown("""
**연구 절차:** 공식 URL 입력 → 브랜드 관련 페이지 후보 탐색 → 원문 수집 → CSV 저장 → 연구자 승인  
제품 상세·성분·효능·리뷰·뉴스·이벤트는 분석 범위에서 제외합니다.
""")

a,b = st.columns([1,2])
brand = a.text_input("브랜드명", placeholder="예: d'Alba")
site = b.text_input("공식 사이트 URL", placeholder="https://...")
max_pages = st.slider("최대 페이지 후보 수", 5, 30, 15)

if st.button("수집 시작", type="primary"):
    if not brand.strip() or not site.strip():
        st.error("브랜드명과 공식 URL을 모두 입력하세요.")
    else:
        if not site.startswith(("http://","https://")):
            site = "https://" + site
        try:
            with st.spinner("브랜드 관련 페이지를 확인하고 있습니다..."):
                st.session_state.df = crawl(brand.strip(), site.strip(), max_pages)
        except Exception as e:
            st.error(f"사이트 접근 실패: {type(e).__name__}: {e}")

if "df" in st.session_state:
    df = st.session_state.df
    st.subheader("수집 결과")
    st.metric("수집된 페이지 후보", len(df))
    st.dataframe(df, use_container_width=True, height=430)
    csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    safe = re.sub(r"[^0-9A-Za-z가-힣_-]+","_", brand.strip()) or "brand"
    st.download_button(
        "연구자 검토용 CSV 다운로드",
        csv,
        file_name=f"{safe}_brand_text_review.csv",
        mime="text/csv"
    )
    st.info("CSV의 Include 열에 승인=1, 제외=0을 입력합니다. 승인된 데이터만 후속 분석에 사용합니다.")

st.divider()
st.caption("일부 JavaScript 기반 사이트, 로그인 페이지, robots.txt 제한 사이트는 자동 수집되지 않을 수 있습니다. 자동수집 결과는 반드시 연구자가 원문 URL과 대조해 검토하십시오.")
