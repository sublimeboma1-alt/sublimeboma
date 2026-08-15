from django.db.models.signals import post_save
from django.dispatch import receiver

from sub_app.frais_scolaires.models import Paiement
from .services import create_payment_distribution


@receiver(post_save, sender=Paiement)
def distribute_valid_payment(sender, instance, created, **kwargs):
    if created:
        create_payment_distribution(instance)
