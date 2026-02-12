import qrcode
from PIL import Image
from pathlib import Path
from api.settings import settings


class QRGenerator:
    """Génération QR codes avec overlay logo optionnel"""

    def generate_qr_code(self, intervention_id: str) -> Image.Image:
        """
        Génère QR code pointant vers intervention

        Args:
            intervention_id: UUID intervention

        Returns:
            PIL Image object
        """
        # URL QR code
        qr_data = f"{settings.EXPORT_QR_BASE_URL}/{intervention_id}"

        # Créer QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

        # Overlay logo si configuré
        logo_path = Path(settings.EXPORT_QR_LOGO_PATH)
        if logo_path.exists():
            try:
                logo = Image.open(logo_path)

                # Redimensionner logo (20% taille QR)
                qr_width, qr_height = qr_img.size
                logo_size = int(qr_width * 0.2)
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

                # Convertir logo en RGB si nécessaire
                if logo.mode != 'RGB':
                    logo = logo.convert('RGB')

                # Centrer logo
                logo_pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
                qr_img.paste(logo, logo_pos)
            except Exception:
                # Si erreur logo, continuer sans (QR code reste valide)
                pass

        return qr_img
