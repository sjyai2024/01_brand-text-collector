# Brand Text Collector v1.1 — Web deployment

## Streamlit Community Cloud 배포
1. GitHub에 새 저장소를 만듭니다.
2. 이 폴더의 `app.py`, `requirements.txt`를 저장소 최상위에 업로드합니다.
3. Streamlit Community Cloud에서 **Create app**을 선택합니다.
4. GitHub 저장소를 선택하고 Main file path를 `app.py`로 지정합니다.
5. Deploy를 누르면 웹 주소가 생성됩니다.

## 연구 절차
공식 URL → 브랜드 관련 페이지 후보 → 원문 CSV → 연구자 `Include` 승인 → 후속 분석.

## 범위
수집 후보: About, Brand Story, Philosophy, Mission, Vision, Values, Heritage, Identity 등.
제품 상세, 성분/효능, 리뷰, 뉴스, 이벤트 등은 제외 후보로 처리합니다.

## 주의
- 사이트별 robots.txt를 확인합니다.
- JavaScript로 본문을 렌더링하는 일부 사이트는 requests/BeautifulSoup만으로 수집되지 않을 수 있습니다.
- 자동수집 결과는 연구자가 원문과 대조하여 승인해야 합니다.
