# 01 Brand Text Collector v2.3

## 승인 UI 변경
페이지와 Content Unit의 `Researcher_Final` 값을 웹 표에서 숫자 0 또는 1로 직접 수정합니다.

- 1 = 분석 포함
- 0 = 제외
- 허용값은 0~1 정수로 제한
- `Auto_Include`는 자동판정 기록으로 읽기 전용 유지
- `Researcher_Final`만 연구자가 직접 수정
- `Researcher_Note`도 직접 입력 가능

기존 URL-only 입력, 브랜드명 자동 추정/수정, 다중 브랜드 누적, 통합 CSV 기능은 유지합니다.
