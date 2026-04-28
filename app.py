"""
RAES DataTrack — Connexion et chargement des données KoboToolbox
"""

import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────
KOBO_TOKEN  = "6f0cb00fcaeaad5d9f5c9066d4710adbd613c642"
KOBO_SERVER = "eu.kobotoolbox.org"

FORMULAIRES = {
    # PRT — Jeunes en milieu scolaire
    "grossesses_bl": ("aZmLJzP4zFbKvPq7WBU2TU", "Grossesses — Pré-test",  "PRT", "#129bd5"),
    "grossesses_el": ("aYykRKagHqNRoEraeE2BHX", "Grossesses — Post-test", "PRT", "#5abde9"),
    "mariages_bl":   ("a6VMRhs4XhgQLDy3VW6GCY", "Mariages — Pré-test",   "PRT", "#129bd5"),
    "mariages_el":   ("aegG3nJWNWkwZyebmQtRKX", "Mariages — Post-test",  "PRT", "#5abde9"),
    "vbg_bl":        ("aEe3o3oakXL5LPK6J3Kcq4", "VBG — Pré-test",        "PRT", "#129bd5"),
    "vbg_el":        ("aikStdVxaCs4YgPKZ2nyFm", "VBG — Post-test",       "PRT", "#5abde9"),
    "puberte_bl":    ("a2teFDUjuBs6Kx6dxe4FXB", "Puberté — Pré-test",   "PRT", "#129bd5"),
    "puberte_el":    ("a9pgM4pSdCePFEiXqdkgHo", "Puberté — Post-test",  "PRT", "#5abde9"),
    # COMOD — Communautés & Animateurs
    "kit_bl":        ("a7jZNqterr3fkA9Wsn9HNg", "Kit Pédagogique — Pré-test",  "COMOD", "#68b485"),
    "kit_el":        ("acbAmxVAa2yUqeEwvTVgLZ", "Kit Pédagogique — Post-test", "COMOD", "#a0d5b3"),
    "comod_bl":      ("aF3PjttCaBsfwYLHqoNZxL", "Ciné-débat — Pré-test",       "COMOD", "#68b485"),
    "comod_el":      ("aZAEzh8nb5NRTZGPvQX8BN", "Ciné-débat — Post-test",      "COMOD", "#a0d5b3"),
}

AGE_MAP = {
    "10_14_ans":"10-14 ans","15_18_ans":"15-18 ans","15_19_ans":"15-19 ans",
    "19_24_ans":"19-24 ans","20_24_ans":"20-24 ans",
    "25_29ans":"25-29 ans","25_29_ans":"25-29 ans",
    "30_35anq":"30-35 ans","30_35_ans":"30-35 ans",
    "35ans_plus":"35 ans et plus","35_plus":"35 ans et plus",
}


@st.cache_data(ttl=3600, show_spinner=False)
def charger_formulaire(uid: str) -> pd.DataFrame:
    """Télécharge un formulaire Kobo et retourne un DataFrame brut."""
    headers = {"Authorization": f"Token {KOBO_TOKEN}"}
    results = []
    url = f"https://{KOBO_SERVER}/api/v2/assets/{uid}/data/?format=json&limit=30000"
    while url:
        r = requests.get(url, headers=headers, timeout=60)
        if r.status_code != 200:
            return pd.DataFrame()
        data = r.json()
        results.extend(data.get("results", []))
        url = data.get("next")
    return pd.DataFrame(results) if results else pd.DataFrame()


def normaliser_base(df: pd.DataFrame, sexe_col: str, age_col: str,
                    zone_col: str = None) -> pd.DataFrame:
    """Normalise les colonnes communes à tous les formulaires."""
    out = pd.DataFrame()
    if len(df) == 0:
        return out

    if sexe_col in df.columns:
        out["sexe"] = df[sexe_col].astype(str).str.lower().map({
            "fille":"Fille","garcon":"Garçon",
            "femme":"Femme","homme":"Homme",
            "une femme":"Femme","un homme":"Homme",
        })
    if age_col in df.columns:
        out["age"] = df[age_col].astype(str).str.strip().map(AGE_MAP)
    if zone_col and zone_col in df.columns:
        out["zone"] = df[zone_col].astype(str).str.strip().str.lower().map(
            {"mbour":"Mbour","sedhiou":"Sédhiou"}).fillna(df[zone_col])
    return out


# ── Nettoyage PRT Grossesses ──────────────────────────────────
def clean_grossesses(df: pd.DataFrame, is_el=False) -> pd.DataFrame:
    if len(df) == 0: return pd.DataFrame()
    out = normaliser_base(df, "Partie_A/sexe", "Partie_A/age", "zone")
    q1_map = {
        "_18ans":      "Tombe enceinte avant l'âge de 18 ans",
        "avant_25ans": "Une fille se marie avant l'âge de 25 ans",
        "avant_18ans": "Une fille se marie avant 18 ans",
        "age_30ans":   "Une fille/femme décide d'avoir un enfant à l'âge de 30 ans",
    }
    out["q_grossesse"] = df["partie_2/definition_grossesse"].map(q1_map)
    cons = df["partie_2/consequences_grossesses"].fillna("").astype(str)
    out["mat"]    = cons.apply(lambda x: 1 if "consequence_1" in x.split() else 0)
    out["abandon"]= cons.apply(lambda x: 1 if "consequence_2" in x.split() else 0)
    out["intel"]  = cons.apply(lambda x: 1 if "consequence_3" in x.split() else 0)
    out["rejet"]  = cons.apply(lambda x: 1 if "consequence_4" in x.split() else 0)
    out["regles"] = df["partie_2/regles"].str.lower().map({"oui":"Oui","non":"Non"})
    if is_el and "capable_1" in df.columns:
        out["capable"] = df["capable_1"].str.lower().map({"oui":"Oui","non":"Non"})
    return out


# ── Nettoyage PRT Mariages ────────────────────────────────────
def clean_mariages(df: pd.DataFrame, is_el=False) -> pd.DataFrame:
    if len(df) == 0: return pd.DataFrame()
    out = normaliser_base(df, "Partie_A/sexe", "Partie_A/age", "zone")
    q1_map = {
        "maruage_1": "Union légale d'un homme et d'une femme",
        "maruage_2": "Union d'un enfant avec un adulte avant l'âge légal",
        "maruage_3": "Union d'un enfant avec un autre enfant avant l'âge légal",
        "maruage_4": "Consentement mutuel peu importe l'âge",
    }
    out["q1"] = df["partie_2/definition_mariage_enfants"].map(q1_map)
    caus = df["partie_2/causes_mariage_enfants_communaute"].fillna("").astype(str)
    cons = df["partie_2/consequences_mariage_enfants"].fillna("").astype(str)
    for i, col in enumerate(["r1","r2","r3","r4","r5"], 1):
        out[col] = caus.apply(lambda x,i=i: 1 if f"cause_{i}" in x.split() else 0)
    for i, col in enumerate(["c1","c2","c3","c4","c5"], 1):
        out[col] = cons.apply(lambda x,i=i: 1 if f"consequence_{i}" in x.split() else 0)
    if is_el:
        cap = next((c for c in df.columns if "capable" in c.lower()), None)
        if cap: out["capable"] = df[cap].str.lower().map({"oui":"Oui","non":"Non"})
    return out


# ── Nettoyage PRT VBG ─────────────────────────────────────────
def clean_vbg(df: pd.DataFrame, is_el=False) -> pd.DataFrame:
    if len(df) == 0: return pd.DataFrame()
    out = normaliser_base(df, "Partie_A/sexe", "Partie_A/age", "zone")
    typ  = df["partie_2/type"].fillna("").astype(str)
    acte = df["partie_2/acte"].fillna("").astype(str)
    # codes type : 1,2,3,5,6 (pas de 4)
    for code, col in [("1","v1"),("2","v2"),("3","v3"),("5","v4"),("6","v5")]:
        out[col] = typ.apply(lambda x,c=code: 1 if c in x.split() else 0)
    for i, col in enumerate(["vs1","vs2","vs3","vs4"], 1):
        out[col] = acte.apply(lambda x,i=i: 1 if str(i) in x.split() else 0)
    lk = {"1":"Tout à fait d'accord","2":"D'accord","3":"Neutre",
          "4":"Pas d'accord","5":"Pas du tout d'accord"}
    out["likert1"] = df["partie_2/violence_physique"].astype(str).map(lk)
    out["likert2"] = df["partie_2/viol"].astype(str).map(lk)
    if is_el:
        cap = next((c for c in df.columns if "capable" in c.lower()), None)
        if cap: out["capable"] = df[cap].str.lower().map({"oui":"Oui","non":"Non"})
    return out


# ── Nettoyage PRT Puberté ─────────────────────────────────────
def clean_puberte(df: pd.DataFrame, is_el=False) -> pd.DataFrame:
    if len(df) == 0: return pd.DataFrame()
    out = normaliser_base(df, "Partie_A/sexe", "Partie_A/age", "zone")
    pub_map = {"1":"Un développement des capacités","2":"Un moment où le corps change",
               "3":"Phase de développement de l'intelligence",
               "4":"Une phase normale de développement","5":"Une maladie"}
    out["q_pub"] = df["partie_2/puberte"].astype(str).map(pub_map)
    chg = df["partie_2/changement"].fillna("").astype(str)
    for i, col in enumerate(["ch1","ch2","ch3","ch4","ch5"], 1):
        out[col] = chg.apply(lambda x,i=i: 1 if str(i) in x.split() else 0)
    lk = {"1":"Tout à fait d'accord","2":"D'accord","3":"Neutre",
          "4":"Pas d'accord","5":"Pas du tout d'accord"}
    out["voix"]       = df["partie_2/changement_1"].astype(str).map(lk)
    out["poils"]      = df["partie_2/changement_2"].astype(str).map(lk)
    out["regles_pub"] = df["partie_2/changement_3"].astype(str).map(lk)
    if is_el:
        cap = next((c for c in df.columns if "capable" in c.lower()), None)
        if cap: out["capable"] = df[cap].str.lower().map({"oui":"Oui","non":"Non"})
    return out


# ── Nettoyage COMOD Kit Pédagogique ──────────────────────────
def clean_kit(df: pd.DataFrame, is_el=False) -> pd.DataFrame:
    if len(df) == 0: return pd.DataFrame()
    out = normaliser_base(df, "ident_repondants/sexe", "ident_repondants/age")
    out["anime"]        = df["ident_repondants/anime_activites"].str.lower().map({"oui":"Oui","non":"Non"})
    out["outille"]      = df["ident_repondants/outille"].str.lower().map({"oui":"Oui","non":"Non"})
    out["parole"]       = df["ident_repondants/parole_public"].str.lower().map({"oui":"Oui","non":"Non"})
    edu_map = {"ensemble_moyens":"Définition correcte","informations":"Informations santé",
               "formation":"Formation médicale","nsp":"Ne sait pas"}
    out["def_education"] = df["concept_definitions/def_education_sante"].map(edu_map)
    roles = df["techniques_animation/roles_posture"].fillna("").astype(str)
    out["role_reguler"] = roles.apply(lambda x: 1 if "reguler" in x.split() else 0)
    out["role_eduquer"] = roles.apply(lambda x: 1 if "eduquer" in x.split() else 0)
    out["role_neutre"]  = roles.apply(lambda x: 1 if "neutre" in x.split() else 0)
    out["role_veiller"] = roles.apply(lambda x: 1 if "veiller_expression" in x.split() else 0)
    out["connais_kit"]  = df["connaissances_kit/connais_kit"].str.lower().map({"oui":"Oui","non":"Non"})
    utilite = df["connaissances_kit/utilite_kit"].fillna("").astype(str)
    out["kit_animer"]   = utilite.apply(lambda x: 1 if "animer_debats" in x.split() else 0)
    out["kit_soutenir"] = utilite.apply(lambda x: 1 if "soutenir_appropriation" in x.split() else 0)
    if is_el:
        sat_map = {"pas_du_tout_satisfait":"Pas du tout satisfait","pas_satisfait":"Pas satisfait",
                   "ni_satisfait":"Neutre","satisfait":"Satisfait","tres_satisfait":"Très satisfait"}
        cap_map = {"pas_du_tout_capable":"Pas du tout capable","pas_capable":"Pas capable",
                   "plutot_capable":"Plutôt capable","tout_a_fait_capable":"Tout à fait capable"}
        if "retours_perspectives/satisfaction" in df.columns:
            out["satisfaction"] = df["retours_perspectives/satisfaction"].map(sat_map)
        if "retours_perspectives/capable" in df.columns:
            out["capable_animer"] = df["retours_perspectives/capable"].map(cap_map)
        if "retours_perspectives/engagement" in df.columns:
            out["engagement"] = df["retours_perspectives/engagement"].str.lower().map({"oui":"Oui","non":"Non"})
    return out


# ── Nettoyage COMOD Ciné-débat ───────────────────────────────
def clean_comod(df: pd.DataFrame, is_el=False) -> pd.DataFrame:
    if len(df) == 0: return pd.DataFrame()
    rows = []
    sfx_map = {"1":"","2":"_001","3":"_002","4":"_003","5":"_004"}
    pfx_map = {"1":"partie_1/","2":"partie_2/","3":"partie_3/","4":"partie_4/","5":"partie_5/"}
    age_map2 = {**AGE_MAP, "30_35anq":"30-35 ans"}

    for _, row in df.iterrows():
        theme = str(row.get("cine",""))
        sfx   = sfx_map.get(theme,"")
        pfx   = pfx_map.get(theme,"")
        r     = {"theme": theme}

        sexe_col = f"{pfx}sexe{sfx}" if sfx else f"{pfx}sexe"
        age_col  = f"{pfx}age{sfx}"  if sfx else f"{pfx}age"
        r["sexe"] = str(row.get(sexe_col,"")).strip()
        r["age"]  = age_map2.get(str(row.get(age_col,"")).strip(), "")

        # Questions communes
        r["enceinte_sans_regles"] = str(row.get(f"connaissance_3{sfx}", ""))
        r["capable_decisions"]    = str(row.get(f"connaissance_1{sfx}", ""))
        if is_el:
            r["engagement_ssr"] = str(row.get(f"connaissance_4{sfx}", ""))

        # Questions spécifiques
        if theme == "3":  # Grossesses
            q1_map = {"_18ans":"Enceinte avant 18 ans","avant_25ans":"Mariage avant 25 ans",
                      "avant_18ans":"Mariage avant 18 ans","age_30ans":"Enfant à 30 ans"}
            r["q_grossesse"] = q1_map.get(str(row.get("partie_31/definition_grossesse","")), "")
            cons = str(row.get("partie_31/consequences_grossesses",""))
            r["g_abandon"] = 1 if "consequence_2_g" in cons.split() else 0
            r["g_rejet"]   = 1 if "consequence_4_g" in cons.split() else 0
            r["regles"]    = str(row.get("partie_31/regles",""))

        elif theme == "1":  # Mariages
            q1_map = {"maruage_1":"Union légale","maruage_2":"Enfant + adulte (correct)",
                      "maruage_3":"Enfant + enfant","maruage_4":"Consentement peu importe l'âge"}
            r["q1"] = q1_map.get(str(row.get("partie_1_1/definition_mariage_enfants","")), "")
            caus = str(row.get("partie_1_1/causes_mariage_enfants_communaute",""))
            cons = str(row.get("partie_1_1/consequences_mariage_enfants",""))
            for i in range(1,6):
                r[f"r{i}"] = 1 if f"cause_{i}" in caus.split() else 0
                r[f"c{i}"] = 1 if f"consequence_{i}" in cons.split() else 0

        elif theme == "4":  # VBG
            typ  = str(row.get("partie_41/type",""))
            acte = str(row.get("partie_41/acte",""))
            for code, col in [("1","v1"),("2","v2"),("3","v3"),("5","v4"),("6","v5")]:
                r[col] = 1 if code in typ.split() else 0
            for i, col in enumerate(["vs1","vs2","vs3","vs4"],1):
                r[col] = 1 if str(i) in acte.split() else 0

        rows.append(r)
    return pd.DataFrame(rows)


# ── Chargement de toutes les données ─────────────────────────
def charger_toutes_donnees():
    """Charge et nettoie tous les formulaires. Utilise le cache Streamlit."""
    data = {}
    loaders = [
        ("grossesses_bl", False, clean_grossesses),
        ("grossesses_el", True,  clean_grossesses),
        ("mariages_bl",   False, clean_mariages),
        ("mariages_el",   True,  clean_mariages),
        ("vbg_bl",        False, clean_vbg),
        ("vbg_el",        True,  clean_vbg),
        ("puberte_bl",    False, clean_puberte),
        ("puberte_el",    True,  clean_puberte),
        ("kit_bl",        False, clean_kit),
        ("kit_el",        True,  clean_kit),
        ("comod_bl",      False, clean_comod),
        ("comod_el",      True,  clean_comod),
    ]
    for key, is_el, fn in loaders:
        uid, _, _, _ = FORMULAIRES[key]
        raw  = charger_formulaire(uid)
        data[key] = fn(raw, is_el=is_el)
    return data
