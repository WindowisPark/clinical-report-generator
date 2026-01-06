"""
Authentication and User Management Module
사용자 인증 및 관리 모듈
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime
import logging
import os
import secrets

logger = logging.getLogger(__name__)


class AuthManager:
    """사용자 인증 및 세션 관리"""

    def __init__(self, config_path: str = "config/users.yaml"):
        self.config_path = Path(config_path)
        self.usage_log_path = Path("data/usage_log.json")
        self.credentials = self._load_credentials()
        self.authenticator = self._create_authenticator()

    def _load_credentials(self) -> Dict[str, Any]:
        """사용자 인증 정보 로드"""
        if not self.config_path.exists():
            # 기본 설정 파일 생성
            # 환경 변수에서 쿠키 시크릿 키 가져오기 (없으면 랜덤 생성)
            cookie_secret = os.environ.get('AUTH_COOKIE_SECRET', secrets.token_hex(32))
            default_config = {
                'credentials': {
                    'usernames': {}
                },
                'cookie': {
                    'name': 'clinical_report_auth',
                    'key': cookie_secret,
                    'expiry_days': 30
                },
                'preauthorized': {
                    'emails': []
                }
            }
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, allow_unicode=True)
            logger.info(f"Created default user config at {self.config_path}")
            return default_config

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _create_authenticator(self):
        """Streamlit Authenticator 인스턴스 생성"""
        return stauth.Authenticate(
            self.credentials['credentials'],
            self.credentials['cookie']['name'],
            self.credentials['cookie']['key'],
            self.credentials['cookie']['expiry_days']
        )

    def login(self):
        """
        로그인 UI 렌더링 및 인증

        session_state에 다음 값들이 저장됨:
        - authentication_status: bool
        - name: str
        - username: str
        """
        try:
            self.authenticator.login(location='main')
        except Exception as e:
            st.error(f"Login error: {e}")

    def logout(self):
        """로그아웃 - 세션 및 인증 상태 완전 초기화"""
        try:
            # streamlit-authenticator의 logout 호출
            self.authenticator.logout()
        except Exception as e:
            logger.warning(f"Logout warning: {e}")

        # 모든 세션 상태 삭제 (쿠키 포함)
        keys_to_delete = list(st.session_state.keys())
        for key in keys_to_delete:
            del st.session_state[key]

        # 재초기화 (AuthManager는 다시 생성됨)
        logger.info("User logged out successfully")

    def log_usage(self, username: str, action: str, details: Dict[str, Any] = None):
        """
        사용자 활동 로그 기록

        Args:
            username: 사용자명
            action: 액션 (login, query, export 등)
            details: 추가 정보
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'username': username,
            'action': action,
            'details': details or {}
        }

        # 로그 파일 생성
        self.usage_log_path.parent.mkdir(parents=True, exist_ok=True)

        # 기존 로그 로드
        logs = []
        if self.usage_log_path.exists():
            with open(self.usage_log_path, 'r', encoding='utf-8') as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []

        # 새 로그 추가
        logs.append(log_entry)

        # 저장 (최근 1000개만 유지)
        with open(self.usage_log_path, 'w', encoding='utf-8') as f:
            json.dump(logs[-1000:], f, ensure_ascii=False, indent=2)

        logger.info(f"User activity logged: {username} - {action}")

    def get_usage_stats(self, username: Optional[str] = None) -> Dict[str, Any]:
        """
        사용 통계 조회

        Args:
            username: 특정 사용자 (None이면 전체)

        Returns:
            통계 딕셔너리
        """
        if not self.usage_log_path.exists():
            return {'total': 0, 'logs': []}

        with open(self.usage_log_path, 'r', encoding='utf-8') as f:
            try:
                all_logs = json.load(f)
            except json.JSONDecodeError:
                return {'total': 0, 'logs': []}

        if username:
            logs = [log for log in all_logs if log['username'] == username]
        else:
            logs = all_logs

        return {
            'total': len(logs),
            'logs': logs,
            'unique_users': len(set(log['username'] for log in all_logs)),
            'actions': {}
        }

    def register_user(self, username: str, name: str, email: str, password: str) -> Dict[str, Any]:
        """
        새 사용자 등록

        Args:
            username: 로그인 ID
            name: 실명
            email: 이메일
            password: 비밀번호

        Returns:
            {'success': bool, 'message': str}
        """
        # 사용자명 중복 확인
        if username in self.credentials['credentials']['usernames']:
            return {
                'success': False,
                'message': f'사용자명 "{username}"이 이미 존재합니다.'
            }

        # 비밀번호 해싱
        hasher = stauth.Hasher()
        hashed_password = hasher.hash(password)

        # 사용자 추가
        self.credentials['credentials']['usernames'][username] = {
            'name': name,
            'password': hashed_password,
            'email': email
        }

        # 설정 파일 저장
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.credentials, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"New user registered: {username}")

        return {
            'success': True,
            'message': f'✅ 회원가입 완료! "{name}"님 환영합니다.'
        }

    def save_token(self, username: str, token: str):
        """사용자의 Databricks 토큰 저장 (암호화하여)"""
        token_path = Path(f"data/tokens/{username}.token")
        token_path.parent.mkdir(parents=True, exist_ok=True)

        # 간단한 인코딩 (실제 프로덕션에서는 더 강력한 암호화 필요)
        import base64
        encoded_token = base64.b64encode(token.encode()).decode()

        with open(token_path, 'w') as f:
            f.write(encoded_token)

        logger.info(f"Token saved for user: {username}")

    def load_token(self, username: str) -> Optional[str]:
        """저장된 Databricks 토큰 로드"""
        token_path = Path(f"data/tokens/{username}.token")

        if not token_path.exists():
            return None

        try:
            with open(token_path, 'r') as f:
                encoded_token = f.read()

            # 디코딩
            import base64
            token = base64.b64decode(encoded_token.encode()).decode()

            logger.info(f"Token loaded for user: {username}")
            return token
        except Exception as e:
            logger.error(f"Failed to load token for {username}: {e}")
            return None


class DatabricksTokenValidator:
    """Databricks Token 검증"""

    @staticmethod
    def validate_token(token: str) -> Dict[str, Any]:
        """
        Token 유효성 검증

        Args:
            token: Databricks access token

        Returns:
            {'valid': bool, 'message': str}
        """
        if not token or not token.strip():
            return {
                'valid': False,
                'message': 'Token이 비어있습니다.'
            }

        # Token 형식 검증 (dapi로 시작하는지)
        if not token.startswith('dapi'):
            return {
                'valid': False,
                'message': 'Invalid token format. Databricks token should start with "dapi".'
            }

        # 길이 검증 (일반적으로 32자 이상)
        if len(token) < 32:
            return {
                'valid': False,
                'message': 'Token이 너무 짧습니다. 올바른 token인지 확인하세요.'
            }

        return {
            'valid': True,
            'message': 'Token 형식이 올바릅니다.'
        }

    @staticmethod
    def test_connection(token: str) -> Dict[str, Any]:
        """
        실제 Databricks 연결 테스트

        Args:
            token: Databricks access token

        Returns:
            {'success': bool, 'message': str}
        """
        import os

        # 임시로 환경변수 설정
        original_token = os.environ.get('DATABRICKS_TOKEN')
        os.environ['DATABRICKS_TOKEN'] = token

        try:
            from services.databricks_client import DatabricksClient

            # 클라이언트 초기화 (새로운 token으로)
            # Singleton을 우회하기 위해 직접 연결 테스트
            client = DatabricksClient()

            # 간단한 쿼리로 테스트
            result = client.execute_query("SELECT 1 as test", max_rows=1)

            if result['success']:
                return {
                    'success': True,
                    'message': f'✅ Databricks 연결 성공! (응답 시간: {result["execution_time"]}초)'
                }
            else:
                return {
                    'success': False,
                    'message': f'❌ 연결 실패: {result["error_message"]}'
                }

        except Exception as e:
            logger.error(f"Token test failed: {e}")
            return {
                'success': False,
                'message': f'❌ 연결 오류: {str(e)}'
            }

        finally:
            # 원래 token 복구
            if original_token:
                os.environ['DATABRICKS_TOKEN'] = original_token
            elif 'DATABRICKS_TOKEN' in os.environ:
                del os.environ['DATABRICKS_TOKEN']


def render_signup_page():
    """회원가입 페이지 렌더링 (중앙 정렬)"""
    # CSS
    st.markdown("""
    <style>
        .signup-header {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .signup-header h2 {
            color: #0066cc;
            font-size: 1.5rem;
            margin-bottom: 0.3rem;
        }
        .signup-header p {
            color: #666;
            font-size: 0.9rem;
        }
        /* Hide sidebar */
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

    # Centered layout
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        st.markdown("""
        <div class="signup-header">
            <h2>Create Account</h2>
            <p>Join Clinical Report Generator</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("signup_form"):
            username = st.text_input("Username", help="Login ID")
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            password_confirm = st.text_input("Confirm Password", type="password")

            col_a, col_b = st.columns([1, 1])
            with col_a:
                submit = st.form_submit_button("Sign Up", type="primary", use_container_width=True)
            with col_b:
                cancel = st.form_submit_button("Cancel", use_container_width=True)

            if cancel:
                st.session_state['show_signup'] = False
                st.rerun()

            if submit:
                # Validation
                if not all([username, name, email, password]):
                    st.error("Please fill in all fields.")
                    return

                if password != password_confirm:
                    st.error("Passwords do not match.")
                    return

                if len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                    return

                # Register
                auth_manager = st.session_state.get('auth_manager')
                if auth_manager:
                    result = auth_manager.register_user(username, name, email, password)

                    if result['success']:
                        st.success(f"Account created! Welcome, {name}.")
                        st.info("Redirecting to login...")
                        import time
                        time.sleep(2)
                        st.session_state['show_signup'] = False
                        st.rerun()
                    else:
                        st.error(result['message'])


def render_token_input_page(username: str):
    """Token 입력 페이지 렌더링"""
    st.markdown(f"### 👋 환영합니다, {username}님!")
    st.markdown("---")

    # 저장된 토큰 확인
    auth_manager = AuthManager()
    saved_token = auth_manager.load_token(username)

    st.info("""
    **Databricks Access Token이 필요합니다**

    Token 발급 방법:
    1. Databricks 로그인
    2. User Settings → Access Tokens
    3. Generate New Token
    4. Token 복사 후 아래에 입력
    """)

    # 저장된 토큰이 있으면 자동 완성
    default_token = saved_token if saved_token else ""

    token = st.text_input(
        "Databricks Access Token",
        value=default_token,
        type="password",
        help="개인 Databricks token을 입력하세요",
        key="databricks_token_input"
    )

    # 토큰 저장 체크박스
    remember_token = st.checkbox(
        "🔒 이 토큰을 기억하기",
        value=bool(saved_token),
        help="다음 로그인 시 토큰이 자동으로 입력됩니다."
    )

    col1, col2 = st.columns([1, 3])

    with col1:
        test_button = st.button("🔍 Token 테스트", type="primary", use_container_width=True)

    if token and test_button:
        with st.spinner("Token 검증 중..."):
            # 1. 형식 검증
            format_check = DatabricksTokenValidator.validate_token(token)

            if not format_check['valid']:
                st.error(f"❌ {format_check['message']}")
                return False

            # 2. 실제 연결 테스트
            connection_test = DatabricksTokenValidator.test_connection(token)

            if connection_test['success']:
                st.success(connection_test['message'])

                # Session state에 저장
                st.session_state['databricks_token'] = token
                st.session_state['token_validated'] = True

                # 토큰 저장 (체크박스 선택 시)
                if remember_token:
                    auth_manager.save_token(username, token)
                    st.success("🔒 토큰이 저장되었습니다. 다음 로그인 시 자동으로 입력됩니다.")

                # 사용 로그 기록
                auth_manager.log_usage(
                    username=username,
                    action='token_validated',
                    details={'timestamp': datetime.now().isoformat(), 'token_saved': remember_token}
                )

                st.rerun()

                return True
            else:
                st.error(connection_test['message'])
                return False

    return False
