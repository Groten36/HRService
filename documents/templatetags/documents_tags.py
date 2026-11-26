from django import template

register = template.Library()

ICONS = {'PDF': 'pdf', 'DOC': 'doc', 'DOCX': 'doc', 'ODT': 'doc',
         'XLS': 'xls', 'XLSX': 'xls', 'ODS': 'xls', 'PNG': 'img', 'JPG': 'img', 'JPEG': 'img',
         'EXE': 'app', 'MSI': 'app', 'MSIX': 'app', 'DMG': 'app', 'PKG': 'app',
         'DEB': 'app', 'RPM': 'app', 'APPIMAGE': 'app', 'ZIP': 'zip', '7Z': 'zip'}


@register.filter
def file_kind(extension):
    return ICONS.get((extension or '').upper(), 'file')
