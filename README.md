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
├── db/
│   ├── __init__.py            # DB 초기화 및 작업 유틸리티
├── templates/
│   ├── dashboard.html         # 대시보드 HTML 템플릿
│   ├── upload_logs.html         # 대시보드 HTML 템플릿
├── Dockerfile                 # Docker 빌드 파일
├── docker-compose.yml         # Docker Compose 설정 파일
└── requirements.txt           # Python 종속성
```


### 추가 수정 필요한 부분

- 대쉬보드 가독성.
- 로그 분석 과정.
- upload_logs가 꼭 필요한가?

