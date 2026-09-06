# EcoLingua-TN v4.26 — Stabilisation globale

## Base
v4.25 Consolidated Generalization Engine. Toutes les corrections et tests existants sont conservés.

## Fixed
- Priorité stricte du pays explicite de chaque ligne dans les tableaux multi-pays.
- Le pays du chapitre/document ne peut plus écraser un pays présent dans la ligne du tableau.
- La devise implicite d'une colonne monétaire est désormais résolue à partir du pays de la ligne, et non du pays global du document.
- Conservation des protections existantes : registres pays/devises dynamiques, résolution temporelle, types Observé/Estimé/Prévision, conflits/doublons, exclusion annexes, filtrage économétrique, exports et séries.

## Non-régression
- 136 tests passent, 0 échec sur la suite incluse dans ce livrable.
- Nouveaux tests v4.26 : tableau multi-pays et devise par pays de ligne.

## Important
Le statut `Validé` reste un statut métier explicable et ne doit pas être interprété comme une mesure d'accuracy. Les performances générales doivent être mesurées sur un corpus Gold inédit avant toute correction.
