"""Представления приложения pages: статичные страницы и страницы ошибок."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView


class AboutView(TemplateView):
    """Страница «О проекте»."""

    template_name = 'pages/about.html'


class RulesView(TemplateView):
    """Страница «Правила»."""

    template_name = 'pages/rules.html'


def page_not_found(
    request: HttpRequest, exception: Exception,
) -> HttpResponse:
    """Кастомная страница ошибки 404."""
    return render(request, 'pages/404.html', status=404)


def csrf_failure(request: HttpRequest, reason: str = '') -> HttpResponse:
    """Кастомная страница ошибки 403 CSRF."""
    return render(request, 'pages/403csrf.html', status=403)


def server_error(request: HttpRequest) -> HttpResponse:
    """Кастомная страница ошибки 500."""
    return render(request, 'pages/500.html', status=500)
