# 01 Brand Text Collector v2.2

## 승인 UI 수정
Streamlit data_editor에서 숫자형 SelectboxColumn이 일부 환경에서 편집되지 않는 문제를 피하기 위해
페이지와 Content Unit 승인 방식을 체크박스로 변경했습니다.

- 체크 = Researcher_Final 1 (포함)
- 체크 해제 = Researcher_Final 0 (제외)
- 연구자 메모는 직접 입력 가능
- 내부 CSV에는 기존과 동일하게 Researcher_Final 1/0으로 저장

기존 v2.1의 URL-only 입력, 브랜드명 자동 추정/수정, 다중 브랜드 누적, 통합 CSV 기능은 유지합니다.
