# RAES DataTrack

Tableau de bord de suivi des données CLV2 — RAES Sénégal

## Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre sur http://localhost:8501

## Déployer sur Streamlit Cloud (gratuit)

1. Créer un compte sur https://github.com (gratuit)
2. Créer un nouveau dépôt `raes-datatrack` (public ou privé)
3. Uploader tous les fichiers de ce dossier
4. Aller sur https://share.streamlit.io
5. Se connecter avec GitHub
6. Cliquer "New app" → sélectionner le dépôt → app.py
7. Cliquer "Deploy"

L'app sera accessible via un lien du type :
https://raes-datatrack.streamlit.app

## Structure

```
raes_datatrack/
├── app.py              ← Application principale
├── requirements.txt    ← Dépendances Python
├── assets/
│   └── logo.svg        ← Logo RAES DataTrack
└── utils/
    └── kobo.py         ← Connexion et nettoyage données Kobo
```

## Mise à jour des données

Les données se rechargent automatiquement toutes les heures.
Pour forcer un rechargement : cliquer "Synchroniser Kobo" dans la sidebar.

## Ajouter un nouveau formulaire

Dans `utils/kobo.py`, ajouter l'UID dans le dictionnaire `FORMULAIRES`
et créer la fonction `clean_xxx()` correspondante.
