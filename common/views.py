from rest_framework import viewsets


class BaseModelViewSet(viewsets.ModelViewSet):

    def perform_create(self, serializer):

        if self.request.user.is_authenticated:
            serializer.save(
                _created_by=self.request.user,
                _updated_by=self.request.user,
            )
        else:
            serializer.save()

    def perform_update(self, serializer):

        if self.request.user.is_authenticated:
            serializer.save(
                _updated_by=self.request.user,
            )
        else:
            serializer.save()