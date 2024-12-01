[2024-11-26] - 양재원

### 아래는 해당 프로젝트의 전체적인 구조다.

## Apache2 / Nginx 웹 서버 로그를 대상으로 수집 / 분석 / 대시보드화 한다.

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


---

# 각 기능별 제안한 개선 가능성 정리


## 1. app.py (메인 엔트리)

- Thread 안전성: 작업 스케줄링에는 Flask-APScheduler 같은 라이브러리를 사용해 스레드 충돌 방지.

- Debug 설정 관리: 운영 환경에서는 debug=True를 비활성화하고, 환경 변수를 통한 설정 관리.

- 스케줄러 최적화: Timer 대신 Celery나 APScheduler로 반복 작업 관리.

(완료)

---


## 2. Blueprint 모듈

### blueprints/analysis/analysis.py

- 기능 구현 필요: 로그 데이터 분석 기능 추가(Pandas 활용).

- 예측 분석: 에러 발생 패턴을 기반으로 경고 시스템 구축.

- 유닛 테스트 작성: 분석 함수의 정확도를 검증하는 테스트 추가.


### blueprints/recent_logs/routes.py

- SQL Injection 방지: SQLAlchemy 사용으로 쿼리의 안전성 확보.

- 페이징: 대규모 데이터 처리 시 결과를 제한하고 페이지네이션 추가.

- 필터 확장: 타임존이나 로그 크기 등 추가 필터 조건 지원.

- 로그가 collector로 실시간 수집될 때 실시간으로 반영되는지 확인 해야함.

- (완료)


### blueprints/dashboard/routes.py

### (***) 대시보드 이상해짐

- UI/UX 업그레이드, 어둡고 모던한 디자인 선호.

- 시각화 강화: Dash 통합으로 대화형 대시보드 지원.

- create_dashboard에서 만든 그래프 dashboard에 실시간 반영.

- collector로 실시간으로 로그를 위에서 직접 만든 대시보드에 연결해서 동적 대시보드화.

- 그래프 유효성 검사: 사용자 입력값(X, Y 축 등)을 검증하는 로직 추가.

- JSON 파일 관리 개선: 파일 대신 데이터베이스나 Redis 활용.

- 사용자 입력 유효성 검사: 허용된 컬럼 이름만 사용하도록 화이트리스트 검증.

- 에러 핸들링 추가: 그래프 생성 및 데이터 조회 시 상세 에러 메시지와 로깅 추가.

### *현재 진행 상황*

- dashboard 작업 중인데 메인페이지 일단 날아갔고, confirm해서 dashboard/ 에다가 넣는거랑 dashboard/create_dash/ 사용하는 부분 없음.

- 그래프는 잘 만들어짐 ㅋㅋ

- 디자인만 손보면 됨. 손보다가 퇴근. collector 에서 넘겨주는 로그값 실시간 반영해야함. 현재 오류 상태임. *(해결 완료)*

- 이젠 시간나면 cleanup 수정하고 아니면 디자인만 손보기.

---

### blueprints/get_logs/routes.py

- 결과 제한: 필터 없는 쿼리에 대해 기본 결과 제한 추가.

- 필터 유효성 검사: 잘못된 level 값을 방지.

- 필드 확장: 응답에 선택적 필드를 포함하는 기능 추가.

- (완료)


### blueprints/upload_logs/routes.py

- 대규모 파일 처리: 스트리밍 방식으로 메모리 사용 최적화.

- 로그 형식 지원: Nginx, JSON 로그 등 다양한 형식 지원.

- (완료)


### blueprints/main/routes.py

- UI/UX 강화.

- 템플릿 데이터 관리:

- 렌더링 시 기본 데이터(예: 앱 이름, 버전 정보)를 전달하여 유지보수성을 향상.

- 확장성 고려:

- 페이지 네비게이션이나 다국어 지원을 추가하려면 별도의 config를 활용.


### blueprints/collector/collector.py

- 위 개선사항들 적용 후 오류 수정. (Nginx 로그도 수집하도록 등등)

- 실시간 로그 수집 안정화. (비동기? 등)

- 실시간 처리 안정성: 파일 읽기 시 try-except 블록 추가로 파일 갱신 문제 방지.

- 효율성 개선: 마지막 읽은 위치를 저장하고 이후 위치부터 읽도록 수정.

- 중복 방지: 데이터베이스에서 고유성 제약 조건 추가.

- 로깅 및 모니터링: 처리된 로그의 수와 실패 로그를 기록.

(완료)

---


## 3. Database Management (db/cleanup.py)

- DB 쿼리 logs 테이블에서 변경 필요.

- (미완료)

---


## 4. Frontend Templates

### templates/main_page.html

- 확장성: 메뉴를 Navbar로 통합하여 페이지 확장성을 확보.

- 스타일 커스터마이징: 로컬 CSS 사용으로 디자인 제어 강화.

- 다국어 지원: 텍스트를 국제화(i18n) 처리.


### templates/upload_logs.html

- 파일 유효성 검사: 파일 크기와 포맷에 대한 클라이언트 검증 추가.

- 업로드 진행률 표시: Progress Bar로 사용자 경험 향상.

- 보안 강화: 업로드 처리에 추가적인 보안 점검.


### templates/recent_logs.html

- 비동기 검색: AJAX를 활용해 실시간 필터링.

- 페이지네이션: 결과를 페이징 처리로 제한.

- 로그 통계: 레벨별 빈도를 시각화해 대시보드 느낌 강화.

---


## 종합적으로:

### 성능 개선: 대규모 데이터 처리에 적합한 최적화.

### 보안 강화: CSRF 방어와 SQL Injection 방지.

### 사용자 경험 향상: 비동기 처리, 대시보드 통합, 직관적 UI 제공.

### 확장 가능성: 로그 포맷 지원 확대와 국제화(i18n) 적용.

---

