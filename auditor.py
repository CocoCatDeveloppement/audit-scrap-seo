import logging
import re
import urllib.parse
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

import config

# Configuration du logging professionnel
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SITES_A_IGNORER = [
    "google.", "gstatic.", "doctolib.fr", "pagesjaunes.fr", "leboncoin.fr", 
    "linkedin.com", "facebook.com", "instagram.com", "resalib.fr", "pagesavotre-sante.fr",
    "annuaire", "mapstr", "yelp", "mappy.com", "pole-emploi", "formation",
    "directory", "psychologies.com", "mon-medecin", "sante.fr", "simplifia", "solocal"
]


def clean_url(url: str) -> str:
    """Nettoie et formate l'URL pour s'assurer qu'elle commence par https://."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def est_un_vrai_prospect(url: str) -> bool:
    """Filtre les annuaires et réseaux sociaux de la liste de prospection."""
    url_lower = url.lower()
    return not any(plateforme in url_lower for plateforme in SITES_A_IGNORER)


def check_advanced_seo(url: str) -> Dict[str, Any]:
    """Analyse complète des balises HTML principales (Title, Description, H1)."""
    results = {
        "title": "Manquant",
        "title_len": 0,
        "title_too_long": False,
        "meta_desc": "Manquante",
        "meta_desc_len": 0,
        "meta_desc_too_long": False,
        "has_h1": False,
        "h1_count": 0,
        "error": None
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3'
    }

    try:
        # verify=True pour garantir la sécurité SSL. Timeout raisonnable de 10s.
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True, verify=True)

        if response.status_code != 200:
            results["error"] = f"Code HTTP {response.status_code}"
            return results

        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Analyse du Title
        if soup.title and soup.title.string:
            title_text = soup.title.string.strip()
            results["title"] = title_text
            results["title_len"] = len(title_text)
            if len(title_text) > config.MAX_TITLE_LENGTH:
                results["title_too_long"] = True

        # 2. Analyse de la Meta Description
        meta_desc_tag = (
            soup.find('meta', attrs={'name': re.compile(r'^description$', re.I)}) or
            soup.find('meta', attrs={'property': 'og:description'})
        )

        if meta_desc_tag and meta_desc_tag.get('content'):
            desc_text = meta_desc_tag['content'].strip()
            results["meta_desc"] = desc_text
            results["meta_desc_len"] = len(desc_text)
            if len(desc_text) > config.MAX_META_DESC_LENGTH:
                results["meta_desc_too_long"] = True

        # 3. Analyse de la balise H1
        h1_tags = soup.find_all('h1')
        results["h1_count"] = len(h1_tags)
        results["has_h1"] = len(h1_tags) > 0

    except requests.exceptions.SSLError:
        results["error"] = "Erreur Certificat SSL"
    except requests.exceptions.Timeout:
        results["error"] = "Délai d'attente dépassé (Timeout)"
    except Exception as e:
        results["error"] = f"Erreur de connexion ({type(e).__name__})"

    return results


def get_pagespeed_metrics(url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Interroge l'API PageSpeed Insights de Google pour récupérer les scores SEO et Perf."""
    encoded_url = urllib.parse.quote(url)
    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={encoded_url}&category=SEO&category=PERFORMANCE"
    
    if api_key:
        api_url += f"&key={api_key}"

    try:
        response = requests.get(api_url, timeout=20)
        if response.status_code == 200:
            data = response.json()
            categories = data.get('lighthouseResult', {}).get('categories', {})

            perf = categories.get('performance', {}).get('score')
            seo = categories.get('seo', {}).get('score')

            return {
                "performance_score": int(perf * 100) if perf is not None else 0,
                "google_seo_score": int(seo * 100) if seo is not None else 0
            }
        return {"error": f"API Error {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def audit_prospect(url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Orchestre l'audit complet pour un prospect donné."""
    target_url = clean_url(url)
    logging.info(f"🔍 Audit en cours : {target_url}")

    seo_data = check_advanced_seo(target_url)

    # Si le site est inaccessible
    if seo_data["error"]:
        return {
            "url": target_url,
            "has_site": "Oui",
            "status": f"Inaccessible ({seo_data['error']})",
            "score_seo": 0,
            "score_perf": 0,
            "h1_status": "N/A",
            "title_status": "N/A",
            "meta_desc_status": "N/A",
            "critique": "Oui 🔥 (Site HS / À refaire)"
        }

    metrics = get_pagespeed_metrics(target_url, api_key)

    score_seo = metrics.get("google_seo_score", 0) if "error" not in metrics else 0
    score_perf = metrics.get("performance_score", 0) if "error" not in metrics else 0

    # Qualification H1
    if not seo_data["has_h1"]:
        h1_status = "Manquant ❌"
    elif seo_data["h1_count"] > 1:
        h1_status = f"Multiple ({seo_data['h1_count']}) ⚠️"
    else:
        h1_status = "OK ✅"

    # Qualification Title
    if seo_data["title"] == "Manquant":
        title_status = "Manquant ❌"
    elif seo_data["title_too_long"]:
        title_status = f"Trop long ({seo_data['title_len']} car.) ⚠️"
    else:
        title_status = f"OK ({seo_data['title_len']} car.) ✅"

    # Qualification Meta Description
    if seo_data["meta_desc"] == "Manquante":
        meta_desc_status = "Manquante ❌"
    elif seo_data["meta_desc_too_long"]:
        meta_desc_status = f"Trop longue ({seo_data['meta_desc_len']} car.) ⚠️"
    else:
        meta_desc_status = f"OK ({seo_data['meta_desc_len']} car.) ✅"

    # Qualification "Prioritaire"
    is_critical = "Non"
    if (not seo_data["has_h1"] or 
        seo_data["meta_desc_too_long"] or 
        seo_data["meta_desc"] == "Manquante" or 
        seo_data["title_too_long"] or 
        score_seo < 60):
        is_critical = "Oui 🔥"

    return {
        "url": target_url,
        "has_site": "Oui",
        "status": "Actif",
        "score_seo": score_seo,
        "score_perf": score_perf,
        "h1_status": h1_status,
        "title_status": title_status,
        "meta_desc_status": meta_desc_status,
        "critique": is_critical
    }