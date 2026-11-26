from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import Document


@receiver(post_delete, sender=Document)
def delete_file_on_document_delete(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)


@receiver(pre_save, sender=Document)
def delete_old_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    old = Document.objects.filter(pk=instance.pk).values_list('file', flat=True).first()
    if old and old != instance.file.name:
        instance.file.storage.delete(old)
