# EcoLingua-TN v4.2 — Professional Intelligence Workspace

## Extraction
- support des phrases contextuelles courtes telles que `En 2022, il atteignait 8,3 %`;
- détection des trimestres écrits en toutes lettres;
- résolution de `trimestre précédent` avec passage d'année correct;
- suppression de la fuite de contexte trimestriel vers un nouvel indicateur annuel;
- résolution correcte de `Pour 2025 ... devrait atteindre ... après ... en 2024`;
- distinction prévision / observation dans une même phrase;
- conservation du moteur sans LLM génératif local.

## Interface
- nouvelle direction visuelle dark economic-intelligence;
- navigation réorganisée: Vue d'ensemble, Nouvelle analyse, Observations, Séries, Visualisations, Statistiques, Sources, Comparer, Exporter;
- suppression de l'assistant RAG de la navigation et du code produit;
- colonnes techniques masquées de l'interface métier;
- statut robuste même lorsqu'une colonne optionnelle est absente;
- `Confiance moyenne` n'est plus présentée comme une métrique d'accuracy.

## Evaluation
- gold dataset fixe de 14 événements;
- calcul automatique Precision, Recall, F1, Event Exact Match et accuracies par champ;
- mesure du temps, events/s et RSS mémoire;
- résultats versionnés en JSON;
- journal expérimental `evaluation/EXPERIMENTS.md`.

## Tests
- 19 tests automatisés validés.
- ajout de régressions pour coréférence courte, trimestres, fuite de contexte et prévision/historique.
