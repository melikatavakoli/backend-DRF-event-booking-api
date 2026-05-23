from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from common.paginations import CustomLimitOffsetPagination
from core.models import CoreUser
from core.serializers import (
    ChangePasswordSerializer,
    LoginOtpSerializer,
    LoginSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    SendOTPSerializer,
    UserListSerializer,
)
from core.types import RoleType

User = get_user_model()

TokenPairSerializer = inline_serializer(
    name="TokenPair",
    fields={
        "access": serializers.CharField(),
        "refresh": serializers.CharField(),
    },
)

LogoutSerializer = inline_serializer(
    name="Logout",
    fields={
        "refresh": serializers.CharField(),
    },
)


class RegisterWithOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses=TokenPairSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class SendOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=SendOTPSerializer, responses=None)
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)


class LoginOTPView(APIView):
    @extend_schema(request=LoginOtpSerializer, responses=TokenPairSerializer)
    def post(self, request):
        serializer = LoginOtpSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    @extend_schema(request=LoginSerializer, responses=TokenPairSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=LogoutSerializer, responses=None)
    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"detail": "refresh token required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"detail": "logout successful"}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    @extend_schema(request=ResetPasswordSerializer, responses=TokenPairSerializer)
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer, responses=None)
    def patch(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)


class UserListView(ListAPIView):
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["status"]
    ordering_fields = ["__created_at", "full_name"]
    search_fields = ["mobile", "first_name", "last_name"]

    def get_queryset(self):
        user = self.request.user

        if user.role == RoleType.ADMIN:
            return User.all_objects.all()
        elif user.role == RoleType.STAFF:
            return User.objects.filter(role=RoleType.PATIENT)
        else:
            return User.objects.filter(id=user.id)


class UserListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserListSerializer
    queryset = CoreUser.objects.all()
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = ("mobile",)
    search_fields = ("first_name", "last_name", "mobile")
    ordering = ("__created_at",)
    ordering_fields = ("first_name", "__created_at")

    @extend_schema(
        responses=UserListSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
