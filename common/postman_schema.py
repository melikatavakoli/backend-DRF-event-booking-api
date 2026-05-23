from drf_spectacular.views import SpectacularAPIView


class DownloadSchemaView(SpectacularAPIView):
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response["Content-Disposition"] = 'attachment; filename="openapi-schema.json"'
        return response
