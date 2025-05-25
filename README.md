# YouTube 영상 분석기

YouTube 영상의 자막을 다운로드하고 AI를 통해 분석하여 Notion에 저장하는 Streamlit 애플리케이션입니다.

## 주요 기능

- YouTube 영상 자막 다운로드
- GPT를 통한 자막 분석
- Notion 데이터베이스에 분석 결과 저장

## 설치 방법

1. 저장소 클론
```bash
git clone [repository-url]
cd [repository-name]
```

2. 가상환경 생성 및 활성화
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

3. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
`.env` 파일을 생성하고 다음 변수들을 설정:
```
OPENAI_API_KEY=your_openai_api_key
```

## 실행 방법

```bash
streamlit run app.py
```

## Notion 설정

1. Notion API 키 생성
   - [Notion Developers](https://www.notion.so/my-integrations) 페이지 방문
   - "새 API 통합" 클릭
   - API 통합 이름 추가
   - 관련 워크스페이스 선택 후 저장
   - 생성된 "프라이빗 API 통합 시크릿" 복사

2. Notion 데이터베이스 생성
   - Notion에서 새 페이지 생성
   - "/database" 입력하여 새 데이터베이스 생성
   - 데이터베이스에 다음 속성 추가:
     - 제목 (Title)
     - 채널명 (Text)
     - URL (URL)
     - 분석일시 (Date)
     - 주요 인사이트 (Text)

3. 데이터베이스 ID 찾기
   - 데이터베이스 페이지 URL에서 ID 복사
   - URL 형식: `https://www.notion.so/workspace/[database-id]?v=...`
   - 본인의 워크스페이스명/ 다음부터 물음표(?) 전까지 복사

4. 통합 연결
   - 데이터베이스 페이지 우측 상단 "..." 클릭
   - "Add connections" 선택
   - 생성한 통합 선택

## 라이선스

MIT License 