#!/usr/bin/env python
"""Django management entry point.

Defaults to the dev settings module so `python manage.py runserver` works
out of the box. In production, DJANGO_SETTINGS_MODULE is set explicitly
(see backend/Dockerfile) to config.settings.prod.
"""
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Is it installed and is your virtualenv active?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
