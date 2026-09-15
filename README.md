# 01 Brand Text Collector v2.1

## 브랜드명 자동 인식 개선
자동 추정 우선순위:
1. JSON-LD Organization / WebSite / Brand name
2. og:site_name
3. application-name / apple-mobile-web-app-title
4. 페이지 title
5. domain fallback

## 연구자 확인
크롤링 직후 자동 인식 브랜드명을 별도 확인 화면에 표시합니다.
자동 인식이 틀리면 연구자가 직접 수정한 뒤 `브랜드명 확인 및 추가`를 눌러 확정합니다.

이후 기능은 v2.0과 동일:
페이지 자동 1/0 → 연구자 수정 → Content Unit → 자동 1/0 → 연구자 수정 → 여러 브랜드 누적 → 통합 CSV.
