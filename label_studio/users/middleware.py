"""Middleware to enforce user approval before granting platform access."""

import json

from django.http import JsonResponse
from django.shortcuts import render


class ApprovalRequiredMiddleware:
    """Block unapproved authenticated users from accessing the platform.

    Exempt paths (login, signup, logout, static, admin, whoami) are allowed
    so users can still authenticate and admins can still manage approvals.
    """

    EXEMPT_PREFIXES = [
        '/user/login/',
        '/user/signup/',
        '/logout',
        '/static/',
        '/admin/',
        '/api/current-user/whoami',
        '/user/pending-approval/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not getattr(request.user, 'is_approved', True):
            if not any(request.path.startswith(p) for p in self.EXEMPT_PREFIXES):
                if request.path.startswith('/api/'):
                    return JsonResponse(
                        {'detail': 'Your account is pending admin approval.'},
                        status=403,
                    )
                return render(request, 'users/pending_approval.html', status=403)

        return self.get_response(request)
