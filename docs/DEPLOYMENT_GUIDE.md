# Clinical Report Generator - 배포 가이드

**대상:** 1-3명 소규모 팀
**버전:** 1.0 (Authentication 추가)
**최종 수정:** 2025-10-20

---

## 🎯 배포 흐름

```
사용자 접속
    ↓
[로그인 화면] ← ID/PW 입력
    ↓
[Databricks Token 입력] ← 개인 Token 입력
    ↓
[Token 검증] ← 실제 연결 테스트
    ↓
[메인 앱 사용] ← 쿼리 생성/실행
```

**특징:**
- ✅ 로그인으로 사용자 기록 보관
- ✅ 개인별 Databricks Token 관리
- ✅ Token 검증 후에만 앱 사용 가능
- ✅ 사용 로그 자동 기록

---

## 📦 사전 준비

### 1. 패키지 설치

```bash
cd /path/to/clinical_report_generator
pip install -r requirements.txt
```

**필수 패키지:**
- `streamlit-authenticator>=0.2.3` (인증)
- `databricks-sql-connector` (DB 연결)

### 2. 사용자 추가

```bash
# 첫 번째 사용자
python3 tools/manage_users.py add user1 "김철수" password123 --email user1@company.com

# 두 번째 사용자
python3 tools/manage_users.py add user2 "이영희" password456 --email user2@company.com

# 사용자 목록 확인
python3 tools/manage_users.py list
```

**출력 예시:**
```
📋 Current Users:
------------------------------------------------------------
Username: user1
  Name: 김철수
  Email: user1@company.com
------------------------------------------------------------
Username: user2
  Name: 이영희
  Email: user2@company.com
------------------------------------------------------------
```

### 3. 설정 파일 확인

**config.yaml** (Gemini API key만 필요)
```yaml
api_keys:
  gemini_api_key: "YOUR_GEMINI_API_KEY_HERE"

databricks:
  server_hostname: ""  # 비워두세요 (사용자별로 입력)
  http_path: "/sql/1.0/warehouses/your_warehouse_id"
  access_token: ""      # 비워두세요 (사용자별로 입력)
```

**config/users.yaml** (자동 생성됨)
```yaml
credentials:
  usernames:
    user1:
      name: 김철수
      password: $2b$12$hashed_password...
      email: user1@company.com
```

---

## 🚀 배포 방법

### **Option 1: Streamlit Cloud** (추천 ⭐⭐⭐)

#### 장점
- ✅ 완전 무료 (3 apps까지)
- ✅ 자동 HTTPS
- ✅ URL 공유로 즉시 접근
- ✅ 자동 재시작

#### 배포 절차

**1단계: GitHub 준비**
```bash
# .gitignore 확인 (중요!)
echo "config/users.yaml" >> .gitignore
echo "data/" >> .gitignore
echo "logs/" >> .gitignore
echo ".streamlit/secrets.toml" >> .gitignore

# Git commit & push
git add .
git commit -m "Add authentication system"
git push origin main
```

**2단계: Streamlit Cloud 설정**
1. https://share.streamlit.io 접속
2. "New app" 클릭
3. GitHub 저장소 연결
4. **Main file path:** `app_with_auth.py`
5. **Python version:** 3.9+

**3단계: Secrets 설정**
Streamlit Cloud Dashboard → Settings → Secrets
```toml
[api_keys]
gemini_api_key = "YOUR_ACTUAL_GEMINI_API_KEY"

[databricks]
server_hostname = "your-workspace.cloud.databricks.com"
http_path = "/sql/1.0/warehouses/abc123"
```

**4단계: Deploy!**
- "Deploy" 버튼 클릭
- 5분 후 URL 생성 (예: `https://clinical-report.streamlit.app`)

#### 사용자 안내
"팀원들에게 URL 공유 → 각자 로그인 → Databricks Token 입력"

---

### **Option 2: 로컬 실행** (테스트용 ⭐)

#### 빠른 시작

```bash
cd /path/to/clinical_report_generator

# 앱 실행
streamlit run app_with_auth.py
```

브라우저에서 `http://localhost:8501` 접속

#### 네트워크에서 접근

```bash
# 내부 IP로 접근 가능하게
streamlit run app_with_auth.py --server.address 0.0.0.0
```

팀원들: `http://[실행PC-IP]:8501` 접속

**제한사항:**
- ⚠️ 실행 PC가 항상 켜져 있어야 함
- ⚠️ 동시 접속 시 느릴 수 있음

---

### **Option 3: Docker** (고급 사용자 ⭐⭐)

#### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 복사
COPY . .

# 포트 노출
EXPOSE 8501

# Streamlit 설정
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8501

# 앱 실행
CMD ["streamlit", "run", "app_with_auth.py"]
```

#### 빌드 & 실행

```bash
# Docker 이미지 빌드
docker build -t clinical-report-generator .

# 컨테이너 실행
docker run -p 8501:8501 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  clinical-report-generator
```

접속: `http://localhost:8501`

---

## 👥 사용자 관리

### 사용자 추가
```bash
python3 tools/manage_users.py add <username> "<name>" <password> --email <email>
```

### 사용자 삭제
```bash
python3 tools/manage_users.py remove <username>
```

### 비밀번호 재설정
```bash
python3 tools/manage_users.py reset <username> <new_password>
```

### 사용자 목록 조회
```bash
python3 tools/manage_users.py list
```

---

## 📊 사용 로그 확인

### 로그 파일 위치
```
data/usage_log.json
```

### 로그 내용 예시
```json
[
  {
    "timestamp": "2025-10-20T10:30:15",
    "username": "user1",
    "action": "login",
    "details": {}
  },
  {
    "timestamp": "2025-10-20T10:31:22",
    "username": "user1",
    "action": "token_validated",
    "details": {"timestamp": "2025-10-20T10:31:22"}
  },
  {
    "timestamp": "2025-10-20T10:35:10",
    "username": "user1",
    "action": "use_nl2sql",
    "details": {}
  }
]
```

### 로그 분석
```bash
# 최근 10개 로그 확인
tail -10 data/usage_log.json | jq

# 특정 사용자 필터링
cat data/usage_log.json | jq '.[] | select(.username == "user1")'
```

---

## 🔐 보안 권장 사항

### 1. Cookie Secret 변경 (프로덕션 필수!)

**config/users.yaml**
```yaml
cookie:
  name: 'clinical_report_auth'
  key: 'CHANGE_THIS_TO_RANDOM_STRING_IN_PRODUCTION'  # ← 변경하세요!
  expiry_days: 30
```

**생성 방법:**
```python
import secrets
print(secrets.token_urlsafe(32))
# 출력: 'xK9f2_mP4vN8qR7tY3sW6uZ1aB5cD0eF'
```

### 2. HTTPS 사용
- Streamlit Cloud: 자동 HTTPS ✅
- 로컬/Docker: ngrok 또는 reverse proxy 사용

### 3. 파일 권한
```bash
chmod 600 config/users.yaml      # 사용자 인증 정보
chmod 600 config.yaml            # API keys
chmod 700 data/                  # 로그 디렉토리
```

### 4. .gitignore 확인
```
config/users.yaml
data/
logs/
.streamlit/secrets.toml
*.pyc
__pycache__/
```

---

## 🐛 문제 해결

### 로그인 실패
**증상:** "Username/password is incorrect"
**해결:**
```bash
# 사용자 확인
python3 tools/manage_users.py list

# 비밀번호 재설정
python3 tools/manage_users.py reset username new_password
```

### Token 검증 실패
**증상:** "❌ 연결 실패: ..."
**해결:**
1. Databricks 토큰 확인
   - User Settings → Access Tokens
   - 토큰이 만료되지 않았는지 확인
   - `dapi`로 시작하는지 확인

2. config.yaml 확인
   ```yaml
   databricks:
     server_hostname: "your-workspace.cloud.databricks.com"
     http_path: "/sql/1.0/warehouses/abc123"
   ```

3. 네트워크 확인
   - Databricks 접근 가능한지 확인
   - 방화벽 설정 확인

### 모듈 import 에러
```bash
pip install -r requirements.txt --upgrade
```

---

## 📞 지원

### 로그 확인
```bash
# 애플리케이션 로그
ls -lh logs/

# 사용 로그
cat data/usage_log.json | jq
```

### 초기화 (긴급 시)
```bash
# 모든 사용자 삭제 (주의!)
rm config/users.yaml

# 사용 로그 초기화
rm data/usage_log.json

# 새 사용자 추가
python3 tools/manage_users.py add admin "Admin" admin123
```

---

## 📋 체크리스트

### 배포 전
- [ ] requirements.txt 설치 완료
- [ ] 사용자 추가 완료 (최소 1명)
- [ ] Gemini API key 설정
- [ ] Databricks 설정 확인 (hostname, http_path)
- [ ] .gitignore 확인
- [ ] Cookie secret 변경 (프로덕션)

### 배포 후
- [ ] 로그인 테스트
- [ ] Token 검증 테스트
- [ ] 쿼리 실행 테스트
- [ ] 사용 로그 확인

### 사용자 안내
- [ ] URL 공유
- [ ] 로그인 ID/PW 전달
- [ ] Databricks token 발급 방법 안내
- [ ] 문제 발생 시 연락처 전달

---

**작성자:** Claude Code
**문의:** 사용 로그 확인 → `data/usage_log.json`
