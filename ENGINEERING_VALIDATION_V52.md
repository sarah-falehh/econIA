# EcoLingua-TN v5.2 — validation d’ingénierie

Date d’exécution : 2026-09-01.

## Baseline reproductible

- ZIP reçu : `ecolinguatn_v50_generalized_event_architecture(1).zip`.
- Sans les dépendances déclarées installées : 141 tests passés, 22 échoués.
- Après installation des dépendances du projet : 163/163 tests passés.
- Cause : l’absence de `pycountry`, `Babel` et `requests` désactivait ou cassait notamment les registres pays/devises et le sélecteur de contenu.

## Corrections v5.2

- Filtrage structurel des pseudo-phrases issues des graduations de graphiques.
- Interdiction de traiter la croissance des prix alimentaires comme croissance du PIB.
- Ajout de familles d’indicateurs : taux directeur, TMM nominal/réel, TCEN/TCER, change bilatéral, CSU, salaire nominal, productivité du travail, marge sur coût salarial, ISC, prix des concurrents et prix de la valeur ajoutée.
- Binding ordonné pour les comparaisons parenthétiques de deux concepts (`A contre B`).
- Test permanent pour chaque famille corrigée.
- `pytest` ajouté aux dépendances afin que la validation soit reproductible.

## Résultat des tests

- Suite complète : **169 passés, 0 échec** en 32,32 s.
- Tests v5.2 ciblés : **6 passés, 0 échec**.

## Exécutions end-to-end

### PDF synthétique complexe (6 pages)

- 96 événements ; 76 Validé, 18 À vérifier, 2 Rejeté.
- Runtime : 12,155 s.

### Rapport « compétitivité-prix » (34 pages, 29 conservées)

- 37 événements ; 14 Validé, 21 À vérifier, 2 Rejeté.
- Runtime : 16,790 s.
- Les faux événements correspondant à la série de graduations `8 %, 7 %, …, 0 %` ont disparu.
- Les valeurs spécialisées ne sont plus automatiquement rabattues sur inflation/PIB : TMM réel, taux directeur, change bilatéral, CSU, salaire, productivité, prix de VA et ISC disposent de codes distincts.

Les CSV complets produits par ces deux runs sont dans `validation_outputs/`.

## Limites connues — importantes

Cette version ne peut pas être qualifiée de « fiable sur n’importe quel PDF ». Aucun moteur déterministe ou NLP ne peut garantir cela sans corpus GOLD représentatif et mesure indépendante.

- Les tableaux multidimensionnels et certaines séries présentes uniquement dans des graphiques restent sous-extraits. Les rejeter évite des faux positifs, mais réduit le rappel.
- Les groupes géographiques (PECO, concurrents asiatiques, etc.) ne sont pas encore modélisés comme une dimension géographique distincte.
- Les périodes moyennes (`2000-2010`, `2001-2016`) ne disposent pas encore d’un schéma complet `period_start/period_end/frequency`; certains événements gardent donc l’année terminale et doivent rester À vérifier.
- La dimension sectorielle n’est pas encore propagée dans tout le schéma d’événement, les conflits et les séries.
- Il n’existe pas encore de GOLD exhaustif, annoté ligne par ligne, pour le rapport de compétitivité. Precision, Recall, F1 et Event Exact Match ne sont donc pas calculés : aucun chiffre n’est inventé.
- Un document scanné sans couche texte nécessite une étape OCR, absente de cette version.

## Prochaine étape nécessaire pour une mesure fiable

Construire une annotation GOLD indépendante, avec provenance page/ligne, couvrant texte, tableaux et graphiques ; étendre le schéma aux périodes-plages, secteurs et groupes géographiques ; puis calculer TP/FP/FN et les exactitudes par champ. Les 169 tests actuels protègent les comportements connus mais ne remplacent pas ce benchmark.
