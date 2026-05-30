from django.db import models

from common.models import GenericModel


class Prefix(GenericModel):
    title = models.CharField(max_length=400,null=True,blank=True)

    class Meta:
        verbose_name = "prefix"
        verbose_name_plural = "prefix"
        db_table = "prefix"
        
    def __str__(self):
        return self.title or "none"
    

class Suffix(GenericModel):
    title = models.CharField(max_length=400,null=True,blank=True)

    class Meta:
        verbose_name = "suffix"
        verbose_name_plural = "suffix"
        db_table = "suffix"
        
    def __str__(self):
        return self.title or "none"
    

class Seat(GenericModel):
    prefix = models.ForeignKey(
        Prefix,
        on_delete=models.CASCADE,
        related_name="seat_prefix",
        null=True,
        blank=True
    )
    suffix = models.ForeignKey(
        Suffix,
        on_delete=models.CASCADE,
        related_name="seat_suffix",
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "seat"
        verbose_name_plural = "seats"
        db_table = "seat"
        
    def __str__(self):
        return f"{self.prefix} {self.suffix}".strip() or "Unnamed Seat"