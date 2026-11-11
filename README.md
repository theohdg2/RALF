# R.A.L.F. — Robot autonome de largage forestier

R.A.L.F. se déplace sur un câble incliné pour déposer un produit dans une zone délimitée par **deux scotchs noirs**, puis poursuit sa descente jusqu'à un **troisième repère de fin de parcours**.

- **Matériel :** Raspberry Pi Pico H + WuKong 2040, moteur CC, servo de trappe, capteur ultrasonique DFRobot URM09, capteur analogique de luminosité, bouton, NeoPixels et buzzer.
- **Logiciel embarqué :** CircuitPython. `code.py` initialise les composants ; `intelligence.py` gère les trois phases de déplacement.
- **Version de référence :** [commit `09d18173`](https://github.com/theohdg2/RALF/commit/09d18173bf2fbf4929e6efc80dad23aeef4f6da3), message `update small bugs`. Les modifications documentées ici constituent **un patch local**, non publié dans ce commit.

## Fonctionnement

| Étape | Repère | Trappe | Commande moteur |
|---|---|---|---|
| Approche et calibration | Avant le 1er scotch noir | Fermée | `MOTOR_POWER_BEFORE_RELEASE` |
| Début du largage | 1er scotch noir | Ouverture | `MOTOR_POWER_DURING_RELEASE` |
| Fin du largage | 2e scotch noir | Fermeture | `MOTOR_POWER_AFTER_RELEASE` |
| Fin du parcours | 3e repère | Fermée | Arrêt à 0 % |

**Le deuxième scotch ne doit plus arrêter le moteur.** Le robot poursuit sa descente, trappe fermée, jusqu'au troisième repère ou à la hauteur d'arrêt programmée.

> **Repère final :** le BOSCARD évoque une « couleur spécifique » sans la préciser. Le capteur de luminosité existant mesure un contraste, **pas une couleur**. Le mode `CONTRAST_OR_DISTANCE` détecte une variation claire ou sombre proche de la hauteur cible ; `DISTANCE_ONLY` utilise uniquement la hauteur. Le fonctionnement optique doit être validé sur le scotch réel.

## Installation

1. Installer une version de CircuitPython compatible avec le Pico H et la carte WuKong 2040.
2. Placer `code.py`, `intelligence.py`, `settings.py`, `settings.toml`, `utils.py`, `servo.py` et `available_musics.py` à la racine du volume `CIRCUITPY`.
3. Copier les bibliothèques de `lib/`, notamment `wumons`, `wumons_i2c`, `adafruit_motor`, ainsi que les dépendances Adafruit nécessaires (`adafruit_bus_device`, `adafruit_pixelbuf`, etc.).
4. Modifier les hauteurs, les trois puissances moteur et les paramètres optiques dans `settings.toml`, puis démarrer avec le bouton connecté sur GP28.

**Installation depuis le patch :** copier les fichiers du ZIP **à leur emplacement correspondant** dans un clone du dépôt. Ne pas remplacer tout le dossier `lib/` par le sous-dossier partiel de l'archive : seul `lib/wumons/motor.py` y est modifié.

### Brochage

| Élément | Connexion |
|---|---|
| Moteur CC | GP10, GP11 |
| Servo trappe | GP6 |
| Bouton de départ | GP28 |
| Luminosité analogique | GP26 |
| URM09 en I²C | GP17 (SCL), GP16 (SDA), adresse `0x11` |
| NeoPixels | GP22 |
| Buzzer | GP9 |

## Réglages dans `settings.toml`

### Les trois puissances indépendantes

```toml
MOTOR_POWER_BEFORE_RELEASE = 100
MOTOR_POWER_DURING_RELEASE = 100
MOTOR_POWER_AFTER_RELEASE = 100
```

Les valeurs autorisées sont **strictement supérieures à 0 et inférieures ou égales à 100**. Il s'agit de commandes PWM en pourcentage, **pas de vitesses physiques** ; 0 % ne garantit pas un freinage mécanique du robot sur un câble incliné.

### Positions et détection

| Réglage | Valeur de démonstration | Rôle |
|---|---:|---|
| `START_PROPAGATION_HEIGHT` | 20 cm | Premier scotch, ouverture |
| `END_PROPAGATION_HEIGHT` | 10 cm | Deuxième scotch, fermeture |
| `STOP_PROPAGATION_HEIGHT` | 5 cm | Troisième repère et hauteur d'arrêt |
| `SECURITY_LEEWAY` | 1 cm | Secours ultrasonique sous les deux premiers repères |
| `BRIGHTNESS_DROP_DETECTION` | 30 % | Baisse lumineuse requise sur les scotchs noirs |
| `STOP_DETECTION_MODE` | `"CONTRAST_OR_DISTANCE"` | Contraste ou distance, ou `"DISTANCE_ONLY"` |
| `STOP_BRIGHTNESS_CHANGE_PERCENT` | 20 % | Variation lumineuse relative du troisième repère |
| `DISTANCE_SAMPLES` | 3 | Médiane ultrasonique, taille imposée par l'algorithme |
| `MAX_INVALID_READINGS` | 8 | Nombre de rejets successifs avant arrêt |
| `MAX_HEIGHT_CHANGE_CM_PER_READING` | 2 cm | Seuil initial de cohérence |
| `MAX_MEDIAN_JUMP_CM` | 4 cm | Plafond absolu des sauts de médiane |
| `BRIGHTNESS_SAMPLES` | 20 | Historique de calibration optique |
| `MIN_BRIGHTNESS_SAMPLES` | 5 | Minimum pour figer la référence |
| `BRIGHTNESS_CONFIRM_SAMPLES` | 2 | Lectures consécutives pour confirmer un contraste |
| `BRIGHTNESS_DETECTION_WINDOW` | 1 cm | Demi-largeur de la zone de détection optique |
| `TRAPDOOR_OPEN_ANGLE` | 45° | Angle d'ouverture de la trappe |
| `SENSOR_READ_INTERVAL_S` | 0,05 s | Pause demandée entre lectures |
| `MAX_RUN_TIME_S` | 120 s | Limite temporelle globale de mission |

**Ordre obligatoire :** `0 < STOP_PROPAGATION_HEIGHT < END_PROPAGATION_HEIGHT < START_PROPAGATION_HEIGHT <= 320`. Les trois zones de détection lumineuse ne doivent pas se chevaucher. **Les 5 cm du dernier repère sont provisoires**, pas une donnée fournie dans le BOSCARD.

`settings.py` lit les valeurs de `settings.toml` avec `supervisor.get_setting()`. La logique de validation est dans `Intelligence.test_values()`.

## Tests sur ordinateur (Python)

Le dossier `tests/` teste **le patch `intelligence.py` avec des faux capteurs et actionneurs**. Il n'exige ni carte Pico ni bibliothèques matérielles pour ces tests. **Python 3.11 ou plus récent** est requis (`tomllib`).

Depuis la **racine du projet**, dans le dossier contenant `intelligence.py`, `settings.toml` et `tests/` :

```bash
python -m unittest discover -s tests -v
```

Sous Windows, si `python` ne fonctionne pas :

```powershell
py -m unittest discover -s tests -v
```

**Résultat attendu pour le patch fourni :** `Ran 16 tests` puis `OK`.

Ces tests vérifient les trois transitions, les trois puissances, les arrêts par contraste et par distance, les erreurs de capteurs, le timeout, la validation des paramètres, la persistance de la calibration du servo et le nouveau simulateur. Ils **ne valident pas** la vitesse réelle, la tenue mécanique sur le câble, le contraste du troisième scotch ni le freinage physique.

## Nouvelle campagne de simulation (3 repères)

Le fichier **`simulation.py` exécute désormais la classe réelle `Intelligence`** de `intelligence.py`,
avec un faux capteur ultrasonique, un faux capteur lumineux, un moteur et une horloge simulés.
Il ne reproduit donc pas manuellement une deuxième version de l'algorithme.

Depuis la racine du projet, avec **Python 3.11+** :

```powershell
# Tests automatisés rapides (16 tests)
python -m unittest discover -s tests -v

# Campagne normale, 10 000 descentes
python simulation.py --count 10000 --seed 0 --profile standard --output results/standard_10000.csv

# Campagne avec défauts de capteurs fréquents, 10 000 descentes
python simulation.py --count 10000 --seed 10000 --profile stress --output results/stress_10000.csv

# Rejouer une seule seed avec la trace des actions
python simulation.py --count 1 --seed 576 --profile standard --verbose
```

L'exécution produit un **CSV par seed** et un fichier associé `*.summary.json`
qui contient les réglages utilisés et les résultats agrégés. Le rapport affiche le nombre
de missions terminées, les arrêts d'urgence et la précision simultanée sur les **trois repères**.

### Paramètres du simulateur

| Option | Valeur par défaut | Rôle |
|---|---:|---|
| `--profile standard` ou `--profile stress` | `standard` | Niveau de bruit et de fausses lectures |
| `--count` | 1 000 | Nombre de descentes |
| `--seed` | 0 | Première seed, rejouable à l'identique |
| `--speed` | 2,0 cm/s | Vitesse **supposée** à 100 % de PWM |
| `--marker-half-width` | 0,6 cm | Demi-largeur simulée des scotchs |
| `--final-marker bright/dark/none` | `bright` | Contraste du dernier repère ou absence de scotch |
| `--settings` | `settings.toml` | Fichier des trois puissances et des seuils du robot |
| `--output` | `results/...csv` | Emplacement du journal des essais |
| `--verbose` | désactivé | Actions et hauteurs détaillées, pour 1 seed de préférence |

Le simulateur applique les puissances de `settings.toml` à sa vitesse de déplacement **supposée proportionnelle au PWM**.
Il n'intègre ni inertie, ni glissement, ni vitesse mesurée, ni freinage réel. Le troisième scotch
est simulé plus clair par défaut, **sans supposer la couleur du scotch réel**.

Les statistiques de 200 000 descentes conservées dans [docs/simulations.md](docs/simulations.md)
concernent **l'ancien simulateur à deux repères** et ne sont pas comparables directement à ces campagnes.


## Sécurité et limites

- L'initialisation échoue si l'URM09 ne répond pas ; une configuration invalide empêche le départ.
- Un dépassement de `MAX_RUN_TIME_S`, trop de mesures incohérentes ou une exception interrompt la mission.
- Le programme ordonne un arrêt moteur et une fermeture de la trappe dans son bloc `finally`. Cela n'assure pas le freinage mécanique si le robot descend librement.
- Le filtrage ultrasonique comprend un saut plafonné par `MAX_MEDIAN_JUMP_CM`, à vérifier en fonction de la vitesse réelle.
- Les mesures lumineuses doivent être calibrées avec la distance capteur–câble et l'éclairage effectifs.

## Fichiers

```text
code.py                     Point d'entrée CircuitPython
intelligence.py             Détection et actions des trois repères
settings.py                 Paramètres et périphériques matériels
settings.toml               Configuration réglable
utils.py                    Commandes moteur, capteurs, LED, musique
servo.py                    Adaptation du servo de trappe
available_musics.py         Mélodies du buzzer
lib/wumons/motor.py         Pilote PWM, servo corrigé
simulation.py               Campagnes à trois repères sur la vraie Intelligence (Python PC)
tests/                      Tests unitaires du patch (Python sur PC)
docs/intelligence.md        Description détaillée des trois phases
docs/simulations.md         Résultats historiques et limites de validité
```
