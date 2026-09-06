# Econia v5.7.4 - Arabic extraction

- Reconstruction RTL dédiée aux pages PDF majoritairement arabes.
- Conservation de l’ordre logique des mots et des frontières de sections arabes.
- Normalisation des diacritiques arabes sans altérer la preuve source stockée.
- Segmentation des phrases avec `.` et `؟`, sans dépendre d’une majuscule latine.
- Ajout des unités et échelles arabes : pourcentage, point de pourcentage, million et milliard.
- Résolution du dirham et du dinar arabes par le pays et le registre ISO existant.
- Ajout des indicateurs arabes nécessaires aux rapports macroéconomiques : PIB, inflation, chômage, déficit, commerce extérieur, compte courant, IDE, taux directeur et réserves.
- Ajout des mois, trimestres et périodes relatives arabes.
- Binding générique des comparaisons `من X إلى Y`, `مقابل`, année/trimestre précédent et trois mois plus tôt.
- Continuité sémantique contrôlée entre lignes RTL coupées par le moteur PDF.
- Aucun recours obligatoire à Qwen ou à un LLM local.

