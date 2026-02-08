"""
Templates d'export pour les commandes fournisseurs.

Ce fichier contient tous les templates configurables pour les exports CSV et email.
Modifiez ces templates selon vos besoins sans toucher au code des routes.

Variables disponibles dans les templates :
- order_number : Numéro de la commande (ex: "SO-2026-001")
- supplier : Dict avec {name, email, code, contact_name, phone}
- lines : Liste de lignes de commande, chaque ligne contient :
    - stock_item : {name, ref, spec, unit, family_code, sub_family_code}
    - manufacturer_item : {manufacturer, ref} (peut être None)
    - standard_spec : {name} (peut être None)
    - quantity : int
    - unit_price : float (peut être None)
    - total_price : float (peut être None)
    - manufacturer : str (direct, peut être None)
    - manufacturer_ref : str (direct, peut être None)
    - purchase_requests : Liste [{item_label, allocated_quantity, requester_name}]

Contraintes :
- CSV : Utiliser le séparateur ';' pour compatibilité Excel français
- Email text : Maximum 80 caractères par ligne recommandé
- Email HTML : Utiliser inline styles (pas de CSS externe)
- Toujours gérer les valeurs None avec .get() ou valeurs par défaut
"""


def get_csv_headers():
    """
    En-têtes du fichier CSV.

    Ordre des colonnes dans le CSV exporté.
    Modifiez cette liste pour ajouter/supprimer/réordonner les colonnes.

    Returns:
        list[str]: Liste des en-têtes de colonnes
    """
    return [
        'Article',
        'Référence',
        'Spécification',
        'Fabricant',
        'Réf. Fabricant',
        'Quantité',
        'Unité',
        'Prix unitaire',
        'Prix total',
        'Demandes liées'
    ]


def format_csv_row(line):
    """
    Formate une ligne de commande pour l'export CSV.

    Cette fonction extrait et formate les données d'une ligne de commande
    selon l'ordre défini dans get_csv_headers().

    Args:
        line (dict): Ligne de commande avec stock_item, manufacturer_item, etc.

    Returns:
        list: Valeurs formatées dans l'ordre des colonnes

    Exemples de personnalisation :
        - Ajouter une colonne : Ajouter un élément dans le return
        - Changer le format du prix : Modifier f"{line.get('unit_price', ''):.2f}€"
        - Ajouter une condition : if stock_item.get('urgent') then ...
    """
    stock_item = line.get('stock_item') or {}
    manufacturer_item = stock_item.get('manufacturer_item') or {}

    # Infos demandes d'achat liées
    # Format: "Article X (x2), Article Y (x1)"
    pr_list = line.get('purchase_requests', [])
    pr_info = ', '.join([
        f"{pr.get('item_label', 'N/A')} (x{pr.get('allocated_quantity', 0)})"
        for pr in pr_list
    ]) if pr_list else ''

    return [
        stock_item.get('name', ''),
        stock_item.get('ref', ''),
        stock_item.get('spec', ''),
        manufacturer_item.get('manufacturer', '') or line.get(
            'manufacturer', ''),
        manufacturer_item.get('ref', '') or line.get('manufacturer_ref', ''),
        line.get('quantity', 0),
        stock_item.get('unit', ''),
        line.get('unit_price', ''),
        line.get('total_price', ''),
        pr_info
    ]


def get_email_subject(order_number):
    """
    Sujet de l'email de commande.

    Args:
        order_number (str): Numéro de la commande

    Returns:
        str: Sujet de l'email

    Exemples de personnalisation :
        - Ajouter urgence : f"[URGENT] Commande {order_number}"
        - Ajouter date : f"Commande {order_number} - {datetime.now().strftime('%d/%m/%Y')}"
        - Ajouter entreprise : f"[ACME Corp] Commande {order_number}"
    """
    return f"Commande {order_number} - Demande de prix"


def get_email_body_text(order_number, supplier_name, lines):
    """
    Corps de l'email en texte brut (fallback pour clients email sans HTML).

    Format simple et lisible, maximum 80 caractères par ligne recommandé.

    Args:
        order_number (str): Numéro de la commande
        supplier_name (str): Nom du fournisseur
        lines (list): Liste des lignes de commande

    Returns:
        str: Corps de l'email en texte brut

    Conseils :
        - Rester simple et lisible
        - Éviter les caractères spéciaux (é, è, à → remplacer par e, a)
        - Utiliser des séparateurs clairs (-, =, *)
        - Tester l'affichage sur mobile (largeur 40 caractères max)
    """
    body_lines = [
        f"Bonjour,",
        "",
        f"Veuillez trouver ci-dessous notre demande de commande n°{order_number}.",
        "",
        "Articles commandés :",
        "-" * 40,
    ]

    for line in lines:
        stock_item = line.get('stock_item') or {}
        manufacturer_item = stock_item.get('manufacturer_item') or {}

        article_name = stock_item.get('name', 'Article')
        article_ref = stock_item.get('ref', '')
        spec = stock_item.get('spec', '')
        manufacturer = manufacturer_item.get(
            'manufacturer', '') or line.get('manufacturer', '')
        manufacturer_ref = manufacturer_item.get(
            'ref', '') or line.get('manufacturer_ref', '')
        quantity = line.get('quantity', 0)
        unit = stock_item.get('unit', 'pcs')

        body_lines.append(f"• {article_name}")
        if article_ref:
            body_lines.append(f"  Réf: {article_ref}")
        if spec:
            body_lines.append(f"  Spec: {spec}")
        if manufacturer:
            body_lines.append(f"  Fabricant: {manufacturer}")
        if manufacturer_ref:
            body_lines.append(f"  Réf. fabricant: {manufacturer_ref}")
        body_lines.append(f"  Quantité: {quantity} {unit}")
        body_lines.append("")

    body_lines.extend([
        "-" * 40,
        "",
        "Merci de nous faire parvenir votre meilleur prix et délai de livraison.",
        "",
        "Cordialement,",
    ])

    return "\n".join(body_lines)


def get_email_body_html(order_number, supplier_name, lines):
    """
    Corps de l'email en HTML (version riche avec tableau).

    Contraintes HTML email :
        - Utiliser UNIQUEMENT des styles inline (pas de <style> externe)
        - Utiliser des tables pour la mise en page (pas de flexbox/grid)
        - Tester sur Outlook, Gmail, Apple Mail
        - Éviter JavaScript, CSS3 avancé, animations
        - Largeur max recommandée : 600px
        - Utiliser des couleurs web-safe (#RRGGBB)

    Args:
        order_number (str): Numéro de la commande
        supplier_name (str): Nom du fournisseur
        lines (list): Liste des lignes de commande

    Returns:
        str: Corps de l'email en HTML

    Exemples de personnalisation :
        - Changer les couleurs : Modifier les background-color, color
        - Ajouter logo : <img src="https://..." style="width:150px">
        - Ajouter colonnes : Ajouter <th> et <td> dans la boucle
        - Changer police : style="font-family: Arial, sans-serif"
    """
    html_lines = [
        "<html>",
        "<body style='font-family: Arial, sans-serif; font-size: 14px; color: #333;'>",
        "<p>Bonjour,</p>",
        f"<p>Veuillez trouver ci-dessous notre demande de commande n°<strong>{order_number}</strong>.</p>",
        "<h3 style='color: #2563EB; margin-top: 20px;'>Articles commandés :</h3>",
        "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse: collapse; width: 100%; max-width: 800px;'>",
        "<thead>",
        "<tr style='background-color: #f0f0f0;'>",
        "<th style='text-align: left; padding: 10px; border: 1px solid #ddd;'>Article</th>",
        "<th style='text-align: left; padding: 10px; border: 1px solid #ddd;'>Référence</th>",
        "<th style='text-align: left; padding: 10px; border: 1px solid #ddd;'>Spécification</th>",
        "<th style='text-align: left; padding: 10px; border: 1px solid #ddd;'>Fabricant</th>",
        "<th style='text-align: left; padding: 10px; border: 1px solid #ddd;'>Réf. Fabricant</th>",
        "<th style='text-align: center; padding: 10px; border: 1px solid #ddd;'>Quantité</th>",
        "</tr>",
        "</thead>",
        "<tbody>",
    ]

    for idx, line in enumerate(lines):
        stock_item = line.get('stock_item') or {}
        manufacturer_item = stock_item.get('manufacturer_item') or {}

        # Alternance de couleurs pour lisibilité
        bg_color = '#ffffff' if idx % 2 == 0 else '#f9f9f9'

        html_lines.append(f"<tr style='background-color: {bg_color};'>")
        html_lines.append(
            f"<td style='padding: 8px; border: 1px solid #ddd;'>{stock_item.get('name', '')}</td>")
        html_lines.append(
            f"<td style='padding: 8px; border: 1px solid #ddd;'>{stock_item.get('ref', '')}</td>")
        html_lines.append(
            f"<td style='padding: 8px; border: 1px solid #ddd;'>{stock_item.get('spec', '')}</td>")
        html_lines.append(
            f"<td style='padding: 8px; border: 1px solid #ddd;'>{manufacturer_item.get('manufacturer', '') or line.get('manufacturer', '')}</td>")
        html_lines.append(
            f"<td style='padding: 8px; border: 1px solid #ddd;'>{manufacturer_item.get('ref', '') or line.get('manufacturer_ref', '')}</td>")
        html_lines.append(
            f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{line.get('quantity', 0)} {stock_item.get('unit', 'pcs')}</td>")
        html_lines.append("</tr>")

    html_lines.extend([
        "</tbody>",
        "</table>",
        "<p style='margin-top: 20px;'>Merci de nous faire parvenir votre meilleur prix et délai de livraison.</p>",
        "<p>Cordialement,</p>",
        "</body>",
        "</html>",
    ])

    return "\n".join(html_lines)


def get_csv_filename(order_number):
    """
    Nom du fichier CSV exporté.

    Contraintes :
        - Pas d'espaces (utiliser _ ou -)
        - Pas de caractères spéciaux (é, è, /, \\, :, etc.)
        - Extension .csv obligatoire
        - Maximum 255 caractères

    Args:
        order_number (str): Numéro de la commande

    Returns:
        str: Nom du fichier

    Exemples de personnalisation :
        - Ajouter date : f"commande_{order_number}_{datetime.now().strftime('%Y%m%d')}.csv"
        - Ajouter fournisseur : f"commande_{order_number}_{supplier_name}.csv"
        - Format différent : f"SO_{order_number}.csv"
    """
    return f"commande_{order_number}.csv"
