from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from jobs.models import Job
from jobs.utils import extract_job_uid

from .authentication import ExtensionTokenAuthentication
from .models import JobScreenshot


class ScreenshotUploadView(APIView):
    """Receives a screenshot POSTed by the Chrome extension and attaches it to
    the matching Job (matched by job_uid extracted from the tab's Upwork URL).

    Job creation is exclusively owned by Gmail ingestion — if no matching Job
    exists, this returns 404 rather than creating a stub.
    """

    authentication_classes = [ExtensionTokenAuthentication]
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]

    def post(self, request):
        if not request.successful_authenticator:
            return Response({"detail": "Missing or invalid Authorization token."}, status=status.HTTP_401_UNAUTHORIZED)

        tab_url = request.data.get("tab_url")
        image = request.data.get("image")
        if not tab_url or not image:
            return Response({"detail": "tab_url and image are required."}, status=status.HTTP_400_BAD_REQUEST)

        job_uid = extract_job_uid(tab_url)
        if not job_uid:
            return Response(
                {"detail": "Could not extract a job identifier from tab_url."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            job = Job.objects.get(job_uid=job_uid)
        except Job.DoesNotExist:
            return Response(
                {"detail": "No job found for this URL — was it ingested from an alert email?"},
                status=status.HTTP_404_NOT_FOUND,
            )

        next_order = job.screenshots.count()
        screenshot = JobScreenshot.objects.create(job=job, image=image, order=next_order)

        if job.status == Job.Status.NEW or job.status == Job.Status.REVIEWED:
            job.status = Job.Status.SCREENSHOTS_ADDED
            job.save(update_fields=["status", "updated_at"])

        return Response(
            {"id": screenshot.id, "job_id": job.id, "order": screenshot.order},
            status=status.HTTP_201_CREATED,
        )
