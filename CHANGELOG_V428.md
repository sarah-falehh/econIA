# EcoLingua-TN v4.28 — Analyst Workspace

## UX métier ajoutée
- Export direct de la série sélectionnée en CSV.
- Classeur Excel par série avec onglets `Série` et `Synthèse`.
- Nom de fichier généré à partir du pays et de l’indicateur.
- Tableau de série enrichi : pays, indicateur, période, valeur, unité, type, statut, confiance, source.
- Cartes utiles : nombre de points, dernière valeur observée, points à vérifier, prévisions.
- Comparaison jusqu’à 3 pays pour un même indicateur.
- Comparaison jusqu’à 3 indicateurs pour un même pays.
- Export CSV de la comparaison actuellement affichée.

## Conservation moteur
Cette version part de v4.27. Aucun changement n’a été apporté au moteur d’extraction, au registre pays/devises, aux règles temporelles, au parsing des tableaux, aux conflits ou au filtrage des annexes.

## Non-régression
- 139 tests passés, 0 échec.
- Compilation des vues Streamlit réussie.
