# EcoLingua-TN v4.1 — fiabilisation du moteur

- Conservation de l'architecture Streamlit et de l'API `run_multi_agent`.
- Moteur recommandé 100 % déterministe : aucun Ollama/LLM local requis.
- Correction des événements atomiques dans les phrases multi-valeurs.
- Séparation stricte encours de dette / ratio de dette.
- Résolution inter-phrases de références comme « l'année précédente » et « l'année suivante ».
- Propagation prudente de l'indicateur et du pays via contexte documentaire.
- Conservation des contradictions réelles avec marquage `À vérifier` au lieu d'un choix arbitraire.
- Exports simples : `observations.csv`, `series.csv`, `statistics.csv`.
- Interface d'extraction simplifiée : les identifiants techniques ne sont plus présentés dans le tableau métier.
- Correction du bug d'intégration `EconomicFact` / métadonnées du pipeline multi-agent.
- Ajout de `pytest.ini` : les tests fonctionnent avec un simple `pytest -q`.
- 16 tests automatisés validés.
