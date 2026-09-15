import streamlit as st
import requests,re,time,io,zipfile
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse,urldefrag
from urllib.robotparser import RobotFileParser
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="01 Brand Text Collector",layout="wide")

BRAND_KEYS=["about","brand","story","our-story","philosophy","mission","vision","values","heritage","identity","concept","purpose",
"소개","브랜드","스토리","철학","미션","비전","가치","정체성"]
EXCLUDE_KEYS=["product","products","shop","store","collection","ingredient","ingredients","review","reviews","news","press","event","faq",
"login","account","cart","checkout","privacy","terms","제품","상품","성분","효능","사용법","리뷰","뉴스","이벤트","장바구니","로그인","개인정보","약관"]
PRODUCT_TERMS=["제품","성분","효능","사용법","ingredient","ingredients","formula","formulation","clinical","dermatologist","피부과","전문의",
"스킨케어","토너","세럼","앰플","선크림","spf","product","products"]
UI_TERMS=["visit and follow us","brand core value","learn more","shop now","view more","discover more"]
UA="AcademicBrandTextCollector/2.0 (+research-use)";HEADERS={"User-Agent":UA}

def clean(u):return urldefrag(u)[0].rstrip("/")
def domain(u):return urlparse(u).netloc.lower().replace("www.","")
def robots_ok(u):
    try:
        p=urlparse(u);rp=RobotFileParser();rp.set_url(f"{p.scheme}://{p.netloc}/robots.txt");rp.read();return rp.can_fetch(UA,u)
    except:return True
def fetch(u):
    if not robots_ok(u):raise PermissionError("robots.txt에서 자동수집을 허용하지 않습니다.")
    r=requests.get(u,headers=HEADERS,timeout=15,allow_redirects=True);r.raise_for_status()
    if "text/html" not in r.headers.get("content-type",""):return None,"",r.url
    s=BeautifulSoup(r.text,"html.parser");title=s.title.get_text(" ",strip=True) if s.title else ""
    return s,title,r.url

def infer_brand(soup,title,url):
    # og:site_name → title → domain 순으로 자동 추정
    og=soup.find("meta",attrs={"property":"og:site_name"}) if soup else None
    candidates=[og.get("content","").strip() if og else "", title.split("|")[0].strip(), title.split("-")[0].strip()]
    for c in candidates:
        if c and 1<len(c)<60:return c
    host=domain(url).split(".")[0]
    return host.replace("-"," ").replace("_"," ").strip().title()

def ptype(u,title="",anchor=""):
    h=f"{u} {title} {anchor}".lower()
    mp=[("Philosophy",["philosophy","철학"]),("Mission",["mission","미션"]),("Vision",["vision","비전"]),
        ("Values",["values","가치"]),("Brand Story",["story","스토리"]),("Heritage",["heritage"]),
        ("About",["about","소개"]),("Brand",["brand","브랜드","identity","정체성","purpose","concept"])]
    for lab,ks in mp:
        if any(k in h for k in ks):return lab
    return "Homepage"
def candidate(u,t=""):
    h=f"{u} {t}".lower()
    return not any(k in h for k in EXCLUDE_KEYS) and any(k in h for k in BRAND_KEYS)
def extract(s):
    for tag in s(["script","style","noscript","svg","form"]):tag.decompose()
    for sel in ["nav","footer"]:
        for x in s.select(sel):x.decompose()
    root=s.find("main") or s.find("article") or s.body or s
    out=[];seen=set()
    for e in root.find_all(["h1","h2","h3","h4","p","li","blockquote"]):
        t=re.sub(r"\s+"," "," ".join(e.stripped_strings)).strip()
        if len(t)>=15 and t.casefold() not in seen:seen.add(t.casefold());out.append(t)
    return "\n".join(out)
def split_units(text):
    blocks=[re.sub(r"[ \t]+"," ",x).strip() for x in re.split(r"\n+",str(text)) if x.strip()]
    out=[]
    for b in blocks:
        parts=[b] if len(b)<=280 else re.split(r"(?<=[.!?。！？])\s+|(?<=다\.)\s+",b)
        out.extend([re.sub(r"\s+"," ",p).strip() for p in parts if len(p.strip())>=15])
    return list(dict.fromkeys(out))

def crawl_site(url,max_pages=15):
    if not url.startswith(("http://","https://")):url="https://"+url
    soup,title,final=fetch(url);brand=infer_brand(soup,title,final)
    found={clean(final):("Homepage",title)}
    for a in soup.find_all("a",href=True):
        u=clean(urljoin(final,a["href"]));txt=a.get_text(" ",strip=True)
        if u.startswith(("http://","https://")) and domain(u)==domain(final) and candidate(u,txt):
            found[u]=(ptype(u,anchor=txt),txt)
    rows=[];day=datetime.now().strftime("%Y-%m-%d")
    for i,(u,(_,anchor)) in enumerate(list(found.items())[:max_pages],1):
        try:
            s,t,fu=fetch(u);txt=extract(s)
            if len(txt)<50:continue
            # 페이지 자동판정: 명확한 브랜드 페이지=1, 홈페이지/불명확=0
            pt=ptype(fu,t,anchor);auto=1 if pt!="Homepage" else 0
            rows.append({"Brand":brand,"Page_ID":f"P{i:03d}","Page_Type":pt,"Page_Title":t,"Source_URL":fu,
                         "Collection_Date":day,"Original_Text":txt,"Auto_Include":auto,"Researcher_Final":auto,"Researcher_Note":""})
            time.sleep(.1)
        except Exception as e:
            rows.append({"Brand":brand,"Page_ID":f"P{i:03d}","Page_Type":"ERROR","Page_Title":"","Source_URL":u,
                         "Collection_Date":day,"Original_Text":"","Auto_Include":0,"Researcher_Final":0,"Researcher_Note":str(e)})
    return brand,pd.DataFrame(rows)

def unit_table(pages):
    rows=[];cnt={}
    approved=pages[pd.to_numeric(pages.Researcher_Final,errors="coerce").fillna(0).astype(int)==1]
    for _,r in approved.iterrows():
        b=r.Brand;cnt.setdefault(b,0)
        for t in split_units(r.Original_Text):
            cnt[b]+=1;tl=t.lower()
            if len(t)<35 or any(x in tl for x in UI_TERMS):cat,auto,why="UI/Heading",0,"UI/섹션 제목 후보"
            elif any(x in tl for x in PRODUCT_TERMS):cat,auto,why="Product/Functional",0,"제품·기능 관련 후보"
            else:cat,auto,why="Brand",1,"브랜드 정체성·철학·가치 후보"
            rows.append({"Brand":b,"Unit_ID":f"{b}_U{cnt[b]:03d}","Page_ID":r.Page_ID,"Source_URL":r.Source_URL,
                         "Text":t,"Auto_Category":cat,"Auto_Include":auto,"Researcher_Final":auto,
                         "Review_Reason":why,"Researcher_Note":""})
    return pd.DataFrame(rows)

st.title("01 Brand Text Collector · v2.0")
st.caption("URL만 추가 → 브랜드명 자동인식 → 크롤링 → 자동 1/0 → 연구자 수정 → 다중 브랜드 통합 CSV")

if "brands" not in st.session_state:st.session_state.brands={}

with st.form("add"):
    url=st.text_input("공식 웹사이트 주소",placeholder="https://...")
    submitted=st.form_submit_button("브랜드 추가 및 크롤링",type="primary")
if submitted and url:
    try:
        with st.spinner("브랜드명 인식 및 공식 브랜드 페이지 수집 중..."):
            brand,pages=crawl_site(url)
        st.session_state.brands[brand]={"pages":pages}
        st.success(f"{brand} 추가 완료")
    except Exception as e:st.error(f"수집 실패: {e}")

if st.session_state.brands:
    st.subheader("수집 브랜드")
    st.write(" · ".join(st.session_state.brands.keys()))
    selected=st.selectbox("검토할 브랜드",list(st.session_state.brands.keys()))
    pages=st.session_state.brands[selected]["pages"]

    st.subheader("1. 페이지 연구자 확인")
    ep=st.data_editor(pages,disabled=[c for c in pages if c not in ["Researcher_Final","Researcher_Note"]],
        column_config={"Researcher_Final":st.column_config.SelectboxColumn(options=[1,0],required=True)},
        use_container_width=True,height=360,key=f"page_{selected}")
    st.session_state.brands[selected]["pages"]=ep

    units=unit_table(ep)
    st.subheader("2. Content Unit 연구자 확인")
    if len(units):
        eu=st.data_editor(units,disabled=[c for c in units if c not in ["Researcher_Final","Researcher_Note"]],
            column_config={"Researcher_Final":st.column_config.SelectboxColumn(options=[1,0],required=True)},
            use_container_width=True,height=420,key=f"unit_{selected}")
        st.session_state.brands[selected]["units"]=eu

    # integrated summary
    all_pages=[];all_units=[]
    for b,v in st.session_state.brands.items():
        all_pages.append(v["pages"])
        if "units" in v:all_units.append(v["units"])
    P=pd.concat(all_pages,ignore_index=True) if all_pages else pd.DataFrame()
    U=pd.concat(all_units,ignore_index=True) if all_units else pd.DataFrame()

    st.divider();st.header("연구자 확인 현황")
    if len(U):
        au=U[pd.to_numeric(U.Researcher_Final,errors="coerce").fillna(0).astype(int)==1].copy()
        au["Word_Count"]=au.Text.astype(str).str.split().str.len();au["Character_Count"]=au.Text.astype(str).str.len()
        summary=au.groupby("Brand").agg(Approved_Units=("Unit_ID","count"),Words=("Word_Count","sum"),
                                        Characters=("Character_Count","sum")).reset_index()
        pp=P[pd.to_numeric(P.Researcher_Final,errors="coerce").fillna(0).astype(int)==1].groupby("Brand").size()
        summary["Approved_Pages"]=summary.Brand.map(pp).fillna(0).astype(int)
        st.dataframe(summary,use_container_width=True,hide_index=True)

        st.header("최종 통합 다운로드")
        st.caption("모든 브랜드의 연구자 승인 Unit을 하나의 CSV로 통합합니다. 이 파일을 02 분석기의 입력자료로 사용할 수 있습니다.")
        final=au[["Brand","Unit_ID","Page_ID","Source_URL","Text","Word_Count","Character_Count",
                  "Auto_Category","Researcher_Final","Researcher_Note"]].copy()
        st.download_button("모든 브랜드 최종 승인 CSV 다운로드",final.to_csv(index=False).encode("utf-8-sig"),
                           "01_all_brands_approved_units.csv","text/csv")
        st.download_button("전체 페이지 검토기록 CSV",P.to_csv(index=False).encode("utf-8-sig"),
                           "01_all_brands_page_review.csv","text/csv")
        st.download_button("전체 Unit 검토기록 CSV",U.to_csv(index=False).encode("utf-8-sig"),
                           "01_all_brands_unit_review.csv","text/csv")
