# EcoLingua-TN v4.2 — Audit de professionnalisation

## KEEP
- `app/services/multi_agent_pipeline.py`: moteur déterministe principal, renforcé en v4.2.
- `context_resolver.py`: contexte inter-phrases et périodes relatives.
- `indicator_catalog.py` / `indicator_registry.py`: ontologie et normalisation économique.
- `content_selector.py`: filtrage documentaire avant extraction.
- `pdf_reader.py`, `csv_reader.py`, `document_loader.py`: ingestion.
- `series_analytics.py`, `analytics_service.py`: séries et statistiques.
- `database.py`, `auth_service.py`: persistance, rôles et traçabilité.
- `workspace.py`: ingestion existante, relookée sans réécriture du moteur.

## REFACTOR
- `economic_extractor.py`: reste compatible mais doit continuer à évoluer vers un orchestrateur plus mince.
- `multi_agent_pipeline.py`: le nom public est conservé pour compatibilité, bien que le moteur soit désormais déterministe et non un système LLM multi-agent.
- `content_selector.py`: conserve encore le mode Ollama historique optionnel; le chemin recommandé n'en dépend pas.
- schémas DataFrame/UI: rendus robustes aux colonnes optionnelles; les métadonnées techniques sont cachées de l'interface principale.

## MERGE / CENTRALIZE
- thème et design centralisés dans `app/ui/theme.py`.
- vues métier unifiées dans `app/views/professional_views.py` pour éviter la duplication de navigation et de cartes.
- benchmark centralisé sous `evaluation/`.

## REMOVE
- anciens `README_V22...V32.md`: historiques redondants qui brouillaient la version courante.
- ancien Assistant RAG (`app/views/rag_assistant.py`, `app/services/rag_service.py`) et index `data/rag/`: fonctionnalité hors périmètre du produit d'extraction actuel et absente de la nouvelle navigation.

## Non supprimé volontairement
- `ollama_client.py`: encore importé par le sélecteur de contenu historique; suppression reportée jusqu'à retrait propre du mode Ollama.
- vues de validation/contradictions historiques: conservées côté code pour ne pas casser les workflows existants, mais retirées de la navigation principale au profit du workspace métier unifié.
