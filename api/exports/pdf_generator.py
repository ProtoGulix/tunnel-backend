from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from api.settings import settings
from api.errors.exceptions import RenderError
from datetime import datetime


class PDFGenerator:
    """Génération PDF avec WeasyPrint et Jinja2"""

    def __init__(self):
        template_dir = Path(settings.EXPORT_TEMPLATE_DIR)
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.env.filters['format_date'] = self._format_date
        self.env.filters['format_priority'] = self._format_priority

    def render_html(self, data: dict) -> str:
        """Rend le template Jinja2 avec les données"""
        try:
            template = self.env.get_template(settings.EXPORT_TEMPLATE_FILE)
            data['now'] = datetime.now().strftime('%Y-%m-%d')
            return template.render(**data)
        except Exception as e:
            raise RenderError(f"Erreur rendu template: {str(e)}")

    def generate_pdf(self, html_content: str) -> bytes:
        """Convertit HTML en PDF avec WeasyPrint"""
        try:
            pdf_bytes = HTML(string=html_content).write_pdf()
            return pdf_bytes
        except Exception as e:
            raise RenderError(f"Erreur génération PDF: {str(e)}")

    def _format_date(self, date_value) -> str:
        """Filtre Jinja2: formate date ISO en YYYY-MM-DD"""
        if not date_value:
            return "N/A"
        if isinstance(date_value, str):
            try:
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except:
                return date_value
        if hasattr(date_value, 'strftime'):
            return date_value.strftime('%Y-%m-%d')
        return str(date_value)

    def _format_priority(self, priority: str) -> str:
        """Filtre Jinja2: traduit codes priorité"""
        mapping = {
            'urgent': 'Urgent',
            'important': 'Important',
            'normale': 'Normal',
            'faible': 'Faible'
        }
        return mapping.get(priority, priority) if priority else "N/A"
