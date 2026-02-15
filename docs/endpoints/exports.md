# Exports

Génération de documents PDF et QR codes pour les interventions.

> Voir aussi : [Interventions](interventions.md) | [Purchase Requests](purchase-requests.md)

---

## `GET /exports/interventions/{id}/pdf`

Génère un rapport PDF complet pour une intervention.

**Auth** : JWT Bearer token requis

### Headers

```
Authorization: Bearer eyJhbG...
```

### Réponse `200`

- Content-Type: `application/pdf`
- Filename: `{code_intervention}.pdf` (ex: `CN001-REA-20260113-QC.pdf`)
- ETag: supporté pour cache client

### Contenu du PDF

- En-tête : logo, titre, code intervention, QR code
- Informations intervention : type, priorité, statut, dates, technicien, équipement
- Actions réalisées avec technicien, temps passé, catégorie, complexité
- Historique des changements de statut
- Demandes d'achat liées (8 colonnes : qté, réf. interne, désignation, fournisseur, réf. fournisseur, fabricant, réf. fabricant, urgence)
- Pied de page : version API, version template, code intervention, pagination (Page X / Y), date de génération

### Erreurs

| Code | Description |
|---|---|
| 400 | Format UUID invalide |
| 401 | JWT manquant ou invalide |
| 404 | Intervention non trouvée |
| 500 | Échec de génération PDF |

### Exemple

```bash
curl -X GET "http://localhost:8000/exports/interventions/5ecf60d5-8471-4739-8ba8-0fdad7b51781/pdf" \
     -H "Authorization: Bearer eyJhbG..." \
     -o intervention.pdf
```

---

## `GET /exports/interventions/{id}/qrcode`

Génère un QR code pointant vers la page détail de l'intervention dans le frontend.

**Auth** : Public (conçu pour impression sur rapports physiques)

### Réponse `200`

- Content-Type: `image/png`
- Filename: `{code_intervention}.png` (inline, pas téléchargement)
- Cache: `public, max-age=3600` (1 heure)

### Contenu du QR

URL : `{EXPORT_QR_BASE_URL}/{intervention_id}`

Exemple : `http://localhost:5173/interventions/5ecf60d5-8471-4739-8ba8-0fdad7b51781`

### Caractéristiques

- Correction d'erreur élevée (`ERROR_CORRECT_H`) pour fiabilité du scan
- Logo overlay optionnel (configurable via `EXPORT_QR_LOGO_PATH`)
- Optimisé pour impression sur papier

### Erreurs

| Code | Description |
|---|---|
| 400 | Format UUID invalide |
| 404 | Intervention non trouvée |
| 500 | Échec de génération QR |

### Exemple

```bash
curl -X GET "http://localhost:8000/exports/interventions/5ecf60d5-8471-4739-8ba8-0fdad7b51781/qrcode" \
     -o qrcode.png
```

---

## Configuration

| Variable | Défaut | Description |
|---|---|---|
| `EXPORT_TEMPLATE_DIR` | `config/templates` | Dossier des templates HTML |
| `EXPORT_TEMPLATE_FILE` | `fiche_intervention_v8.html` | Fichier template |
| `EXPORT_TEMPLATE_VERSION` | `v8.0` | Version du template |
| `EXPORT_TEMPLATE_DATE` | `2025-10-03` | Date de version du template |
| `EXPORT_QR_BASE_URL` | `http://localhost:5173/interventions` | URL frontend pour QR |
| `EXPORT_QR_LOGO_PATH` | `config/templates/logo.png` | Logo overlay QR |
