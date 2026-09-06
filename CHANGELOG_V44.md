# EcoLingua-TN v4.4 — Extraction Reliability

## Corrections
- Normalisation des devises TND, MAD, DZD, EGP, USD et EUR.
- Suppression des chaînes `nan` dans les unités de l'export utilisateur.
- `% du PIB` est désormais distingué de `%`.
- Détection étendue de `réserves officielles de change`.
- Détection étendue de `solde budgétaire primaire`.
- `un an auparavant` ajouté à la résolution contextuelle.
- Confiance interne fondée sur plusieurs éléments de preuve (période, unité/devise, indicateur, pays, relation linguistique) plutôt que deux constantes seulement.
- Conservation du marquage des contradictions : le stress-test contient volontairement des valeurs incompatibles pour un même pays/période, ce qui explique un taux de revue élevé.

## Validation
- 22 tests automatisés passent.
- Benchmark de régression 14 événements : Precision=1.0, Recall=1.0, F1=1.0, Exact Match=1.0.
- Stress-test synthétique 41 pages, extraction directe du texte PDF : 500 événements en ~0.258 s dans l'environnement de développement du 2026-08-21.
- 60 événements `foreign_exchange_reserves` et 10 `primary_balance` détectés sur ce stress-test.
- 0 événement issu des phrases contenant coefficient/p-value/R²/statistique t/erreur standard.

Ces chiffres sont spécifiques aux corpus synthétiques fournis et ne constituent pas une mesure de performance générale sur des rapports réels.
