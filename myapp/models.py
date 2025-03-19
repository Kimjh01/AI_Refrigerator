from django.db import models
from django.core.exceptions import ValidationError
import json

class FoodItem(models.Model):
    FOOD_SOURCE_CHOICES = [
        ('barcode', '바코드 스캔'),
        ('receipt', '영수증 스캔'),
        ('manual', '수동 입력'),
        ('ai_scan', 'AI 스캔')  # AI 스캔 추가
    ]

    item_data = models.JSONField(verbose_name='식품 정보', default=dict, blank=True)
    source = models.CharField(
        max_length=10,
        choices=FOOD_SOURCE_CHOICES,
        default='manual',
        verbose_name='입력 방식'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일')

    name = models.CharField(max_length=200, blank=True, null=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.IntegerField(default=1)
    purchase_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    storage_type = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)

    def clean(self):
        """데이터 유효성 검사"""
        if self.source != 'manual' and self.item_data:
            required_fields = ['food_name']
            for field in required_fields:
                if field not in self.item_data:
                    raise ValidationError(f'{field} is required in item_data')

    def __str__(self):
        return self.name or self.item_data.get("food_name", "Unknown Food Item")

    def get_expiry_date(self):
        """소비기한 반환"""
        return self.expiry_date or self.item_data.get("expiration_date") or self.item_data.get("expiry_date")

    def get_purchase_date(self):
        """구입일 반환"""
        return self.purchase_date or self.item_data.get("purchase_date")

    def save_barcode_data(self, product_info, capture_date):
        """바코드 스캔 데이터 저장"""
        self.source = 'barcode'
        self.name = product_info.get('name')
        self.barcode = product_info.get('barcode')
        self.purchase_date = capture_date
        self.item_data = {
            'food_name': self.name,
            'purchase_date': str(capture_date),
            'barcode': self.barcode,
            'additional_info': product_info
        }
        self.save()

    def save_receipt_data(self, receipt_data):
        """영수증 스캔 데이터 저장"""
        self.source = 'receipt'
        self.item_data = receipt_data
        self.name = receipt_data.get('food_name')
        self.save()

    class Meta:
        verbose_name = '식품'
        verbose_name_plural = '식품 목록'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
        ]

class Note(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note {self.id}"
