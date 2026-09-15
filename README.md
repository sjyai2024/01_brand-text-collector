# 01 Brand Text Collector v2.7

## StreamlitWidgetAlreadyInstantiatedError 수정
v2.6에서 `url_input` 위젯이 생성된 뒤 `st.session_state["url_input"]` 값을 직접 변경해 발생하던 오류를 제거했습니다.

- 브랜드 추가 완료 후 URL 위젯 state를 코드에서 강제로 수정하지 않음
- URL 지우기는 `on_click` callback으로 안전하게 처리
- 새 브랜드는 기존 URL을 직접 덮어쓰거나 `입력 URL 지우기` 후 입력
- 다중 브랜드 누적, 브랜드명 확인, 페이지 승인, Content Unit 승인, 통합 CSV 기능 유지
