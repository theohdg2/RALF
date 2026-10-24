# R.A.L.F.

R.A.L.F. est un robot mobile de largage piloté par une carte WuKong 2040 exécutant CircuitPython. Le projet commande un moteur à courant continu, une trappe à servo, un capteur ultrasonique, un capteur analogique de luminosité, un bouton, des NeoPixels et un buzzer.

## Fonctionnement actuel

`code.py` est le point d'entrée exécuté automatiquement par CircuitPython.

1. Le programme place la trappe à 0°, initialise le capteur ultrasonique et règle le moteur à l'arrêt.
2. Si l'initialisation est considérée réussie, les LED passent au vert. Le programme attend le bouton analogique en affichant la luminosité sur la console série et en laissant les LED bleues.
3. À l'appui sur le bouton, la trappe passe à 90° et le moteur avance à 100 %.
4. Le moteur s'arrête lorsque la distance mesurée est comprise entre 0 cm inclus et 10 cm exclu. Le programme revient ensuite à l'attente d'un nouvel appui.

La séquence réellement exécutée est dans `code.py` et `utils.py`. `intelligence.py` contient un prototype distinct de détection par distance et luminosité ; il n'est pas appelé par `code.py` et ne commande pas la trappe au déclenchement START. Voir [la documentation de l'intelligence](docs/intelligence.md). Le simulateur et ses résultats sont décrits dans [la documentation des simulations](docs/simulations.md).

> [!CAUTION]
> Dans la séquence principale, un retour `False` de l'initialisation du capteur ultrasonique n'est pas vérifié. Une mesure négative n'arrête pas le moteur ; si le capteur n'est pas initialisé, `None` peut provoquer une erreur dans la comparaison de distance. Vérifiez le capteur avant un essai physique et ajoutez une stratégie d'arrêt en cas de lecture invalide ou de délai dépassé.

## Matériel et connexions

| Élément | Broche(s) |
| --- | --- |
| Moteur CC | GP10, GP11 |
| Servo de la trappe | GP6 |
| Bouton de démarrage analogique | GP28 |
| Capteur de luminosité analogique | GP26 |
| Capteur ultrasonique DFRobot URM09 (I²C) | GP17 (SCL), GP16 (SDA), adresse `0x11` |
| NeoPixels (2 LED) | GP22 |
| Buzzer | GP9 |

Vérifiez le brochage, l'alimentation et la fixation mécanique avant toute mise sous tension. Le capteur URM09 doit être accessible sur le bus I²C.

## Installation sur la carte

1. Flashez une version de **CircuitPython** compatible avec la WuKong 2040.
2. Connectez la carte et ouvrez le volume `CIRCUITPY`.
3. Copiez à la racine les fichiers de programme (`code.py`, `settings.py`, `utils.py`, `servo.py`, `available_musics.py` et, si nécessaire, `intelligence.py`), ainsi que `settings.toml` si vous souhaitez définir des réglages CircuitPython personnalisés.
4. Copiez le dossier `lib/` et ses bibliothèques sur la carte. Ajoutez également les paquets Adafruit `adafruit_bus_device` et `adafruit_pixelbuf` correspondant à votre firmware : ils ne sont pas inclus dans ce dépôt, mais sont importés par les pilotes.
5. Redémarrez la carte ou enregistrez `code.py`. Les diagnostics sont disponibles sur la console série.

Ce projet dépend de modules matériels fournis par CircuitPython (`board`, `analogio`, `pwmio`, `busio`, `digitalio`, `supervisor`, entre autres). Il ne se lance donc pas tel quel avec le Python classique de Windows/macOS/Linux : les essais sur ordinateur nécessitent une simulation et des adaptations des imports propres au firmware.

## Réglages

`settings.py` récupère les seuils avec `supervisor.get_setting()` ; les valeurs par défaut figurent dans ce fichier et les valeurs personnalisées peuvent être placées dans `settings.toml`. Les réglages utilisés par le prototype `intelligence.py` comprennent notamment :

| Paramètre | Valeur par défaut | Rôle |
| --- | ---: | --- |
| `START_PROPAGATION_HEIGHT` | 20 cm | Cible de détection START |
| `END_PROPAGATION_HEIGHT` | 10 cm | Cible de détection END |
| `SECURITY_LEEWAY` | 1 cm | Déclenchement ultrasonique de secours sous la cible |
| `BRIGHTNESS_DROP_DETECTION` | 30 % | Baisse lumineuse relative exigée |
| `DISTANCE_SAMPLES` | 3 | Mesures utilisées pour la médiane |
| `MAX_INVALID_READINGS` | 8 | Mesures invalides consécutives avant arrêt du prototype |

Les broches et objets matériels sont créés dans `settings.py`. Les seuils du prototype ne modifient pas la séquence principale de `code.py`.

## Fichiers principaux

```text
code.py              Point d'entrée et séquence principale du robot
settings.py          Configuration et création des composants matériels
settings.toml        Valeurs de configuration personnalisées (facultatif)
utils.py             Commandes moteur, capteurs, LED et initialisation I²C
servo.py             Adaptation du servo et de sa plage d'impulsions
available_musics.py  Séquences musicales prédéfinies
intelligence.py      Prototype expérimental de détection START/END
simulation.py        Simulation logicielle de l'intelligence
docs/
  intelligence.md    Fonctionnement et limites du prototype
  simulations.md     Modèle et résultats des simulations
lib/                 Bibliothèques et pilotes CircuitPython
```
