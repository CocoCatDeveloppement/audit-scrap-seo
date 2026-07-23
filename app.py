# app.py
import time
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from auditor import audit_prospect, est_un_vrai_prospect
import config

def connecter_google_sheet():
    """Initialise la connexion avec l'API Google Sheets et pointe vers Prospection_SEO_Propre"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open(config.GOOGLE_SHEET_NAME).sheet1
        return sheet
    except Exception as e:
        print(f"❌ Erreur de connexion au Sheet '{config.GOOGLE_SHEET_NAME}' : {e}")
        return None

def recuperer_urls_prospects(max_resultats):
    """Lit les résultats extraits de google.txt"""
    print(f"📂 Lecture du fichier local 'google.txt'...")
    urls_trouvees = []
    
    try:
        with open("google.txt", "r", encoding="utf-8") as f:
            contenu = f.read()
            
        # Regex élargie : prend les URLs avec ou sans http(s)
        pattern = r'(?:https?://|www\.)[^\s\"\'<>(),]+|(?:[a-zA-Z0-9-]+\.)+(?:fr|com|net|org|io|eu)(?:/[^\s\"\'<>(),]*)?'
        toutes_les_urls = re.findall(pattern, contenu)
        
        for url in toutes_les_urls:
            url_propre = url.split(')')[0].split(']')[0].rstrip(',.;"\'')
            if not url_propre.startswith(('http://', 'https://')):
                url_propre = 'https://' + url_propre
            
            if est_un_vrai_prospect(url_propre):
                if url_propre not in urls_trouvees:
                    urls_trouvees.append(url_propre)
                    print(f"   ✅ Prospect qualifié extrait : {url_propre}")
            
            if len(urls_trouvees) >= max_resultats:
                break
                
    except FileNotFoundError:
        print("❌ Le fichier 'google.txt' est introuvable à la racine.")
    except Exception as e:
        print(f"❌ Erreur lors du parsing : {e}")
        
    return urls_trouvees

def run_pipeline():
    print("="*60)
    print(f"  PIPELINE AUDIT SEO -> {config.GOOGLE_SHEET_NAME}  ")
    print("="*60)
    
    sheet = connecter_google_sheet()
    if not sheet:
        return
        
    try:
        # Initialisation de l'en-tête du tableau
        if not sheet.get_all_values():
            sheet.append_row([
                "URL", 
                "Site Existant", 
                "Statut Site", 
                "Score SEO", 
                "Score Perf", 
                "Balise H1", 
                "Balise Title", 
                "Meta Description", 
                "Prioritaire 🔥"
            ])
    except Exception as e:
        print(f"❌ Erreur de configuration de la feuille : {e}")
        return
    
    urls_cibles = recuperer_urls_prospects(config.NOMBRE_DE_SITES_A_SCRAPER)
    
    if not urls_cibles:
        print("\n❌ Aucun site web de prospect trouvé dans 'google.txt'.")
        return
        
    print(f"\n🎯 {len(urls_cibles)} sites web identifiés. Début des audits...\n")
    
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
            
            sheet.append_row(row)
            print(f"   ✅ Données enregistrées dans Google Sheet.\n")
            
        except Exception as pipeline_error:
            print(f"💥 Erreur lors de l'audit de {url}: {pipeline_error}\n")
            
        time.sleep(1.5)
        
    print("="*60)
    print(f" 🔥 AUDITS TERMINÉS ! Fichier mis à jour : {config.GOOGLE_SHEET_NAME}")
    print("="*60)

if __name__ == "__main__":
    run_pipeline()