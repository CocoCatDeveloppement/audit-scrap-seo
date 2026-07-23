# 🐍 Python SEO Auditor & Google Sheets Sync

Un outil d'automatisation en Python conçu pour **auditer automatiquement les métadonnées SEO** d'une liste de sites web et **synchroniser les résultats en temps réel** dans une feuille Google Sheets.

Idéal pour la prospection, l'audit rapide de leads ou la veille SEO.

---

## 🚀 Fonctionnalités

* 🔍 **Extraction & Analyse SEO :** Vérification automatique des éléments clés :
  * Présence et conformité de la balise **H1** (détection des balises multiples ou manquantes).
  * Longueur et pertinence de la balise **Title**.
  * Analyse de la **Meta Description**.
* 🔥 **Scoring de Priorité :** Identification visuelle des prospects nécessitant une intervention SEO urgente (indicateur *Prioritaire 🔥*).
* 📊 **Rapport Google Sheets :** Exportation et mise à jour automatique des données dans un tableau structuré et coloré via l'API Google Sheets.

---

## 🛠️ Prérequis

* **Python 3.8+**
* Un compte **Google Cloud Console** avec les API Google Sheets et Google Drive activées.
* Un fichier de clés de service Google (`credentials.json`).

---

## 📦 Installation & Configuration

### 1. Cloner le projet
```bash
git clone [https://github.com/CocoCatDeveloppement/audit-scrap-seo.git](https://github.com/CocoCatDeveloppement/audit-scrap-seo.git)
cd audit-scrap-seo