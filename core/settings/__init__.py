# core/settings/__init__.py
import os

# אם לא הגדרנו כלום, ניקח את dev כברירת מחדל
env = os.environ.get('DJANGO_STATE', 'dev')

if env == 'prod':
    from .prod import *
else:
    from .dev import *