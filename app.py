import os
import re
import time
from typing import List

import gspread
from google.oauth2.service_account import Credentials

import config
from auditor import audit_prospect, est_un_vrai_prospect


def connecter_google_sheet():
    """Initialise la connexion avec Google Sheets via des identifiants sécurisés."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials_path = config.GOOGLE_CREDENTIALS_PATH

    if not os.path.exists(credentials_path):
        print(f"❌ Fichier d'identifiants introuvable: '{credentials_path}'. Assurez-vous qu'il existe localement.")
        return None

    try:
        creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open(config.GOOGLE_SHEET_NAME).sheet1
        return sheet
    except Exception as e:
        print(f"❌ Erreur de connexion à Google Sheets '{config.GOOGLE_SHEET_NAME}' : {e}")
        return None


def recuperer_urls_prospects(max_resultats: int) -> List[str]:
    """Extrait et filtre les URLs du fichier source 'google.txt'."""
    print("📂 Lecture du fichier local 'google.txt'...")
    urls_trouvees = []

    try:
        with open("google.txt", "r", encoding="utf-8") as f:
            contenu = f.read()

        pattern = r'(?:https?://|www\.)[^\s\"\'<>(),]+|(?:[a-zA-Z0-9-]+\.)+(?:fr|com|net|org|io|eu)(?:/[^\s\"\'<>(),]*)?'
        toutes_les_urls = re.findall(pattern, contenu)

        for url in toutes_les_urls:
            url_propre = url.split(')')[0].split(']')[0].rstrip(',.;"\'')
            if not url_propre.startswith(('http://', 'https://')):
                url_propre = 'https://' + url_propre

            if est_un_vrai_prospect(url_propre) and url_propre not in urls_trouvees:
                urls_trouvees.append(url_propre)
                print(f"   ✅ Prospect qualifié : {url_propre}")

            if len(urls_trouvees) >= max_resultats:
                break

    except FileNotFoundError:
        print("❌ Le fichier 'google.txt' est introuvable à la racine.")
    except Exception as e:
        print(f"❌ Erreur lors du parsing des URLs : {e}")

    return urls_trouvees


def run_pipeline():
    print("=" * 60)
    print(f"  PIPELINE AUDIT SEO -> {config.GOOGLE_SHEET_NAME}")
    print("=" * 60)

    sheet = connecter_google_sheet()
    if not sheet:
        return

    try:
        # En-tête du tableau
        if not sheet.get_all_values():
            sheet.append_row([
                "URL", "Site Existant", "Statut Site", "Score SEO", 
                "Score Perf", "Balise H1", "Balise Title", "Meta Description", "Prioritaire 🔥"
            ])
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la feuille : {e}")
        return

    urls_cibles = recuperer_urls_prospects(config.NOMBRE_DE_SITES_A_SCRAPER)

    if not urls_cibles:
        print("\n❌ Aucun prospect qualifié trouvé dans 'google.txt'.")
        return

    print(f"\n🎯 {len(urls_cibles)} sites web à auditer. Début du traitement...\n")

    rows_to_insert = []

    for idx, url in enumerate(urls_cibles, 1):
        print(f"[{idx}/{len(urls_cibles)}]")
        try:
            data = audit_prospect(url, config.PAGESPEED_API_KEY)

            row = [
                data.get("url", url),
                data.get("has_site", "Oui"),
                data.get("status", "Erreur"),
                data.get("score_seo", 0),
                data.get("score_perf", 0),
                data.get("h1_status", "N/A"),
                data.get("title_status", "N/A"),
                data.get("meta_desc_status", "N/A"),
                data.get("critique", "Non")
            ]
            rows_to_insert.append(row)
            print("   ✅ Audit terminé.")

        except Exception as pipeline_error:
            print(f"💥 Erreur lors de l'audit de {url}: {pipeline_error}")

        time.sleep(1)

    # Insertion en BATCH (Une seule requête API à la fin)
    if rows_to_insert:
        try:
            print("\n💾 Enregistrement des données dans Google Sheets...")
            sheet.append_rows(rows_to_insert)
            print("✅ Sauvegarde effectuée avec succès !")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde sur Google Sheets : {e}")

    print("=" * 60)
    print(" 🔥 TOUS LES AUDITS SONT TERMINÉS !")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()