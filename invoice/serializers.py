from decimal import Decimal
from rest_framework import serializers
from django.db import transaction
from decimal import Decimal, InvalidOperation
from invoice.models import Invoice, Item
from order.serializers import OrderSerializer
from product.serializers import ProductListSerializer


class InvoiceItemSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Item
        fields = [
            'row_number',
            'product_code',
            'description',
            'quantity',
            'unit_price',
            'discount_amount',
            'discount_percent',
        ]

    def validate_quantity(self, value):
        if not value or value == "":
            value = "0"
        try:
            if float(value) <= 0:
                raise serializers.ValidationError("تعداد باید بیشتر از صفر باشد.")
        except:
            raise serializers.ValidationError("مقدار تعداد معتبر نیست.")
        return value
    
    def validate_unit_price(self, value):
        if not value or value == "":
            value = "0"
        try:
            if float(value) <= 0:
                raise serializers.ValidationError("قیمت واحد باید بیشتر از صفر باشد.")
        except:
            raise serializers.ValidationError("مقدار قیمت واحد معتبر نیست.")
        return value


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(
        many=True, 
        read_only=True, 
        required=False
        )
    order = OrderSerializer()
    product = ProductListSerializer()
    user = serializers.SerializerMethodField()
    total_amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True, 
        )
    total_discount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True, 
        )
    total_tax = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True, 
        )
    final_amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True, 
        )

    class Meta:
        model = Invoice
        fields = [
            'id',
            'user',
            'invoice_number',
            'tracking_code',
            'fiscal_memory_number',
            'fiscal_memory_serial',
            'pos_serial',
            'description',
            'invoice_date',
            'issue_date',
            'status',
            'product',
            'order',
            'items',
            'total_amount',
            'total_discount',
            'total_tax',
            'final_amount',
        ]
        read_only_fields = [
            "invoice_number", 
            "tracking_code", 
            "total_amount", 
            "total_discount", 
            "total_tax", 
            "final_amount"
            ]

    def get_user(self, obj):
        if not obj.user:
            return None
        return {
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'full_name': getattr(obj.user, 'full_name', ''),
            'mobile': obj.user.mobile,
        }


class InvoiceWriteSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(
        many=True, 
        write_only=True, 
        required=True 
        )

    class Meta:
        model = Invoice
        fields = [
            "id", "order", "description", "items", "user",
            "invoice_date", "issue_date", "tracking_code",
            "fiscal_memory_number", "fiscal_memory_serial", "pos_serial",
        ]
        read_only_fields = ["id"] 
    
    def validate(self, attrs):
        if not attrs.get("order"):
            raise serializers.ValidationError({"order": "فیلد order الزامی است."})
        
        items_data = attrs.get("items", [])
        if not items_data:
            raise serializers.ValidationError({"items": "حداقل یک آیتم برای فاکتور لازم است."})
        
        return attrs
    
    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        
        if not user:
            raise serializers.ValidationError({"detail": "کاربر احراز هویت نشده است."})
        
        items_data = validated_data.pop("items", [])
        
        with transaction.atomic():
            # حذف user اگر وجود دارد
            validated_data.pop('user', None)
            
            invoice = Invoice.objects.create(
                user=user,
                created_by=user,
                **validated_data
            )
            
            for idx, item_data in enumerate(items_data, start=1):
                # فقط ذخیره کنید، هیچ محاسبه‌ای نکنید
                Item.objects.create(
                    invoice=invoice,
                    row_number=idx,
                    product_code=item_data.get("product_code", ""),
                    description=item_data.get("description", ""),
                    quantity=item_data.get("quantity", "0"),
                    unit_price=item_data.get("unit_price", "0"),
                    discount_amount=item_data.get("discount_amount", "0"),
                    discount_percent=item_data.get("discount_percent", "0"),
                )
        
        return invoice


class InvoiceListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    items = InvoiceItemSerializer(
        many=True, 
        read_only=True, 
        required=False
        )
    order = OrderSerializer(read_only=True)
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id',
            "invoice_number",
            "created_at",
            'user',
            'status',
            'issue_date',
            'invoice_date',
            'order',
            'product',
            'items'
        ]


    def get_user(self, obj):
        if not obj.user:
            return None
        return {
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'full_name': getattr(obj.user, 'full_name', ''),
            'mobile': obj.user.mobile,
        }
        

class InvoiceAdminSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(
        many=True, 
        read_only=True
        )
    order = OrderSerializer()
    product = ProductListSerializer()
    user = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            'user',
            "invoice_number",
            "tracking_code",
            "fiscal_memory_number",
            "fiscal_memory_serial",
            "total_amount",
            "total_discount",
            "total_tax",
            "pos_serial",
            "description",
            "created_at",
            "items",
            'issue_date',
            "created_by",
            "status",
            "order",
            'product',
            'final_amount',
        ]
        read_only_fields = ["invoice_number"]

    def get_user(self, obj):
        if not obj.user:
            return None
        return {
            'first_name': obj.core_user.first_name,
            'last_name': obj.core_user.last_name,
            'full_name': getattr(obj.core_user, 'full_name', ''),
            'mobile': obj.core_user.mobile,
        }
        

