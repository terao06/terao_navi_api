"""
データベースマイグレーション用のDjango設定
"""
import os
import sys

# パスの構築
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR)))

# プロジェクトルートをパスに追加
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# セキュリティ警告: プロダクションでは秘密鍵を使用しないでください！
SECRET_KEY = 'local-development-key-do-not-use-in-production'

# セキュリティ警告: プロダクションではデバッグモードをオンにしないでください！
DEBUG = True

ALLOWED_HOSTS = ['*']

# アプリケーション定義
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'local_setting.local_mysql.apps.ModelsConfig',
    'django.contrib.sessions'
]

# データベース
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQL_DATABASE', 'db_local'),
        'USER': os.environ.get('MYSQL_USER', 'navi_admin_user'),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD', 'password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# 国際化
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

# デフォルトの主キーフィールドタイプ
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
