# Databricks 연결 설정 가이드

이 문서는 Clinical Report Generator를 Databricks와 연결하여 실제 쿼리 실행을 가능하게 하는 설정 방법을 안내합니다.

---

## 📋 목차

1. [연결 정보 확인](#1-연결-정보-확인)
2. [설정 방법](#2-설정-방법)
3. [연결 테스트](#3-연결-테스트)
4. [문제 해결](#4-문제-해결)

---

## 1. 연결 정보 확인

Databricks 연결에 필요한 3가지 정보:

### 1.1 Server Hostname

**형식**: `<workspace-id>.cloud.databricks.com`

**찾는 방법**:
1. Databricks 워크스페이스 접속
2. 브라우저 주소창 확인
   - 예: `https://adb-1234567890123456.7.azuredatabricks.net/`
   - → Server Hostname: `adb-1234567890123456.7.azuredatabricks.net`

### 1.2 HTTP Path

**형식**: `/sql/1.0/warehouses/<warehouse-id>`

**찾는 방법**:
1. Databricks 워크스페이스 → **SQL** → **SQL Warehouses**
2. 사용할 Warehouse 클릭
3. **Connection Details** 탭 클릭
4. **HTTP Path** 복사
   - 예: `/sql/1.0/warehouses/abc123def456ghi789`

### 1.3 Access Token (Personal Access Token)

**형식**: `dapi<random-string>`

**생성 방법**:
1. Databricks 워크스페이스 → **Settings** (톱니바퀴 아이콘)
2. **User Settings** → **Access Tokens**
3. **Generate New Token** 클릭
4. Token 정보 입력:
   - Comment: `Clinical Report Generator`
   - Lifetime: `90 days` (또는 원하는 기간)
5. **Generate** 클릭
6. **토큰 복사** (한 번만 표시됨!)
   - 예: `dapi1234567890abcdefghijklmnopqrstuvwxyz`

⚠️ **주의**: 토큰은 생성 시 한 번만 표시되므로 안전한 곳에 저장하세요!

---

## 2. 설정 방법

### 방법 1: config.yaml 사용 (권장)

1. 프로젝트 루트의 `config.yaml` 파일 열기

2. `databricks` 섹션 추가:

```yaml
api_keys:
  gemini_api_key: "YOUR_GEMINI_API_KEY"

databricks:
  server_hostname: "adb-xxx.7.azuredatabricks.net"
  http_path: "/sql/1.0/warehouses/abc123"
  access_token: "dapi1234567890abcdef"
```

3. 실제 값으로 대체:
   - `server_hostname`: 위 1.1에서 확인한 값
   - `http_path`: 위 1.2에서 확인한 값
   - `access_token`: 위 1.3에서 생성한 토큰

### 방법 2: 환경변수 사용

#### macOS/Linux:

```bash
# ~/.zshrc 또는 ~/.bashrc에 추가
export DATABRICKS_SERVER_HOSTNAME="adb-xxx.7.azuredatabricks.net"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/abc123"
export DATABRICKS_TOKEN="dapi1234567890abcdef"

# 적용
source ~/.zshrc  # 또는 source ~/.bashrc
```

#### Windows (PowerShell):

```powershell
# 시스템 환경변수 설정
[Environment]::SetEnvironmentVariable("DATABRICKS_SERVER_HOSTNAME", "adb-xxx.7.azuredatabricks.net", "User")
[Environment]::SetEnvironmentVariable("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/abc123", "User")
[Environment]::SetEnvironmentVariable("DATABRICKS_TOKEN", "dapi1234567890abcdef", "User")
```

### 방법 3: .env 파일 사용 (개발용)

1. 프로젝트 루트에 `.env` 파일 생성:

```bash
DATABRICKS_SERVER_HOSTNAME=adb-xxx.7.azuredatabricks.net
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/abc123
DATABRICKS_TOKEN=dapi1234567890abcdef
```

2. `.gitignore`에 `.env` 추가 (보안):

```
.env
```

3. Python에서 `python-dotenv` 사용:

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 3. 연결 테스트

### 3.1 Python 스크립트로 테스트

```python
from services.databricks_client import DatabricksClient

# 클라이언트 초기화
client = DatabricksClient()

# 연결 테스트
if client.test_connection():
    print("✅ Databricks 연결 성공!")

    # 간단한 쿼리 실행
    result = client.execute_query("SELECT 1 as test")

    if result['success']:
        print(f"✅ 쿼리 실행 성공!")
        print(result['data'])
    else:
        print(f"❌ 쿼리 실행 실패: {result['error_message']}")
else:
    print("❌ Databricks 연결 실패")
```

### 3.2 Streamlit 앱에서 확인

1. 앱 실행:
```bash
streamlit run app.py
```

2. **🤖 자연어 SQL 생성** 탭 확인:
   - ✅ "Databricks 연결 가능" → 성공
   - ⚠️ "Databricks 연결 정보 없음" → 설정 확인 필요

3. SQL 생성 후 **▶️ 쿼리 실행** 버튼 클릭하여 테스트

---

## 4. 문제 해결

### 4.1 "Missing Databricks configuration" 오류

**원인**: 연결 정보가 설정되지 않음

**해결**:
1. `config.yaml` 또는 환경변수 설정 확인
2. 오타 확인 (특히 키 이름)
3. 앱 재시작

### 4.2 연결 실패 (Connection failed)

**원인 1**: Server Hostname 오류
- **확인**: `https://` 제거 확인 (hostname만 입력)
- **올바른 예**: `adb-xxx.7.azuredatabricks.net`
- **잘못된 예**: `https://adb-xxx.7.azuredatabricks.net`

**원인 2**: HTTP Path 오류
- **확인**: 정확히 Warehouse Connection Details에서 복사
- **형식**: `/sql/1.0/warehouses/xxxxx`

**원인 3**: Access Token 만료/오류
- **확인**: Databricks에서 토큰 상태 확인
- **해결**: 새 토큰 생성 후 재설정

### 4.3 권한 오류 (Permission denied)

**원인**: Warehouse 또는 테이블 접근 권한 부족

**해결**:
1. Databricks 관리자에게 권한 요청
2. 사용 중인 Warehouse에 대한 "Can Use" 권한 확인
3. 조회할 테이블에 대한 SELECT 권한 확인

### 4.4 쿼리 실행 오류

**CAST_INVALID_INPUT**:
```sql
-- ❌ 잘못된 방법
CAST(res_treat_start_date AS DATE)

-- ✅ 올바른 방법
TO_DATE(res_treat_start_date, 'yyyyMMdd')
```

**TABLE_OR_VIEW_NOT_FOUND**:
- 좌측 사이드바 "데이터 사전"에서 정확한 테이블명 확인
- 대소문자 구분 주의
- 카탈로그/스키마 경로 확인 (필요시 `catalog.schema.table` 형식 사용)

---

## 5. 보안 권장사항

### 5.1 토큰 보안

1. **절대 코드에 직접 입력하지 마세요**
   ```python
   # ❌ 위험
   access_token = "dapi1234567890abcdef"

   # ✅ 안전
   access_token = os.getenv("DATABRICKS_TOKEN")
   ```

2. **config.yaml 또는 .env 파일을 Git에 커밋하지 마세요**
   ```bash
   # .gitignore에 추가
   config.yaml
   .env
   ```

3. **토큰 주기적 갱신**
   - 90일마다 토큰 재생성 권장
   - 유출 의심 시 즉시 폐기 후 재생성

### 5.2 네트워크 보안

- VPN 사용 권장 (회사 네트워크 정책에 따라)
- 공용 Wi-Fi에서 접속 지양

---

## 6. 추가 리소스

- [Databricks SQL Connector 공식 문서](https://docs.databricks.com/dev-tools/python-sql-connector.html)
- [Personal Access Token 관리](https://docs.databricks.com/dev-tools/auth.html#personal-access-tokens)
- [SQL Warehouse 설정](https://docs.databricks.com/sql/admin/sql-endpoints.html)

---

## 도움이 필요하신가요?

- 프로젝트 이슈: [GitHub Issues](https://github.com/your-org/clinical_report_generator/issues)
- Databricks 문의: Databricks 관리자 또는 지원팀
