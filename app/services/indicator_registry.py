from __future__ import annotations

import hashlib
import re
from typing import Any

# Canonical internal catalogue. External codes are supplied only when the
# extracted concept matches the published indicator closely enough.
INDICATORS: dict[str, dict[str, Any]] = {
    "economic_cost_level": {"official_name_fr": "Niveau de coût économique (concept à préciser)", "official_name_en": "Economic cost level (concept requires review)", "category": "Compétitivité-coût", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Plage ou niveau de coût dont le concept précis doit être vérifié dans le contexte ou le tableau associé."},
    "purchasing_power_growth": {"official_name_fr": "Variation du pouvoir d’achat des ménages", "official_name_en": "Household purchasing-power growth", "category": "Revenus des ménages", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Variation du pouvoir d’achat ou du revenu disponible réel des ménages selon la source."},
    "policy_rate": {"official_name_fr": "Taux directeur de la banque centrale", "official_name_en": "Central bank policy rate", "category": "Politique monétaire", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Taux de référence fixé par la banque centrale."},
    "money_market_rate": {"official_name_fr": "Taux moyen du marché monétaire (TMM nominal)", "official_name_en": "Nominal money market rate", "category": "Politique monétaire", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Taux moyen nominal observé sur le marché monétaire."},
    "real_money_market_rate": {"official_name_fr": "Taux moyen du marché monétaire réel", "official_name_en": "Real money market rate", "category": "Politique monétaire", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Taux du marché monétaire corrigé de l’inflation selon la source."},
    "nominal_effective_exchange_rate": {"official_name_fr": "Variation du taux de change effectif nominal (TCEN)", "official_name_en": "Nominal effective exchange rate change", "category": "Taux de change", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Variation du taux de change effectif nominal."},
    "real_effective_exchange_rate": {"official_name_fr": "Variation du taux de change effectif réel (TCER)", "official_name_en": "Real effective exchange rate change", "category": "Taux de change", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Variation du taux de change effectif réel."},
    "relative_price_change": {"official_name_fr": "Variation des prix relatifs", "official_name_en": "Relative price change", "category": "Compétitivité-prix", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Variation de la composante de prix relatifs selon la source."},
    "exchange_rate_change": {"official_name_fr": "Variation du taux de change bilatéral", "official_name_en": "Bilateral exchange rate change", "category": "Taux de change", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Appréciation ou dépréciation face à une devise partenaire."},
    "manufactured_goods_inflation": {"official_name_fr": "Variation des prix des produits manufacturés", "official_name_en": "Manufactured goods price change", "category": "Prix", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Variation des prix des produits manufacturés."},
    "unit_labor_cost": {"official_name_fr": "Variation du coût salarial unitaire nominal (CSU)", "official_name_en": "Nominal unit labour cost change", "category": "Compétitivité-coût", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Variation du coût du travail par unité produite."},
    "unit_labor_cost_level": {"official_name_fr": "Coût salarial unitaire", "official_name_en": "Unit labour cost", "category": "Compétitivité-coût", "default_unit": "ratio", "external_standard": None, "external_code": None, "definition_fr": "Niveau du coût salarial unitaire selon la définition de la source."},
    "nominal_wage_rate": {"official_name_fr": "Variation du taux de salaire nominal", "official_name_en": "Nominal wage rate change", "category": "Marché du travail", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Variation du taux de salaire nominal."},
    "labor_productivity": {"official_name_fr": "Variation de la productivité du travail", "official_name_en": "Labour productivity change", "category": "Productivité", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Variation de la productivité du travail."},
    "value_added_price": {"official_name_fr": "Variation du prix de la valeur ajoutée", "official_name_en": "Value-added price change", "category": "Prix", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Variation du prix de la valeur ajoutée."},
    "wage_cost_margin": {"official_name_fr": "Variation de la marge sur coût salarial", "official_name_en": "Wage-cost margin change", "category": "Compétitivité-coût", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Variation de la marge calculée relativement au coût salarial."},
    "competitiveness_index": {"official_name_fr": "Variation de l’indicateur synthétique de compétitivité", "official_name_en": "Synthetic competitiveness index change", "category": "Compétitivité", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Variation de l’indicateur synthétique de compétitivité défini par la source."},
    "competitor_prices": {"official_name_fr": "Variation des prix des concurrents", "official_name_en": "Competitor price change", "category": "Compétitivité-prix", "default_unit": "%", "external_standard": None, "external_code": None, "definition_fr": "Variation des prix des concurrents exprimée dans la devise indiquée."},
    "gdp_growth": {
        "official_name_fr": "Taux de croissance du PIB (variation annuelle)",
        "official_name_en": "GDP growth (annual %)",
        "category": "Comptes nationaux",
        "default_unit": "%",
        "external_standard": "World Bank WDI",
        "external_code": "NY.GDP.MKTP.KD.ZG",
        "definition_fr": "Variation annuelle en pourcentage du PIB à prix constants. La mention « réel » n'est ajoutée que lorsque le texte source la précise.",
    },
    "inflation_rate": {
        "official_name_fr": "Taux d’inflation des prix à la consommation",
        "official_name_en": "Consumer price inflation rate",
        "category": "Prix",
        "default_unit": "%",
        "external_standard": "World Bank WDI / Eurostat HICP",
        "external_code": "FP.CPI.TOTL.ZG",
        "definition_fr": "Variation du niveau des prix payés par les ménages. Le moteur conserve IPC ou IPCH lorsque le document le précise.",
    },
    "inflation_annual_average": {
        "official_name_fr": "Taux d’inflation des prix à la consommation (moyenne annuelle)",
        "official_name_en": "Consumer price inflation (annual average)",
        "category": "Prix",
        "default_unit": "%",
        "external_standard": "IMF WEO",
        "external_code": None,
        "definition_fr": "Variation moyenne de l’indice des prix à la consommation sur l’année, distincte de l’inflation en fin de période.",
    },
    "inflation_end_period": {
        "official_name_fr": "Taux d’inflation des prix à la consommation (fin de période)",
        "official_name_en": "Consumer price inflation (end of period)",
        "category": "Prix",
        "default_unit": "%",
        "external_standard": "IMF WEO",
        "external_code": None,
        "definition_fr": "Variation de l’indice des prix à la consommation mesurée en fin de période, distincte de la moyenne annuelle.",
    },
    "core_inflation": {
        "official_name_fr": "Taux d’inflation sous-jacente",
        "official_name_en": "Core inflation rate",
        "category": "Prix",
        "default_unit": "%",
        "external_standard": None,
        "external_code": None,
        "definition_fr": "Mesure de l’inflation excluant certains éléments volatils selon la définition de la source.",
    },
    "food_inflation": {
        "official_name_fr": "Taux d’inflation des produits alimentaires",
        "official_name_en": "Food inflation rate",
        "category": "Prix",
        "default_unit": "%",
        "external_standard": None,
        "external_code": None,
        "definition_fr": "Variation des prix des produits alimentaires selon la définition de la source.",
    },
    "activity_rate": {
        "official_name_fr": "Taux d’activité",
        "official_name_en": "Labour force participation rate",
        "category": "Marché du travail",
        "default_unit": "%",
        "external_standard": "ILO / World Bank WDI (concept)",
        "external_code": None,
        "definition_fr": "Part de la population en âge de travailler appartenant à la population active, selon la définition de la source.",
    },
    "current_account_balance": {
        "official_name_fr": "Solde du compte courant (% du PIB)",
        "official_name_en": "Current account balance (% of GDP)",
        "category": "Secteur extérieur",
        "default_unit": "% du PIB",
        "external_standard": "IMF BOP / World Bank WDI",
        "external_code": "BN.CAB.XOKA.GD.ZS",
        "definition_fr": "Solde du compte courant rapporté au PIB. Un déficit peut être exprimé avec un signe négatif ou par le libellé de la source.",
    },
    "fdi_growth": {
        "official_name_fr": "Variation des investissements directs étrangers (IDE)",
        "official_name_en": "Foreign direct investment change",
        "category": "Secteur extérieur",
        "default_unit": "%",
        "external_standard": None,
        "external_code": None,
        "definition_fr": "Variation en pourcentage des flux ou montants d’investissements directs étrangers par rapport à une période de référence.",
    },
    "unemployment_rate": {
        "official_name_fr": "Taux de chômage",
        "official_name_en": "Unemployment rate",
        "category": "Marché du travail",
        "default_unit": "% de la population active",
        "external_standard": "OECD / ILO / World Bank WDI",
        "external_code": "SL.UEM.TOTL.ZS",
        "definition_fr": "Part des personnes sans emploi, disponibles et en recherche active d'emploi dans la population active.",
    },
    "public_debt_ratio": {
        "official_name_fr": "Dette publique (% du PIB)",
        "official_name_en": "Public debt (% of GDP)",
        "category": "Finances publiques",
        "default_unit": "% du PIB",
        "external_standard": "IMF (concept proche : general government gross debt, % of GDP)",
        "external_code": None,
        "definition_fr": "Ratio de dette publique rapporté au PIB. Le code IMF GGXWDG_NGDP n'est appliqué que si le texte précise la dette brute des administrations publiques.",
    },
    "public_debt_stock": {
        "official_name_fr": "Encours de la dette publique",
        "official_name_en": "Public debt stock",
        "category": "Finances publiques",
        "default_unit": "Monnaie",
        "external_standard": "IMF Government Finance Statistics (concept)",
        "external_code": None,
        "definition_fr": "Montant nominal de dette publique à une date donnée.",
    },
    "internal_debt_stock": {
        "official_name_fr": "Encours de la dette publique intérieure",
        "official_name_en": "Domestic public debt stock",
        "category": "Finances publiques",
        "default_unit": "Monnaie",
        "external_standard": None,
        "external_code": None,
        "definition_fr": "Montant nominal de dette publique intérieure.",
    },
    "external_debt_stock": {
        "official_name_fr": "Encours de la dette publique extérieure",
        "official_name_en": "External public debt stock",
        "category": "Finances publiques",
        "default_unit": "Monnaie",
        "external_standard": None,
        "external_code": None,
        "definition_fr": "Montant nominal de dette publique extérieure.",
    },
    "internal_debt_share": {
        "official_name_fr": "Part de la dette intérieure dans l’encours de la dette publique",
        "official_name_en": "Domestic debt share of public debt stock",
        "category": "Finances publiques",
        "default_unit": "%",
        "external_standard": None,
        "external_code": None,
        "definition_fr": "Part de l'encours de dette publique constituée de dette intérieure.",
    },
    "external_debt_ratio": {
        "official_name_fr": "Dette publique extérieure (% du PIB)",
        "official_name_en": "External public debt (% of GDP)",
        "category": "Finances publiques",
        "default_unit": "% du PIB",
        "external_standard": None,
        "external_code": None,
        "definition_fr": "Part de la dette publique extérieure rapportée au PIB.",
    },
    "internal_debt_ratio": {
        "official_name_fr": "Dette publique intérieure (% du PIB)",
        "official_name_en": "Domestic public debt (% of GDP)",
        "category": "Finances publiques",
        "default_unit": "% du PIB",
        "external_standard": None,
        "external_code": None,
        "definition_fr": "Part de la dette publique intérieure rapportée au PIB.",
    },
    "public_revenue": {
        "official_name_fr": "Recettes publiques",
        "official_name_en": "Government revenue",
        "category": "Finances publiques",
        "default_unit": None,
        "external_standard": None,
        "external_code": None,
        "definition_fr": "Recettes des administrations publiques telles que présentées dans le document source.",
    },
    "public_expenditure": {
        "official_name_fr": "Dépenses publiques",
        "official_name_en": "Government expenditure",
        "category": "Finances publiques",
        "default_unit": None,
        "external_standard": None,
        "external_code": None,
        "definition_fr": "Dépenses des administrations publiques telles que présentées dans le document source.",
    },
    "budget_deficit": {
        "official_name_fr": "Déficit budgétaire",
        "official_name_en": "Budget deficit",
        "category": "Finances publiques",
        "default_unit": "% du PIB ou monnaie",
        "external_standard": "IMF WEO (concept proche : net lending/borrowing)",
        "external_code": None,
        "definition_fr": "Écart négatif entre recettes et dépenses budgétaires selon le périmètre du document.",
    },
    "primary_balance": {
        "official_name_fr": "Solde budgétaire primaire",
        "official_name_en": "Primary fiscal balance",
        "category": "Finances publiques",
        "default_unit": "% du PIB ou monnaie",
        "external_standard": "IMF Fiscal Monitor",
        "external_code": None,
        "definition_fr": "Solde budgétaire hors charges d'intérêts.",
    },
    "trade_balance": {
        "official_name_fr": "Solde commercial",
        "official_name_en": "Trade balance",
        "category": "Secteur extérieur",
        "default_unit": "Monnaie",
        "external_standard": "National statistics / IMF trade statistics",
        "external_code": None,
        "definition_fr": "Différence entre la valeur des exportations et des importations de biens selon le périmètre de la source.",
    },
    "trade_coverage_ratio": {
        "official_name_fr": "Taux de couverture des importations par les exportations",
        "official_name_en": "Import coverage ratio by exports",
        "category": "Secteur extérieur",
        "default_unit": "%",
        "external_standard": "National trade statistics",
        "external_code": None,
        "definition_fr": "Rapport entre les exportations et les importations, exprimé en pourcentage.",
    },
    "cpi_monthly_change": {
        "official_name_fr": "Variation mensuelle de l’indice des prix à la consommation",
        "official_name_en": "Monthly change in consumer price index",
        "category": "Prix",
        "default_unit": "%",
        "external_standard": "CPI statistics",
        "external_code": None,
        "definition_fr": "Variation de l’indice des prix à la consommation par rapport au mois précédent.",
    },
    "exports_growth": {
        "official_name_fr": "Taux de variation des exportations de biens et services",
        "official_name_en": "Growth rate of exports of goods and services",
        "category": "Secteur extérieur", "default_unit": "%", "external_standard": "Trade statistics", "external_code": None,
        "definition_fr": "Variation des exportations sur la période indiquée par la source.",
    },
    "imports_growth": {
        "official_name_fr": "Taux de variation des importations de biens et services",
        "official_name_en": "Growth rate of imports of goods and services",
        "category": "Secteur extérieur", "default_unit": "%", "external_standard": "Trade statistics", "external_code": None,
        "definition_fr": "Variation des importations sur la période indiquée par la source.",
    },
    "exports": {
        "official_name_fr": "Exportations de biens et services",
        "official_name_en": "Exports of goods and services",
        "category": "Secteur extérieur",
        "default_unit": "Monnaie ou volume",
        "external_standard": "World Bank WDI",
        "external_code": None,
        "definition_fr": "Valeur ou volume des biens et services exportés, selon le texte source.",
    },
    "imports": {
        "official_name_fr": "Importations de biens et services",
        "official_name_en": "Imports of goods and services",
        "category": "Secteur extérieur",
        "default_unit": "Monnaie ou volume",
        "external_standard": "World Bank WDI",
        "external_code": None,
        "definition_fr": "Valeur ou volume des biens et services importés, selon le texte source.",
    },
    "foreign_direct_investment": {
        "official_name_fr": "Investissements directs étrangers (IDE)",
        "official_name_en": "Foreign direct investment (FDI)",
        "category": "Secteur extérieur",
        "default_unit": "Monnaie ou % du PIB",
        "external_standard": "World Bank WDI / IMF BOP",
        "external_code": None,
        "definition_fr": "Flux ou stock d'investissements directs étrangers selon le texte source.",
    },
    "foreign_exchange_reserves": {
        "official_name_fr": "Réserves officielles de change",
        "official_name_en": "Official foreign exchange reserves",
        "category": "Secteur extérieur",
        "default_unit": "Monnaie ou mois/jours d'importation",
        "external_standard": "IMF International Financial Statistics",
        "external_code": None,
        "definition_fr": "Avoirs de réserve officiels exprimés en valeur ou en couverture des importations.",
    },
    "public_spending_ratio": {
        "official_name_fr": "Dépenses publiques (% du PIB)",
        "official_name_en": "Public expenditure (% of GDP)",
        "category": "Finances publiques",
        "default_unit": "% du PIB",
        "external_standard": None,
        "external_code": None,
        "definition_fr": "Dépenses publiques rapportées au PIB selon le périmètre du document.",
    },
    "external_debt_share": {
        "official_name_fr": "Part de la dette extérieure dans l’encours de la dette publique",
        "official_name_en": "External debt share of public debt stock",
        "category": "Finances publiques",
        "default_unit": "%",
        "external_standard": None,
        "external_code": None,
        "definition_fr": "Part de l'encours public détenue sous forme de dette extérieure.",
    },
    "public_debt_state_share": {
        "official_name_fr": "Part de la dette publique dans la dette de l’État",
        "official_name_en": "Public debt share of state debt",
        "category": "Finances publiques",
        "default_unit": "%",
        "external_standard": None,
        "external_code": None,
        "definition_fr": "Part de la dette publique dans l'ensemble de la dette de l'État telle que définie dans le document.",
    },
}

from app.services.country_registry import ALIAS_TO_COUNTRY as COUNTRIES, detect_country



def indicator_metadata(code: str, sentence: str = "") -> dict[str, Any]:
    meta = dict(INDICATORS.get(code, {}))
    if not meta:
        return {
            "indicator_id": code.upper(),
            "official_name_fr": code,
            "official_name_en": code,
            "category": "Autre",
            "external_standard": None,
            "external_code": None,
            "definition_fr": "",
        }
    indicator_id = f"ECO.{code.upper()}"
    official_fr = meta["official_name_fr"]
    # Do not infer “real GDP” unless the source explicitly says real/constant prices.
    if code == "gdp_growth":
        if re.search(r"\bPIB\s+r[ée]el|prix\s+constants?\b", sentence, re.I):
            official_fr = "Taux de croissance du PIB réel (variation annuelle)"
        if re.search(r"\b(?:[1-4](?:er|e|ème)?|premier|deuxième|deuxieme|troisième|troisieme|quatrième|quatrieme|dernier)\s+trimestre\b|\btrimestre\s+(?:pr[ée]c[ée]dent|precedent|suivant)\b|\btrimestre\s+qui\s+(?:pr[ée]c[ée]dait|precedait|suivait)\b|par\s+rapport\s+au\s+trimestre\s+(?:pr[ée]c[ée]dent|precedent)|trois\s+mois\s+plus\s+tard", sentence, re.I):
            official_fr = "Taux de croissance du PIB (variation trimestrielle)"
    if code == "inflation_rate":
        if re.search(r"\bIPCH\b|indice\s+harmonis[ée]", sentence, re.I):
            official_fr = "Taux d’inflation mesuré par l’IPCH"
        elif re.search(r"\bIPC\b|indice\s+des\s+prix\s+[àa]\s+la\s+consommation", sentence, re.I):
            official_fr = "Taux d’inflation mesuré par l’IPC"
    if code == "public_debt_ratio" and re.search(r"administrations?\s+publiques?.*dette\s+brute|dette\s+brute.*administrations?\s+publiques?", sentence, re.I):
        official_fr = "Dette brute des administrations publiques (% du PIB)"
        meta["external_code"] = "GGXWDG_NGDP"
        meta["external_standard"] = "IMF WEO"
    return {"indicator_id": indicator_id, **meta, "official_name_fr": official_fr}




def build_series_id(country_iso3: str | None, indicator_id: str, unit: str | None, scale: str | None, currency: str | None) -> str:
    geography = country_iso3 or "UNK"
    measurement = "|".join(str(x or "") for x in (unit, scale, currency))
    suffix = hashlib.sha1(measurement.encode("utf-8")).hexdigest()[:6].upper()
    return f"{geography}:{indicator_id}:{suffix}"
