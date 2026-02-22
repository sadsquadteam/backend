from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from interaction.models.report import Report
from interaction.serializers.report import ReportSerializer


class ReportCreateView(generics.CreateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
