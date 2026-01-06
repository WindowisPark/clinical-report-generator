"""
User Management Utility
사용자 추가/삭제/비밀번호 변경 도구
"""

import yaml
import streamlit_authenticator as stauth
from pathlib import Path
import argparse


class UserManager:
    """사용자 관리 클래스"""

    def __init__(self, config_path: str = "config/users.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_or_create_config()

    def _load_or_create_config(self):
        """설정 파일 로드 또는 생성"""
        if not self.config_path.exists():
            config = {
                'credentials': {
                    'usernames': {}
                },
                'cookie': {
                    'name': 'clinical_report_auth',
                    'key': 'clinical_report_secret_key_2025',  # 프로덕션에서는 변경하세요!
                    'expiry_days': 30
                },
                'preauthorized': {
                    'emails': []
                }
            }
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_config(config)
            print(f"✅ Created new config file: {self.config_path}")
            return config

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _save_config(self, config=None):
        """설정 파일 저장"""
        if config is None:
            config = self.config

        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    def add_user(self, username: str, name: str, password: str, email: str = ""):
        """
        사용자 추가

        Args:
            username: 로그인 ID
            name: 실명
            password: 비밀번호
            email: 이메일 (선택)
        """
        if username in self.config['credentials']['usernames']:
            print(f"❌ User '{username}' already exists!")
            return False

        # 비밀번호 해싱
        hasher = stauth.Hasher()
        hashed_password = hasher.hash(password)

        # 사용자 정보 추가
        self.config['credentials']['usernames'][username] = {
            'name': name,
            'password': hashed_password,
            'email': email
        }

        self._save_config()
        print(f"✅ User '{username}' added successfully!")
        print(f"   Name: {name}")
        print(f"   Email: {email}")
        return True

    def remove_user(self, username: str):
        """사용자 삭제"""
        if username not in self.config['credentials']['usernames']:
            print(f"❌ User '{username}' not found!")
            return False

        del self.config['credentials']['usernames'][username]
        self._save_config()
        print(f"✅ User '{username}' removed successfully!")
        return True

    def list_users(self):
        """모든 사용자 목록 출력"""
        users = self.config['credentials']['usernames']

        if not users:
            print("No users found.")
            return

        print("\n📋 Current Users:")
        print("-" * 60)
        for username, info in users.items():
            print(f"Username: {username}")
            print(f"  Name: {info['name']}")
            print(f"  Email: {info.get('email', 'N/A')}")
            print("-" * 60)

    def reset_password(self, username: str, new_password: str):
        """비밀번호 재설정"""
        if username not in self.config['credentials']['usernames']:
            print(f"❌ User '{username}' not found!")
            return False

        # 새 비밀번호 해싱
        hasher = stauth.Hasher()
        hashed_password = hasher.hash(new_password)

        # 비밀번호 업데이트
        self.config['credentials']['usernames'][username]['password'] = hashed_password

        self._save_config()
        print(f"✅ Password reset for user '{username}'!")
        return True


def main():
    """CLI 인터페이스"""
    parser = argparse.ArgumentParser(description='User Management for Clinical Report Generator')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # add 명령어
    parser_add = subparsers.add_parser('add', help='Add a new user')
    parser_add.add_argument('username', help='Login username')
    parser_add.add_argument('name', help='Full name')
    parser_add.add_argument('password', help='Password')
    parser_add.add_argument('--email', default='', help='Email address (optional)')

    # remove 명령어
    parser_remove = subparsers.add_parser('remove', help='Remove a user')
    parser_remove.add_argument('username', help='Username to remove')

    # list 명령어
    subparsers.add_parser('list', help='List all users')

    # reset 명령어
    parser_reset = subparsers.add_parser('reset', help='Reset user password')
    parser_reset.add_argument('username', help='Username')
    parser_reset.add_argument('password', help='New password')

    args = parser.parse_args()

    manager = UserManager()

    if args.command == 'add':
        manager.add_user(args.username, args.name, args.password, args.email)
    elif args.command == 'remove':
        manager.remove_user(args.username)
    elif args.command == 'list':
        manager.list_users()
    elif args.command == 'reset':
        manager.reset_password(args.username, args.password)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
