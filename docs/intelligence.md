# R.A.L.F. — Prototype d'intelligence

`intelligence.py` contient une logique expérimentale qui détecte successivement un repère START autour de **20 cm** et un repère END autour de **10 cm**. Elle combine les mesures ultrasoniques avec la baisse de luminosité au passage d'un repère.

> [!WARNING]
> `code.py` n'importe pas et ne lance pas `intelligence.py`. Le programme principal suit une autre séquence : après l'appui sur le bouton, il ouvre la trappe, avance et s'arrête quand la mesure ultrasonique est comprise entre 0 et 10 cm. Le prototype décrit ici ne doit pas être considéré comme le comportement actuellement utilisé par le robot.

## Réglages par défaut

Les valeurs sont définies dans `settings.py` et peuvent être remplacées par des réglages lus via `supervisor.get_setting()`.

| Paramètre | Valeur par défaut | Utilisation |
| --- | ---: | --- |
| `START_PROPAGATION_HEIGHT` | 20 cm | Cible START |
| `END_PROPAGATION_HEIGHT` | 10 cm | Cible END |
| `SECURITY_LEEWAY` | 1 cm | Seuil de secours sous chaque cible |
| `BRIGHTNESS_DROP_DETECTION` | 30 % | Baisse lumineuse minimale par rapport à la référence |
| `DISTANCE_SAMPLES` | 3 | Nombre de lectures pour la médiane |
| `MAX_HEIGHT_CHANGE_CM_PER_READING` | 2 cm | Variation maximale de médiane acceptée par lecture |
| `MAX_INVALID_READINGS` | 8 | Nombre d'anomalies consécutives avant arrêt |
| `BRIGHTNESS_SAMPLES` | 20 | Taille maximale de l'historique lumineux |
| `MIN_BRIGHTNESS_SAMPLES` | 5 | Nombre minimum de mesures pour établir une référence |
| `BRIGHTNESS_CONFIRM_SAMPLES` | 2 | Mesures sombres consécutives exigées |
| `BRIGHTNESS_DETECTION_WINDOW` | 1 cm | Demi-largeur de la fenêtre de détection lumineuse |

Avec les valeurs par défaut, la luminosité peut déclencher START entre **19 et 21 cm** et END entre **9 et 11 cm**. La condition de secours déclenche START à **19 cm ou moins** et END à **9 cm ou moins**, selon la médiane filtrée.

La baisse est relative : avec une référence de 60 %, le seuil de 30 % exige une lecture inférieure ou égale à 42 %.

## Déroulement

1. `run_intelligence()` commande le moteur vers l'avant à 100 %.
2. À chaque tour, il lit la distance et la luminosité. Une distance `None`, négative ou supérieure à 320 cm est invalide : l'historique des distances et le compteur de confirmations lumineuses sont réinitialisés.
3. Après `DISTANCE_SAMPLES` distances valides, le code utilise la médiane. Les variations de médiane supérieures à `MAX_HEIGHT_CHANGE_CM_PER_READING` sont rejetées. Les lectures invalides et les variations rejetées alimentent le compteur de sécurité ; après huit anomalies consécutives, le moteur est arrêté et la fonction retourne.
4. **Calibration START :** tant que la médiane est supérieure à 21 cm, le code conserve au plus 20 mesures lumineuses. En quittant cette zone, il fige leur moyenne si au moins cinq mesures ont été recueillies.
5. **Détection START :** dans la fenêtre 19–21 cm, une luminosité au plus égale à 70 % de la référence doit être observée deux fois de suite. Sinon, le secours ultrasonique déclenche à 19 cm ou moins. START appelle `_run_start_actions()`, puis les historiques lumineux et de distance sont réinitialisés pour la phase suivante.
6. **Calibration END :** après START, le code recueille une nouvelle référence lorsque la médiane se trouve strictement entre 11 et 19 cm. Comme pour START, la moyenne est figée en quittant la zone, à condition d'avoir au moins cinq échantillons.
7. **Détection END :** dans la fenêtre 9–11 cm, deux mesures lumineuses consécutives sous le seuil déclenchent END. Le secours ultrasonique intervient à 9 cm ou moins. `_run_end_actions()` arrête le moteur, puis la boucle se termine.

La médiane réduit l'effet d'une mesure isolée aberrante. Elle n'élimine pas toutes les erreurs : si une lecture est rejetée à cause d'un saut incohérent, l'historique des distances est conservé et une nouvelle médiane sera calculée aux tours suivants.

## État actuel et limites

- **Le prototype n'est pas intégré au programme principal.** Il ne s'exécute que si un autre code l'instancie et appelle `run_intelligence()`.
- `_run_start_actions()` affiche seulement « Déclenchement du début » : elle n'ouvre pas la trappe et n'effectue pas d'autre action. `_run_end_actions()` arrête le moteur et affiche un message.
- Les paramètres `distance_sensor` et `brightness_sensor` passés au constructeur sont vérifiés par `test_values()`, mais les lectures de la boucle passent par `get_height()` et `get_brightness()` dans `utils.py`. Ces fonctions utilisent les composants globaux définis dans `settings.py` ; les capteurs passés au constructeur ne pilotent donc pas les lectures.
- `test_values()` vérifie les deux cibles, leur ordre et les types des capteurs. En cas d'échec, le constructeur affiche un message générique, mais continue quand même : l'exécution n'est pas bloquée et l'erreur n'est pas signalée à l'appelant.
- Si moins de cinq mesures lumineuses sont collectées avant de quitter une zone de calibration, aucune référence n'est figée. La détection lumineuse ne peut alors pas déclencher pour cette phase ; seul le seuil de secours reste disponible.
- La boucle ne contient ni pause ni délai maximal. Sa cadence dépend des lectures matérielles et le robot n'a pas de protection contre un capteur bloqué ou une progression qui n'atteint jamais les seuils.
- Les paramètres `DISTANCE_SAMPLES` et `BRIGHTNESS_CONFIRM_SAMPLES` sont configurables, mais le code suppose une médiane de trois valeurs (`sorted(distance_history)[1]`). Changer `DISTANCE_SAMPLES` de 3 peut produire une médiane incorrecte ou une erreur d'index.
- Les imports et capteurs employés sont propres à CircuitPython. Comme indiqué dans le [README](../README.md), ce fichier ne se lance pas directement avec le Python classique sur ordinateur.

## Pistes d'amélioration

1. **Terminer et valider l'intégration** : fournir de vraies actions START/END, décider si le prototype remplace la séquence de `code.py`, puis tester le comportement sur le robot avec une procédure de sécurité.
2. **Rendre les capteurs injectés réellement utilisables** : lire les objets reçus par le constructeur (ou retirer ces arguments et utiliser explicitement les fonctions globales) afin que les tests et la configuration correspondent au comportement réel.
3. **Corriger les validations** : lever une erreur explicite ou retourner un résultat d'échec plutôt que d'imprimer un message et de poursuivre ; valider également les limites et la cohérence de tous les paramètres.
4. **Rendre les filtres cohérents avec leur configuration** : calculer la médiane correctement pour un nombre configurable d'échantillons, ou imposer clairement une taille de trois.
5. **Renforcer les sécurités** : définir le comportement pour une lecture lumineuse invalide, ajouter une durée maximale de déplacement, arrêter explicitement le moteur lors de toute sortie anormale, et traiter l'échec d'initialisation du capteur.
6. **Tester les cas limites** : absence d'écho, valeurs hors plage, sauts de distance, référence lumineuse insuffisante, scotch manqué et conditions de luminosité changeantes. Le simulateur fournit un point de départ, mais ne remplace pas des essais physiques.

Le modèle et les résultats enregistrés de la simulation sont présentés dans [la documentation dédiée](simulations.md).
