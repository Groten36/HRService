from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Department, Employee, Section


@receiver(post_save, sender=Department)
@receiver(post_save, sender=Section)
def refresh_employee_search_text(sender, instance, created, **kwargs):
    """Po zmianie nazwy wydziału/działu odśwież tekst wyszukiwania pracowników."""
    if created:
        return
    lookup = {'department': instance} if sender is Department else {'section': instance}
    for employee in Employee.objects.filter(**lookup).select_related('department', 'section'):
        Employee.objects.filter(pk=employee.pk).update(search_text=employee.build_search_text())
