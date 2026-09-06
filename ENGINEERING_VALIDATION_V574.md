# Validation d’ingénierie - v5.7.4

## Cause racine

Le PDF arabe contenait un calque texte exploitable et la langue était correctement détectée. La reconstruction générique triait toutefois les mots de gauche à droite, inversant les lignes RTL. Le segmentateur exigeait ensuite une majuscule latine après la ponctuation. La page entière était donc éliminée avant l’analyse économique.

## Résultat end-to-end sur `test_economie_arabe_maroc(1).pdf`

- Langue détectée : `ar`
- Passages économiques détectés : 14
- Résultats numériques tracés : 32
- Chiffres inexpliqués : 0
- Événements économiques conservés : 31
- Variation de 0,6 point : détectée puis rejetée comme niveau économique
- Durée mesurée : environ 4 secondes dans l’environnement de validation

Familles vérifiées : PIB observé/estimé/prévu, inflation annuelle et mensuelle, inflation alimentaire, chômage et révision, déficit budgétaire, exportations, importations, compte courant, IDE, taux directeur et réserves de change.

## Non-régression

- Suite complète : 216 tests réussis
- Échecs : 0
- Durée : 39,49 secondes
- Les 211 tests de la v5.7.3 restent réussis.

## Limite honnête

Cette correction traite les PDF arabes possédant un calque texte. Les documents constitués uniquement d’images nécessitent encore une voie OCR arabe, qui ne doit pas être activée silencieusement sans signaler son niveau de confiance.

