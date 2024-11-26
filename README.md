[2024-11-26] - 양재원

### 아래는 해당 프로젝트의 전체적인 구조다.

```bash
project-root/
├── app.py                     # Flask 애플리케이션 엔트리포인트
├── blueprints/
│   ├── upload_logs/
│   │   ├── __init__.py        # Upload Logs 블루프린트
│   │   └── routes.py          # 업로드 API 정의
│   ├── get_logs/
│   │   ├── __init__.py        # Get Logs 블루프린트
│   │   └── routes.py          # 조회 API 정의
│   ├── dashboard/
│   │   ├── __init__.py        # Dashboard 블루프린트
│   │   └── routes.py          # 대시보드 API 정의
│   ├── collector/
│   │   ├── __init__.py        # Collector 블루프린트
│   │   └── collector.py       # 실시간 Apache 로그 수집
│   ├── main/
│   │   ├── __init__.py        # 블루프린트
│   │   └── routes.py          # 메인 페이지
│   ├── recent_logs/
│   │   ├── __init__.py        # 블루프린트
│   │   └── routes.py          # 최근 로그 검색
│   ├── analysis/
│   │   ├── __init__.py        # 블루프린트
│   │   └── analysis.py        # 분석한 로그 분석
├── db/
│   ├── __init__.py            # DB 초기화 및 작업 유틸리티
│   ├── cleanup.py             # 주기적으로 디비 청소(압축 백업)
├── templates/
│   ├── dashboard.html         # 대시보드 HTML 템플릿
│   ├── upload_logs.html       # 로그 파일 업로드 템플릿
│   ├── main_page.html         # 메인 페이지 템플릿
│   ├── create_graph.html      # 대시보드 그래프 만드는 템플릿
│   ├── recent_logs.html       # 최근 로그와 로그 검색 템플릿
├── export/
│   ├── logs_export.csv.gz     # DB 일정량 가득차면 파일로 백업 후 디비 청소
├── Dockerfile                 # Docker 빌드 파일
├── docker-compose.yml         # Docker Compose 설정 파일
└── requirements.txt           # Python 종속성
└── sorted_graph.json          # 생성한 그래프 저장 관리 파일
```


### 추가 수정 필요한 부분

- 메인 페이지 필요성. -> 일단 만듦.
- 대쉬보드 가독성. -> 어느정도 진행.
- 로그 분석 과정.
- upload_logs가 꼭 필요한가?

