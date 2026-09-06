# v4.26 — Matrice de non-régression

La v4.26 conserve les protections accumulées jusqu'à v4.25 et ajoute les invariants suivants :

- pays explicite de ligne > contexte de tableau > contexte de document > héritage ;
- un changement de pays entre deux lignes d'un même tableau doit être respecté ;
- la devise nationale implicite d'une colonne monétaire suit le pays de la ligne ;
- aucune règle spécifique à un pays n'est ajoutée au parser générique ;
- annexes et bruit économétrique restent exclus ;
- les corrections temporelles, fréquence, observation type, conflits et déduplication restent couvertes par la suite historique.

Résultat de la suite livrée : 136 passed, 0 failed.
