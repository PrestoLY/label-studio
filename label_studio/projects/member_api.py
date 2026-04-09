"""API endpoints for managing project membership (admin only)."""

from django.shortcuts import get_object_or_404
from projects.models import Project, ProjectMember
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User


class ProjectMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMember
        fields = ('id', 'user', 'user_email', 'user_name', 'project', 'enabled', 'created_at')
        read_only_fields = ('id', 'project', 'created_at')

    def get_user_name(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'.strip() or obj.user.email


class ProjectMemberListAPI(APIView):
    """List and add project members. Admin only."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied
        project = get_object_or_404(Project, pk=pk)
        members = ProjectMember.objects.filter(project=project).select_related('user')
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied
        project = get_object_or_404(Project, pk=pk)
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, pk=user_id)
        member, created = ProjectMember.objects.get_or_create(
            user=user, project=project, defaults={'enabled': True}
        )
        if not created and not member.enabled:
            member.enabled = True
            member.save(update_fields=['enabled'])

        serializer = ProjectMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ProjectMemberDetailAPI(APIView):
    """Remove a project member. Admin only."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, member_pk):
        if not request.user.is_staff:
            raise PermissionDenied
        member = get_object_or_404(ProjectMember, pk=member_pk, project_id=pk)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
