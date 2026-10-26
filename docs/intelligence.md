# R.A.L.F. — Intelligence et architecture de décision

`intelligence.py` contient la logique de détection expérimentale du robot. Elle analyse successivement un repère `START`
autour de **20 cm** puis un repère `END` autour de **10 cm**. La décision repose sur un filtrage ultrasonique et sur une
baisse relative de luminosité dans la zone cible.

> [!NOTE]
> La logique décrite ici est bien celle actuellement appelée par `code.py` via `brain.run_intelligence()`. La structure
de la boucle principale a été refactorisée pour clarifier les états `WAITING` et `ACTION`, mais la logique de détection
elle-même reste inchangée.

## Architecture de la boucle principale

Le programme principal a été organisé en deux blocs distincts :

- `WAITING` : le robot surveille le bouton de démarrage et affiche sa luminosité / distance.
- `ACTION` : lorsque le bouton est appuyé, il exécute `Intelligence.run_intelligence()`.

Cette structure est gérée dans `code.py`, tandis que `intelligence.py` porte la logique métier de détection et d’action.

## Réglages par défaut

Les valeurs sont définies dans `settings.py` et peuvent être remplacées via `supervisor.get_setting()`.

| Paramètre                          | Valeur par défaut | Utilisation                                          |
|------------------------------------|------------------:|------------------------------------------------------|
| `START_PROPAGATION_HEIGHT`         |             20 cm | Cible START                                          |
| `END_PROPAGATION_HEIGHT`           |             10 cm | Cible END                                            |
| `SECURITY_LEEWAY`                  |              1 cm | Seuil de secours sous chaque cible                   |
| `BRIGHTNESS_DROP_DETECTION`        |              30 % | Baisse lumineuse minimale par rapport à la référence |
| `DISTANCE_SAMPLES`                 |                 3 | Nombre de lectures pour la médiane                   |
| `MAX_HEIGHT_CHANGE_CM_PER_READING` |              2 cm | Variation maximale de médiane acceptée par lecture   |
| `MAX_INVALID_READINGS`             |                 8 | Nombre d’anomalies consécutives avant arrêt          |
| `BRIGHTNESS_SAMPLES`               |                20 | Taille maximale de l’historique lumineux             |
| `MIN_BRIGHTNESS_SAMPLES`           |                 5 | Nombre minimum de mesures pour établir une référence |
| `BRIGHTNESS_CONFIRM_SAMPLES`       |                 2 | Mesures sombres consécutives exigées                 |
| `BRIGHTNESS_DETECTION_WINDOW`      |              1 cm | Demi-largeur de la fenêtre de détection lumineuse    |

Avec les valeurs par défaut, la luminosité peut déclencher `START` entre **19 et 21 cm** et `END` entre **9 et 11 cm**.
Le secours ultrasonique déclenche `START` à **19 cm ou moins** et `END` à **9 cm ou moins** selon la médiane filtrée.

## Déroulement de l’intelligence

1. `run_intelligence()` commande le moteur vers l’avant à 100 %.
2. À chaque tour, la fonction lit la distance et la luminosité.
3. Une distance `None`, négative ou supérieure à 320 cm est invalide : l’historique des distances est réinitialisé et le
   compteur de sécurité augmente.
4. Après `DISTANCE_SAMPLES` mesures valides, le code applique la médiane glissante. Si une variation de médiane est trop
   brusque, la lecture est rejetée.
5. **Calibration START :** tant que la médiane est supérieure à `START_PROPAGATION_HEIGHT + SECURITY_LEEWAY`, le code
   collecte des valeurs lumineuses en vue d’établir une référence.
6. **Détection START :** dans la zone cible, si la luminosité tombe suffisamment et si la condition est confirmée
   plusieurs fois, alors `START` est déclenché. Sinon, le secours ultrasonique peut aussi déclencher la même action.
7. Après `START`, la logique réinitialise les historiques pour la phase `END` et recalibre la référence sur le câble
   gris.
8. **Détection END :** lorsque la médiane entre dans la fenêtre de fin, la logique applique la même logique.
   `_run_end_actions()` arrête le moteur et ferme la trappe.
9. Une lecture invalide répétée ou un saut incohérent trop important déclenche `_run_emergency_actions()` et stoppe le
   robot.

La médiane réduit l’effet d’une mesure isolée aberrante. Elle n’élimine pas toutes les erreurs, mais apporte une
stabilité utile dans le cadre d’un prototype et d’une validation simulée.

## État actuel et limites

- La logique d’intelligence est maintenant bien intégrée dans la boucle principale via `code.py`, mais reste un
  prototype de détection, pas une solution totalement robuste pour un usage industriel ou de terrain.
- Les capteurs passés au constructeur sont vérifiés, mais les lectures de la boucle passent encore par `get_height()` et
  `get_brightness()` dans `utils.py`; ce point reste une zone à améliorer pour rendre l’architecture plus testable.
- `test_values()` valide la cohérence des seuils et des types, mais la gestion d’erreur doit encore être renforcée pour
  des essais physiques réels.
- La boucle ne contient ni délai maximal absolu ni mécanisme de watchdog complet. Le robot reste dépendant de la
  stabilité du capteur et des conditions environnementales.
- Les imports et capteurs employés sont propres à CircuitPython ; le code ne se lance pas directement sur Python
  standard.

## Pistes d’amélioration

1. **Rendre les capteurs injectés réellement utilisables** : utiliser directement les objets reçus plutôt que de
   dépendre des globals.
2. **Renforcer les validations** : lever des exceptions explicites ou retourner un statut détaillé plutôt que de
   continuer silencieusement.
3. **Sécuriser les lectures** : valider les `None`, les dépassements, les temporisations et les capteurs bloqués.
4. **Rendre le filtre cohérent avec une configuration variable** : calculer correctement la médiane pour un nombre
   configurable d’échantillons ou imposer clairement une taille de 3.
5. **Ajouter des états explicites** : `INITIALIZING`, `WAITING`, `ACTION`, `EMERGENCY_STOP`, `DONE` pour gagner en
   lisibilité et testabilité.
6. **Valider sur le robot réel** : les simulations sont utiles, mais les essais matérielle restent indispensables avant
   un usage fiable.

Le modèle et les résultats des simulations sont présentés dans [simulations.md](simulations.md).
