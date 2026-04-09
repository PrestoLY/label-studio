"""API endpoints for the admin review workflow (accept/reject annotations)."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from tasks.models import Annotation


class AnnotationAcceptAPI(APIView):
    """Accept a submitted annotation. Staff only."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied('Only staff can accept annotations.')
        annotation = get_object_or_404(Annotation, pk=pk)
        annotation.last_action = 'accepted'
        annotation.review_comment = request.data.get('comment', '')
        annotation.save(update_fields=['last_action', 'review_comment'])
        return Response({'status': 'accepted', 'annotation_id': annotation.pk})


class AnnotationRejectAPI(APIView):
    """Reject a submitted annotation and send it back for correction. Staff only."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied('Only staff can reject annotations.')
        annotation = get_object_or_404(Annotation, pk=pk)
        annotation.last_action = 'rejected'
        annotation.review_comment = request.data.get('comment', '')
        annotation.save(update_fields=['last_action', 'review_comment'])
        return Response({'status': 'rejected', 'annotation_id': annotation.pk})
