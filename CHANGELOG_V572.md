# Econia v5.7.2

## Interface

- Navigation latérale stabilisée : un seul clic change de page.
- Valeurs affichées sans zéros décimaux inutiles (`4.400000` devient `4.4`).
- Sélecteur explicite lorsqu'une série contient plusieurs valeurs pour une même année.
- Le choix annuel est appliqué au graphe, aux statistiques, à la vue horizontale et aux exports.
- Axes, graduations, titres et légendes des graphiques utilisent un noir lisible.
- La page Comparer prend en charge les pays, régions, partenaires et groupes économiques.
- Les libellés de comparaison montrent explicitement le type de géographie.

## Protection du moteur

- Aucun fichier dans `app/services` n'a été modifié par cette mise à jour.
- Les règles d'extraction, de validation et de déduplication restent celles de la v5.7.1 fournie.
- 5 tests UI permanents ont été ajoutés.
- Suite complète : 208 tests réussis, 0 échec.
