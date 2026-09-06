# Validation d’ingénierie — v5.7.3

## Cause racine

Les groupes économiques étaient présents dans les observations, mais le sélecteur de comparaison était construit après le choix de l’indicateur. Un indicateur disponible uniquement pour la Tunisie supprimait donc PECO et Concurrents asiatiques de la liste.

## Correction

Le parcours sélectionne désormais les géographies parmi l’inventaire global, puis calcule les indicateurs communs. Si aucune intersection n’existe, l’interface explique explicitement la disponibilité partielle.

Le choix d’une valeur en double est désormais un contrôle segmenté compact associé visuellement au graphe. Une seule valeur par année alimente le tracé, les statistiques et les exports.

## Vérification

- Suite complète : 211 tests réussis, 0 échec, en 36,93 secondes.
- Nouveaux tests : ordre géographies/indicateurs, intersection des indicateurs, contrôle compact des doublons et tailles de police.
- Périmètre : interface uniquement ; aucun fichier sous `app/services` n’a été modifié pour cette version.

