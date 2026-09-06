# Nomenclature des indicateurs — EcoLingua V40

Cette version distingue le **concept détecté dans le document** du **code externe officiel**.

Principes :

1. Le moteur n'invente pas « réel », « brut », « administrations publiques », « IPC » ou « IPCH » si le document ne les mentionne pas.
2. `Taux de croissance du PIB (variation annuelle)` est le libellé canonique par défaut. Il devient `Taux de croissance du PIB réel` uniquement lorsque le texte mentionne le PIB réel ou les prix constants.
3. `Dette publique (% du PIB)` reste générique. Le code FMI `GGXWDG_NGDP` n'est affecté que si le texte décrit explicitement la dette brute des administrations publiques.
4. Chaque événement reçoit un `indicator_id` interne stable et un `series_id` construit à partir du pays, de l'indicateur et de l'unité.
5. Les exports regroupent les séries par **pays + indicateur + unité**, afin d'éviter de mélanger plusieurs pays ou plusieurs mesures.

Référentiels consultés : Banque mondiale WDI, FMI WEO, OCDE et Eurostat.
