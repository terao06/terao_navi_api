from django.apps import AppConfig


class ModelsConfig(AppConfig):
    """モデルアプリケーションの設定"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'local_setting.local_mysql'
    label = 'local_mysql_models'
    verbose_name = 'Database Models'
