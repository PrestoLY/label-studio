"""Analytics API: productivity dashboard and CSV export for admin users."""

import csv
import io

from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.http import StreamingHttpResponse
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from tasks.models import Annotation


class ProductivityDashboardAPI(APIView):
    """Admin-only productivity dashboard with filtering by date, user, and project."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            raise PermissionDenied

        annotations = Annotation.objects.filter(
            project__organization=request.user.active_organization,
            was_cancelled=False,
        )

        # Apply filters
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        user_id = request.query_params.get('user_id')
        project_id = request.query_params.get('project_id')

        if date_from:
            annotations = annotations.filter(created_at__gte=date_from)
        if date_to:
            annotations = annotations.filter(created_at__lte=date_to)
        if user_id:
            annotations = annotations.filter(completed_by_id=user_id)
        if project_id:
            annotations = annotations.filter(project_id=project_id)

        # Summary stats
        summary = annotations.aggregate(
            total_annotations=Count('id'),
            avg_lead_time=Avg('lead_time'),
            total_accepted=Count('id', filter=Q(last_action='accepted')),
            total_rejected=Count('id', filter=Q(last_action='rejected')),
            total_submitted=Count('id', filter=Q(last_action='submitted')),
        )

        # Per-user breakdown
        per_user = list(
            annotations.values(
                'completed_by__id',
                'completed_by__email',
                'completed_by__first_name',
                'completed_by__last_name',
            )
            .annotate(
                count=Count('id'),
                avg_time=Avg('lead_time'),
                accepted=Count('id', filter=Q(last_action='accepted')),
                rejected=Count('id', filter=Q(last_action='rejected')),
            )
            .order_by('-count')
        )

        # Per-day activity
        per_day = list(
            annotations.annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        return Response({
            'summary': summary,
            'per_user': per_user,
            'per_day': per_day,
        })


class Echo:
    """Helper that implements just the write method of a file-like interface."""

    def write(self, value):
        return value


class ProductivityExportAPI(APIView):
    """Admin-only CSV export of per-user productivity data."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            raise PermissionDenied

        annotations = Annotation.objects.filter(
            project__organization=request.user.active_organization,
            was_cancelled=False,
        )

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        project_id = request.query_params.get('project_id')

        if date_from:
            annotations = annotations.filter(created_at__gte=date_from)
        if date_to:
            annotations = annotations.filter(created_at__lte=date_to)
        if project_id:
            annotations = annotations.filter(project_id=project_id)

        per_user = (
            annotations.values(
                'completed_by__email',
                'completed_by__first_name',
                'completed_by__last_name',
            )
            .annotate(
                total=Count('id'),
                avg_time=Avg('lead_time'),
                accepted=Count('id', filter=Q(last_action='accepted')),
                rejected=Count('id', filter=Q(last_action='rejected')),
                submitted=Count('id', filter=Q(last_action='submitted')),
            )
            .order_by('-total')
        )

        def generate_csv():
            buf = Echo()
            writer = csv.writer(buf)
            yield writer.writerow([
                'Email', 'First Name', 'Last Name',
                'Total Annotations', 'Avg Time (sec)',
                'Accepted', 'Rejected', 'Submitted',
            ])
            for row in per_user:
                avg_time = round(row['avg_time'], 1) if row['avg_time'] else ''
                yield writer.writerow([
                    row['completed_by__email'],
                    row['completed_by__first_name'],
                    row['completed_by__last_name'],
                    row['total'],
                    avg_time,
                    row['accepted'],
                    row['rejected'],
                    row['submitted'],
                ])

        response = StreamingHttpResponse(generate_csv(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="productivity_report.csv"'
        return response
