from __future__ import annotations


INDICATORS = {
    "inflation": {
        "fr": [
            "taux d'inflation",
            "inflation",
            "hausse des prix",
            "prix à la consommation",
            "indice des prix à la consommation",
        ],
        "en": [
            "inflation rate",
            "inflation",
            "consumer price index",
            "consumer prices",
            "cpi",
        ],
        "ar": [
            "نسبة التضخم",
            "معدل التضخم",
            "التضخم",
            "ارتفاع الأسعار",
            "مؤشر أسعار الاستهلاك",
        ],
    },
    "gdp_growth": {
        "fr": [
            "croissance du pib",
            "croissance économique",
            "taux de croissance",
            "produit intérieur brut",
            "pib",
        ],
        "en": [
            "gdp growth",
            "economic growth",
            "gross domestic product",
            "gdp",
        ],
        "ar": [
            "نمو الناتج المحلي الإجمالي",
            "النمو الاقتصادي",
            "الناتج المحلي الإجمالي",
            "معدل النمو",
        ],
    },
    "unemployment": {
        "fr": [
            "taux de chômage",
            "chômage",
            "demandeurs d'emploi",
        ],
        "en": [
            "unemployment rate",
            "unemployment",
            "jobless rate",
        ],
        "ar": [
            "نسبة البطالة",
            "معدل البطالة",
            "البطالة",
        ],
    },
    "exports": {
        "fr": [
            "exportations",
            "ventes à l'étranger",
        ],
        "en": [
            "exports",
            "export sales",
        ],
        "ar": [
            "الصادرات",
            "التصدير",
        ],
    },
    "imports": {
        "fr": [
            "importations",
            "achats à l'étranger",
        ],
        "en": [
            "imports",
            "import purchases",
        ],
        "ar": [
            "الواردات",
            "التوريد",
        ],
    },
    "trade_balance": {
        "fr": [
            "balance commerciale",
            "déficit commercial",
            "excédent commercial",
        ],
        "en": [
            "trade balance",
            "trade deficit",
            "trade surplus",
        ],
        "ar": [
            "الميزان التجاري",
            "العجز التجاري",
            "الفائض التجاري",
        ],
    },
    "fdi": {
        "fr": [
            "investissements directs étrangers",
            "investissement direct étranger",
            "ide",
        ],
        "en": [
            "foreign direct investment",
            "fdi",
        ],
        "ar": [
            "الاستثمار الأجنبي المباشر",
            "الاستثمارات الأجنبية المباشرة",
        ],
    },
    "investment": {
        "fr": [
            "investissements",
            "investissement",
        ],
        "en": [
            "investments",
            "investment",
        ],
        "ar": [
            "الاستثمارات",
            "الاستثمار",
        ],
    },
    "public_debt": {
        "fr": [
            "dette publique",
            "endettement public",
            "dette de l'état",
        ],
        "en": [
            "public debt",
            "government debt",
            "sovereign debt",
        ],
        "ar": [
            "الدين العمومي",
            "الدين العام",
            "المديونية",
        ],
    },
    "budget_deficit": {
        "fr": [
            "déficit budgétaire",
            "déficit public",
            "déficit fiscal",
        ],
        "en": [
            "budget deficit",
            "fiscal deficit",
            "government deficit",
        ],
        "ar": [
            "العجز في الميزانية",
            "عجز الميزانية",
            "العجز المالي",
        ],
    },
    "interest_rate": {
        "fr": [
            "taux directeur",
            "taux d'intérêt",
            "taux clé",
        ],
        "en": [
            "key interest rate",
            "policy rate",
            "interest rate",
            "key rate",
        ],
        "ar": [
            "نسبة الفائدة المديرية",
            "سعر الفائدة",
            "نسبة الفائدة",
        ],
    },
    "exchange_rate": {
        "fr": [
            "taux de change",
            "cours de change",
        ],
        "en": [
            "exchange rate",
            "currency rate",
        ],
        "ar": [
            "سعر الصرف",
            "معدل الصرف",
        ],
    },
    "industrial_production": {
        "fr": [
            "production industrielle",
            "indice de production industrielle",
        ],
        "en": [
            "industrial production",
            "industrial output",
        ],
        "ar": [
            "الإنتاج الصناعي",
            "مؤشر الإنتاج الصناعي",
        ],
    },
    "tourism_revenue": {
        "fr": [
            "recettes touristiques",
            "revenus touristiques",
            "recettes du tourisme",
        ],
        "en": [
            "tourism revenues",
            "tourism receipts",
            "tourist revenues",
        ],
        "ar": [
            "العائدات السياحية",
            "إيرادات السياحة",
            "مداخيل السياحة",
        ],
    },
    "tourism": {
        "fr": [
            "tourisme",
            "nuitées",
        ],
        "en": [
            "tourism",
            "overnight stays",
        ],
        "ar": [
            "السياحة",
            "الليالي المقضاة",
        ],
    },
}


INDICATOR_LABELS = {
    "inflation": {
        "fr": "Inflation",
        "en": "Inflation",
        "ar": "التضخم",
    },
    "gdp_growth": {
        "fr": "Croissance du PIB",
        "en": "GDP growth",
        "ar": "نمو الناتج المحلي الإجمالي",
    },
    "unemployment": {
        "fr": "Chômage",
        "en": "Unemployment",
        "ar": "البطالة",
    },
    "exports": {
        "fr": "Exportations",
        "en": "Exports",
        "ar": "الصادرات",
    },
    "imports": {
        "fr": "Importations",
        "en": "Imports",
        "ar": "الواردات",
    },
    "trade_balance": {
        "fr": "Balance commerciale",
        "en": "Trade balance",
        "ar": "الميزان التجاري",
    },
    "fdi": {
        "fr": "Investissements directs étrangers",
        "en": "Foreign Direct Investment",
        "ar": "الاستثمار الأجنبي المباشر",
    },
    "investment": {
        "fr": "Investissement",
        "en": "Investment",
        "ar": "الاستثمار",
    },
    "public_debt": {
        "fr": "Dette publique",
        "en": "Public debt",
        "ar": "الدين العمومي",
    },
    "budget_deficit": {
        "fr": "Déficit budgétaire",
        "en": "Fiscal deficit",
        "ar": "عجز الميزانية",
    },
    "interest_rate": {
        "fr": "Taux directeur",
        "en": "Interest rate",
        "ar": "نسبة الفائدة",
    },
    "exchange_rate": {
        "fr": "Taux de change",
        "en": "Exchange rate",
        "ar": "سعر الصرف",
    },
    "industrial_production": {
        "fr": "Production industrielle",
        "en": "Industrial production",
        "ar": "الإنتاج الصناعي",
    },
    "tourism_revenue": {
        "fr": "Recettes touristiques",
        "en": "Tourism revenues",
        "ar": "العائدات السياحية",
    },
    "tourism": {
        "fr": "Tourisme",
        "en": "Tourism",
        "ar": "السياحة",
    },
}


TOPIC_LABELS = {
    "inflation": "Prix et inflation",
    "gdp_growth": "Croissance économique",
    "unemployment": "Marché du travail",
    "exports": "Commerce extérieur",
    "imports": "Commerce extérieur",
    "trade_balance": "Commerce extérieur",
    "fdi": "Investissement",
    "investment": "Investissement",
    "public_debt": "Finances publiques",
    "budget_deficit": "Finances publiques",
    "interest_rate": "Politique monétaire",
    "exchange_rate": "Marché des changes",
    "industrial_production": "Activité industrielle",
    "tourism_revenue": "Tourisme",
    "tourism": "Tourisme",
}


from app.services.country_registry import CANONICAL_VARIANTS as COUNTRIES
