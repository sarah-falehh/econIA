from __future__ import annotations

"""Lightweight multilingual semantic indicator matcher.

This version deliberately avoids PyTorch, Transformers and model downloads.
It uses a local TF-IDF word/character similarity model built from the economic
indicator catalogue. The API is unchanged, so the rest of EcoLingua continues
to work without modification.
"""

from functools import lru_cache
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import FeatureUnion


INDICATOR_DESCRIPTIONS = {
    "gdp_growth": "economic growth gross domestic product GDP growth real GDP PIB croissance économique الناتج المحلي الإجمالي النمو الاقتصادي",
    "inflation": "inflation consumer prices CPI price level hausse des prix indice des prix التضخم أسعار المستهلك",
    "interest_rate": "central bank policy interest rate key rate taux directeur taux d'intérêt سعر الفائدة البنك المركزي",
    "unemployment": "unemployment jobless rate labour market chômage taux de chômage البطالة سوق العمل",
    "public_debt": "public government debt sovereign debt dette publique الدين العمومي الدين الحكومي",
    "fiscal_deficit": "budget fiscal deficit government balance déficit budgétaire solde public عجز الميزانية",
    "trade_balance": "trade balance current account merchandise deficit balance commerciale déficit commercial الميزان التجاري العجز التجاري",
    "exports": "exports exported goods and services exportations صادرات الصادرات",
    "imports": "imports imported goods and services importations واردات الواردات",
    "fdi": "foreign direct investment FDI investissement direct étranger IDE الاستثمار الأجنبي المباشر",
    "investment": "investment capital formation investissement استثمار تكوين رأس المال",
    "tourism_revenue": "tourism receipts tourism revenues recettes touristiques revenus touristiques عائدات السياحة الإيرادات السياحية",
    "tourism": "tourism visitors arrivals nights tourisme touristes nuitées سياحة سياح ليالي",
    "exchange_rate": "exchange rate currency appreciation depreciation taux de change devise سعر الصرف العملة",
    "industrial_production": "industrial production manufacturing output production industrielle industrie الإنتاج الصناعي",
    "remittances": "worker remittances transfers from abroad transferts des migrants تحويلات العاملين",
}


@lru_cache(maxsize=1)
def _build_model():
    codes = list(INDICATOR_DESCRIPTIONS)
    texts = [INDICATOR_DESCRIPTIONS[code] for code in codes]

    vectorizer = FeatureUnion([
        ("word", TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            analyzer="word",
            sublinear_tf=True,
        )),
        ("char", TfidfVectorizer(
            lowercase=True,
            ngram_range=(3, 5),
            analyzer="char_wb",
            sublinear_tf=True,
        )),
    ])
    catalog_matrix = vectorizer.fit_transform(texts)
    return codes, vectorizer, catalog_matrix


def semantic_scores(sentence: str, candidate_codes: Iterable[str] | None = None) -> dict[str, float]:
    if not sentence or len(sentence.strip()) < 5:
        return {}

    try:
        codes, vectorizer, catalog_matrix = _build_model()
        query = vectorizer.transform([sentence])
        similarities = cosine_similarity(query, catalog_matrix)[0]
        scores = {code: float(similarities[i]) for i, code in enumerate(codes)}

        if candidate_codes is not None:
            allowed = set(candidate_codes)
            scores = {code: score for code, score in scores.items() if code in allowed}

        return scores
    except Exception:
        return {}
