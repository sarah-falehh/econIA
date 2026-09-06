from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline


MODEL_PATH = Path(
    "data/models/economic_sentence_classifier.joblib"
)


@dataclass
class TopicPrediction:
    label: str
    confidence: float


SEED_EXAMPLES = {
    "inflation": [
        "The inflation rate declined to 6.7 percent in June.",
        "Consumer prices increased during the month.",
        "Food price inflation remained elevated.",
        "Le taux d'inflation a baissé en juin.",
        "Les prix à la consommation ont augmenté.",
        "La hausse des prix alimentaires ralentit.",
        "تراجع معدل التضخم خلال شهر جوان.",
        "ارتفعت أسعار الاستهلاك.",
        "انخفضت نسبة التضخم السنوي.",
    ],
    "gdp_growth": [
        "GDP growth reached 2.8 percent in the second quarter.",
        "The economy expanded during the quarter.",
        "Gross domestic product contracted last year.",
        "La croissance du PIB a atteint 2,8 pour cent.",
        "L'économie a progressé au deuxième trimestre.",
        "Le produit intérieur brut s'est contracté.",
        "بلغ نمو الناتج المحلي الإجمالي 2.8 بالمائة.",
        "سجل الاقتصاد نموا خلال الربع الثاني.",
        "تراجع الناتج المحلي الإجمالي.",
    ],
    "unemployment": [
        "The unemployment rate remained at 15.2 percent.",
        "Youth unemployment declined during the quarter.",
        "The jobless rate increased.",
        "Le taux de chômage est resté stable.",
        "Le chômage des jeunes a diminué.",
        "Le nombre de demandeurs d'emploi augmente.",
        "استقرت نسبة البطالة عند 15 بالمائة.",
        "انخفضت بطالة الشباب.",
        "ارتفع معدل البطالة.",
    ],
    "interest_rate": [
        "The central bank kept its key interest rate at 8 percent.",
        "The policy rate was left unchanged.",
        "Interest rates were raised by the central bank.",
        "La banque centrale a maintenu son taux directeur.",
        "Le taux d'intérêt a été relevé.",
        "La politique monétaire reste restrictive.",
        "أبقى البنك المركزي على نسبة الفائدة المديرية.",
        "تم رفع سعر الفائدة.",
        "استقرت نسبة الفائدة.",
    ],
    "exports": [
        "Exports increased by 9.4 percent.",
        "Export sales rose during the first half.",
        "Goods exports declined year on year.",
        "Les exportations ont progressé.",
        "Les ventes à l'étranger ont augmenté.",
        "Les exportations de biens ont reculé.",
        "ارتفعت الصادرات بنسبة 9 بالمائة.",
        "تراجعت مبيعات التصدير.",
        "نمت الصادرات خلال السنة.",
    ],
    "imports": [
        "Imports grew by 6.1 percent.",
        "Import purchases declined.",
        "The country imported more goods.",
        "Les importations ont augmenté.",
        "Les achats à l'étranger ont baissé.",
        "La valeur des importations progresse.",
        "ارتفعت الواردات.",
        "تراجعت قيمة التوريد.",
        "زادت واردات السلع.",
    ],
    "trade_balance": [
        "The trade deficit narrowed.",
        "The trade surplus increased.",
        "The trade balance deteriorated.",
        "Le déficit commercial s'est réduit.",
        "La balance commerciale s'est améliorée.",
        "L'excédent commercial a augmenté.",
        "تراجع العجز التجاري.",
        "تحسن الميزان التجاري.",
        "ارتفع الفائض التجاري.",
    ],
    "fdi": [
        "Foreign direct investment reached 1.45 billion dinars.",
        "FDI inflows increased.",
        "Foreign investors invested more capital.",
        "Les investissements directs étrangers ont augmenté.",
        "Les IDE ont atteint un milliard de dinars.",
        "Les flux d'investissement direct étranger progressent.",
        "بلغ الاستثمار الأجنبي المباشر مليار دينار.",
        "ارتفعت تدفقات الاستثمارات الأجنبية المباشرة.",
        "تراجع الاستثمار الأجنبي المباشر.",
    ],
    "public_debt": [
        "Public debt represented 78.6 percent of GDP.",
        "Government debt declined.",
        "The sovereign debt ratio increased.",
        "La dette publique représente 78 pour cent du PIB.",
        "L'endettement public a diminué.",
        "Le ratio de dette de l'Etat augmente.",
        "بلغ الدين العمومي 78 بالمائة من الناتج.",
        "تراجعت المديونية العامة.",
        "ارتفعت نسبة الدين العام.",
    ],
    "budget_deficit": [
        "The fiscal deficit narrowed to 3.4 percent of GDP.",
        "The budget deficit increased.",
        "Government finances recorded a deficit.",
        "Le déficit budgétaire s'est réduit.",
        "Le déficit public a augmenté.",
        "Les finances publiques restent déficitaires.",
        "تراجع عجز الميزانية.",
        "ارتفع العجز المالي.",
        "سجلت الميزانية عجزا.",
    ],
    "tourism_revenue": [
        "Tourism revenues reached 3.8 billion dinars.",
        "Tourism receipts increased during the first half.",
        "Foreign currency earnings from tourism declined.",
        "Les recettes touristiques ont atteint trois milliards.",
        "Les revenus du tourisme progressent.",
        "Les recettes du secteur touristique ont baissé.",
        "بلغت العائدات السياحية ثلاثة مليارات دينار.",
        "ارتفعت إيرادات السياحة.",
        "تراجعت مداخيل القطاع السياحي.",
    ],
    "exchange_rate": [
        "The exchange rate of the dinar depreciated.",
        "The currency strengthened against the euro.",
        "The dinar exchange rate remained stable.",
        "Le taux de change du dinar s'est déprécié.",
        "La monnaie s'est appréciée face à l'euro.",
        "Le cours de change est stable.",
        "تراجع سعر صرف الدينار.",
        "تحسنت قيمة العملة مقابل اليورو.",
        "استقر معدل الصرف.",
    ],
    "other": [
        "The minister attended an international conference.",
        "The report contains fifty pages.",
        "The institution published a new document.",
        "Le ministre a participé à une réunion.",
        "Le rapport contient plusieurs chapitres.",
        "L'organisation a publié un communiqué.",
        "شارك الوزير في اجتماع دولي.",
        "يحتوي التقرير على عدة صفحات.",
        "نشرت المؤسسة وثيقة جديدة.",
    ],
}


def training_dataset() -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []

    for label, examples in SEED_EXAMPLES.items():
        for example in examples:
            texts.append(example)
            labels.append(label)

    return texts, labels


def create_pipeline() -> Pipeline:
    features = FeatureUnion(
        [
            (
                "word",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                    min_df=1,
                    max_features=12000,
                ),
            ),
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb",
                    lowercase=True,
                    ngram_range=(3, 5),
                    sublinear_tf=True,
                    min_df=1,
                    max_features=18000,
                ),
            ),
        ]
    )

    return Pipeline(
        [
            ("features", features),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2500,
                    class_weight="balanced",
                    C=4.0,
                    random_state=42,
                ),
            ),
        ]
    )


def train_classifier(
    force: bool = False,
) -> Pipeline:
    if MODEL_PATH.exists() and not force:
        return joblib.load(MODEL_PATH)

    texts, labels = training_dataset()
    pipeline = create_pipeline()
    pipeline.fit(texts, labels)

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        pipeline,
        MODEL_PATH,
    )

    return pipeline


def get_classifier() -> Pipeline:
    return train_classifier(
        force=False
    )


def predict_topics(
    text: str,
    top_k: int = 3,
) -> list[TopicPrediction]:
    cleaned = (text or "").strip()

    if not cleaned:
        return []

    model = get_classifier()
    probabilities = model.predict_proba(
        [cleaned]
    )[0]

    classes = model.classes_
    order = np.argsort(
        probabilities
    )[::-1][:top_k]

    return [
        TopicPrediction(
            label=str(classes[index]),
            confidence=round(
                float(probabilities[index]),
                4,
            ),
        )
        for index in order
    ]


def primary_topic(
    text: str,
) -> TopicPrediction:
    predictions = predict_topics(
        text,
        top_k=1,
    )

    if not predictions:
        return TopicPrediction(
            label="other",
            confidence=0.0,
        )

    return predictions[0]


def model_information() -> dict:
    texts, labels = training_dataset()

    return {
        "model_path": str(MODEL_PATH),
        "training_examples": len(texts),
        "labels": sorted(set(labels)),
        "model_exists": MODEL_PATH.exists(),
        "architecture": (
            "TF-IDF mots + caractères "
            "+ régression logistique"
        ),
    }
