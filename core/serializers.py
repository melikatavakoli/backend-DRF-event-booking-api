import logging
import random
import string
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework import serializers
from common.serializers import GenericModelSerializer
from core.models import CoreUser
from .tasks import send_registry_sms, send_verification_sms
from .choices import RoleType, StatusType
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator

User = get_user_model()
logger = logging.getLogger(__name__)


class UserListSerializer(GenericModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = CoreUser
        fields = GenericModelSerializer.Meta.fields + (
            "mobile",
            "full_name",
            "role",
            "email",
        )


class RegisterSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    re_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    code = serializers.CharField(max_length=6, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)

    def validate(self, data):
        mobile = data.get("mobile")
        code = data.get("code")
        password = data.get("password")
        re_password = data.get("re_password")

        mobile_validator = RegexValidator(
            regex=r"^09\d{9}$", message="فرمت شماره موبایل نادرست است."
        )

        try:
            mobile_validator(mobile)
        except DjangoValidationError:
            raise serializers.ValidationError(
                {"mobile": "فرمت شماره موبایل نادرست است."}
            )

        if password != re_password:
            raise serializers.ValidationError("رمز عبور مطابقت ندارد.")
        if User.objects.filter(mobile=mobile).exists():
            raise serializers.ValidationError("این موبایل قبلاً ثبت شده است.")

        if code:
            redis_conn = get_redis_connection("default")
            stored_code = redis_conn.get(f"verification_code:{mobile}")
            if not stored_code:
                raise serializers.ValidationError({"code": "کد تأیید یافت نشد."})
            if stored_code.decode("utf-8") != code:
                raise serializers.ValidationError({"code": "کد تأیید اشتباه است."})
        return data

    @transaction.atomic
    def save(self):
        data = self.validated_data
        user = CoreUser.objects.create_user(
            mobile=data["mobile"],
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            role=RoleType.PATIENT,
            status=StatusType.ACTIVE,
        )
        redis_conn = get_redis_connection("default")
        redis_conn.delete(f"verification_code:{data['mobile']}")
        return user


class SendOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    mode = serializers.ChoiceField(choices=["register", "login", "forget_password"])

    def validate_mobile(self, value):
        if not value.isdigit() or len(value) != 11 or not value.startswith("09"):
            raise serializers.ValidationError("شماره موبایل معتبر نیست.")
        return value

    def validate(self, attrs):
        mobile = attrs["mobile"]
        mode = attrs["mode"]
        user_exists = User.objects.filter(mobile=mobile).exists()
        if mode == "register" and user_exists:
            raise serializers.ValidationError("این شماره قبلاً ثبت‌نام شده است.")
        if mode in ["login", "forget_password"] and not user_exists:
            raise serializers.ValidationError("این شماره یافت نشد.")
        return attrs

    def create(self, validated_data):
        mobile = validated_data["mobile"]
        mode = validated_data["mode"]
        verification_code = "".join(random.choices(string.digits, k=5))
        redis_key = f"verification_code:{mobile}"
        try:
            redis_conn = get_redis_connection("default")
            redis_conn.setex(redis_key, 300, verification_code)
            if mode == "login":
                send_verification_sms.delay(mobile, verification_code)
            elif mode == "register":
                send_registry_sms.delay(mobile, verification_code)
            elif mode == "forget_password":
                send_verification_sms.delay(mobile, verification_code)
        except Exception as e:
            logger.error(f"OTP failed for {mobile}: {e}")
            raise serializers.ValidationError("ارسال کد تأیید ناموفق بود.")
        return validated_data


class LoginOtpSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        mobile = data.get("mobile")
        code = data.get("code")

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            raise serializers.ValidationError("کاربری با این شماره یافت نشد.")
        if user.status != StatusType.ACTIVE:
            raise serializers.ValidationError("حساب کاربری فعال نیست.")
        redis_conn = get_redis_connection("default")
        stored_code = redis_conn.get(f"verification_code:{mobile}")
        if not stored_code or stored_code.decode() != code:
            raise serializers.ValidationError("کد تأیید نامعتبر است.")
        redis_conn.delete(f"verification_code:{mobile}")
        data["user"] = user
        return data


class LoginSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        mobile = data.get("mobile")
        password = data.get("password")

        try:
            user = CoreUser.objects.get(mobile=mobile)
        except CoreUser.DoesNotExist:
            raise serializers.ValidationError("کاربری با این موبایل یافت نشد.")
        if user.status != StatusType.ACTIVE:
            raise serializers.ValidationError("حساب کاربری فعال نیست.")
        if not user.check_password(password):
            raise serializers.ValidationError("رمز عبور نامعتبر است.")
        data["user"] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    re_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError("رمز عبور فعلی اشتباه است.")
        if attrs["password"] != attrs["re_password"]:
            raise serializers.ValidationError("رمز عبور مطابقت ندارد.")
        return attrs

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["password"])
        user.password__updated_at = timezone.now()
        user.save(update_fields=["password", "password__updated_at"])
        return user


class ResetPasswordSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True)
    re_password = serializers.CharField(write_only=True)

    def validate(self, data):
        mobile = data["mobile"]
        code = data["code"]
        password = data["password"]
        re_password = data["re_password"]
        if password != re_password:
            raise serializers.ValidationError("رمز عبور مطابقت ندارد.")
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            raise serializers.ValidationError("کاربری با این شماره یافت نشد.")
        redis_conn = get_redis_connection("default")
        stored_code = redis_conn.get(f"verification_code:{mobile}")
        if not stored_code or stored_code.decode() != code:
            raise serializers.ValidationError("کد تأیید نامعتبر است.")
        data["user"] = user
        return data

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["password"])
        user.save()
        redis_conn = get_redis_connection("default")
        redis_conn.delete(f"verification_code:{self.validated_data['mobile']}")
        return user