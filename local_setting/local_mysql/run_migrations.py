#!/usr/bin/env python
"""
Djangoマイグレーション実行スクリプト
"""
import os
import sys
import django
import time
import MySQLdb

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, '/app')


# Django設定を指定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'local_setting.local_mysql.django_settings')

def wait_for_db():
    """データベースの接続を待機"""
    max_retries = 30
    retry_interval = 2
    
    db_config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', '3306')),
        'user': os.environ.get('MYSQL_USER', 'navi_admin_user'),
        'password': os.environ.get('MYSQL_PASSWORD', 'password'),
        'database': os.environ.get('MYSQL_DATABASE', 'db_local'),
    }
    
    print(f"Waiting for database at {db_config['host']}:{db_config['port']}...")
    
    for attempt in range(max_retries):
        try:
            conn = MySQLdb.connect(**db_config)
            conn.close()
            print("Database is ready!")
            return True
        except MySQLdb.Error as e:
            print(f"Attempt {attempt + 1}/{max_retries}: Database not ready yet... ({e})")
            time.sleep(retry_interval)
    
    print("Failed to connect to database after maximum retries")
    return False

def run_migrations():
    """マイグレーションを実行"""
    if not wait_for_db():
        sys.exit(1)
    
    # Djangoのセットアップ
    django.setup()
    
    from django.core.management import execute_from_command_line
    from django.db import connection
    
    print("Starting Django migrations...")
    
    # マイグレーションファイルの作成
    print("\n=== マイグレーションファイルの作成 ===")
    try:
        execute_from_command_line(['manage.py', 'makemigrations', 'local_mysql_models'])
        print("Migration files created successfully!")
    except Exception as e:
        print(f"Note during makemigrations: {e}")
        # makemigrationsがエラーでも続行（既にマイグレーションがある場合など）
    
    # マイグレーションの実行
    print("\n=== マイグレーションの実行 ===")
    try:
        execute_from_command_line(['manage.py', 'migrate'])
        execute_from_command_line(['manage.py', 'migrate', 'sessions'])
        print("\n=== Migration completed successfully ===")
    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)
    
    # 初期データの投入
    print("\n=== 初期データの投入 ===")
    insert_initial_data()

def insert_initial_data():
    """初期データの投入"""
    from local_setting.local_mysql.models import Role, Company, User, Application, Manual

    # ロールの初期データ
    roles = [
        {'role_id': 1, 'name': '全権限付与', 'description': 'すべての機能にアクセス可能'},
        {'role_id': 2, 'name': '閲覧・編集権限', 'description': 'データの閲覧と編集が可能'},
        {'role_id': 3, 'name': '閲覧権限', 'description': 'データの閲覧のみ可能'},
    ]
    companies = [
        {"company_id": 1, "name": "株式会社A", "address": "岩戸南4-3-6", "tel": "080-1111-1111", "home_page": "http://localhost:3000", "is_deleted": 0}
    ]

    users = [
        {
            "user_id": 1,
            "username": "user",
            "email": "test@aaa.com",
            "password": "pbkdf2_sha256$600000$a8Zcr3N5ZgZtau4cpe9hb6$Sgt0eFukNvOZ0g6sSYpNEdHFRtf9P2WFhDMsJAlFF7U=",
            "first_name": "太郎",
            "last_name": "テスト",
            "is_active": 1,
            "company_id": 1,
            "is_deleted": 0,
            "role_id": 1
        }
    ]

    applications = [
        {
            "application_id": 1,
            "application_name": "動作確認用アプリケーション",
            "description": "api側動作確認用アプリケーションです",
            "is_deleted": 0,
            "company_id": 1
        }
    ]

    manuals = [
        {
            "manual_id": 1,
            "manual_name": "入居者向けマニュアル",
            "description": "入居者向けマニュアルです。",
            "file_extension": "pdf",
            "file_size": 2000,
            "is_deleted": 0,
            "application_id": 1
        }
    ]
    
    for role_data in roles:
        Role.objects.update_or_create(
            role_id=role_data['role_id'],
            defaults={
                'name': role_data['name'],
                'description': role_data['description']
            }
        )
        print(f"Role created/updated: {role_data['name']}")

    for company_data in companies:
        Company.objects.update_or_create(
            company_id=company_data['company_id'],
            defaults={
                'name': company_data['name'],
                'address': company_data['address'],
                'tel': company_data['tel'],
                'home_page': company_data['home_page'],
                'is_deleted': company_data['is_deleted']
            }
        )
        print(f"Company created/updated: {company_data['name']}")

    for user_data in users:
        User.objects.update_or_create(
            user_id=user_data['user_id'],
            defaults={
                'username': user_data['username'],
                'email': user_data['email'],
                'password': user_data['password'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'is_active': user_data['is_active'],
                'company_id': user_data['company_id'],
                'is_deleted': user_data['is_deleted'],
                'role_id': user_data['role_id']
            }
        )
        print(f"User created/updated: {user_data['username']}")

    for app_data in applications:
        Application.objects.update_or_create(
            application_id=app_data['application_id'],
            defaults={
                'application_name': app_data['application_name'],
                'description': app_data['description'],
                'is_deleted': app_data['is_deleted'],
                'company_id': app_data['company_id']
            }
        )
        print(f"Application created/updated: {app_data['application_name']}")

    for manual_data in manuals:
        Manual.objects.update_or_create(
            manual_id=manual_data['manual_id'],
            defaults={
                'manual_name': manual_data['manual_name'],
                'description': manual_data['description'],
                'file_extension': manual_data['file_extension'],
                'file_size': manual_data['file_size'],
                'is_deleted': manual_data['is_deleted'],
                'application_id': manual_data['application_id']
            }
        )
        print(f"Manual created/updated: {manual_data['manual_name']}")
    
    print("Initial data insertion completed!")

if __name__ == '__main__':
    run_migrations()
