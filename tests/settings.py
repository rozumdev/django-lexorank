SECRET_KEY = "tests"

INSTALLED_APPS = [
    "django_lexorank",
    "tests",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}
