from django.db.models import Count, Q

from .models import Category


def nav_categories(request):
    """Kategorie do menu rozwijanego wraz z liczbą opublikowanych dokumentów."""
    return {
        'nav_categories': Category.objects.annotate(
            doc_count=Count('documents', filter=Q(documents__is_published=True))
        ),
    }
