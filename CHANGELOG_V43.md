# EcoLingua-TN v4.3 — Editorial Intelligence UI

## Interface
- Remplacement complet du thème sombre v4.2 par une identité claire éditoriale/fintech.
- Palette papier / encre / cobalt / corail, grille subtile et typographie Manrope + DM Sans.
- Navigation latérale transformée en index numéroté.
- Cartes KPI asymétriques, composants à angles sobres et ombres discrètes.
- Nouveau workspace d'analyse en trois étapes visuelles : source, moteur, lancement.
- Refonte de l'écran d'authentification dans la même identité graphique.
- Suppression du vocabulaire et de l'apparence de chatbot.

## Correctifs
- Migration de `import fitz` vers `import pymupdf` pour supprimer l'avertissement de dépréciation PyMuPDF.
- Correction de la route post-login vers `Vue d’ensemble`.
- Aucun changement volontaire dans la logique d'extraction v4.2 afin de préserver le benchmark.

## Validation
- La suite de tests doit rester identique ou meilleure que v4.2.
