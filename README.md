# RALF

RALF est un robot mobile piloté par un contrôleur compatible CircuitPython et une carte WuKong 2040. Le programme utilise un capteur ultrasonique pour détecter une balise, un capteur de luminosité, un moteur à courant continu et une trappe motorisée.

## Fonctionnement

Le fichier `code.py` est le point d'entrée exécuté automatiquement par CircuitPython :

1. Au démarrage, le programme place la trappe à 0°, initialise le capteur ultrasonique et règle le moteur à l'arrêt.
2. Le robot indique qu'il est prêt par ses LED vertes, puis attend le bouton de démarrage. En attente, les LED clignotent en bleu et la luminosité mesurée est affichée sur la console série.
3. Après un appui, la trappe passe à 90° et le moteur avance à pleine vitesse.
4. Le robot s'arrête lorsque le capteur mesure une distance inférieure à 10 cm.

`intelligence.py` contient un prototype de détection en deux étapes, combinant distance et variation de luminosité. Il n'est pas appelé par le programme principal actuel. Voir la [documentation détaillée de l'intelligence](docs/intelligence.md) pour son fonctionnement, ses seuils et les points à terminer avant de l'utiliser.

## Matériel et connexions

Les broches ci-dessous sont celles définies dans `settings.py` et `lib/wumons/__init__.py`.

| Élément | Broche(s) |
| --- | --- |
| Moteur CC | GP10, GP11 |
| Servo de la trappe | GP6 |
| Bouton de démarrage analogique | GP28 |
| Capteur de luminosité analogique | GP26 |
| Capteur ultrasonique DFRobot URM09 (I²C) | GP17 (SCL), GP16 (SDA), adresse `0x11` |
| LED NeoPixel (2 LED) | GP22 |
| Buzzer / lecteur musical | GP9 |

Vérifiez le brochage de votre contrôleur et l'alimentation des composants avant la mise sous tension. Le capteur URM09 doit être accessible sur le bus I²C pour que la séquence de démarrage et la détection de distance fonctionnent correctement.

## Installation et lancement

1. Flashez sur le contrôleur une version de **CircuitPython** compatible avec la carte et ses broches `GP`.
2. Connectez le contrôleur à l'ordinateur et ouvrez son volume `CIRCUITPY`.
3. Copiez à la racine du volume les fichiers Python du projet (`code.py`, `settings.py`, `utils.py`, `servo.py`, `available_musics.py`, `intelligence.py`) ainsi que le dossier `lib/`.
4. Redémarrez le contrôleur ou enregistrez `code.py`. CircuitPython lance ce fichier automatiquement. Les messages de diagnostic sont visibles via la console série.

Les bibliothèques Python utilisées par le projet sont en partie fournies dans `lib/`. Ajoutez également dans `lib/` les paquets `adafruit_bus_device` et `adafruit_pixelbuf` de la bibliothèque Adafruit CircuitPython correspondant à votre firmware : ils sont importés par les pilotes du projet, mais ne sont pas inclus dans ce dépôt. Les modules matériels tels que `board`, `analogio`, `pwmio`, `busio` et `neopixel_write` doivent être disponibles dans le firmware CircuitPython installé.

## Réglages

Les paramètres matériels et les seuils principaux se trouvent dans `settings.py` :

- `START_PROPAGATION_HEIGHT` et `END_PROPAGATION_HEIGHT` définissent les distances de référence de la logique expérimentale.
- `SECURITY_LEEWAY` et `BRIGHTNESS_DROP_DETECTION` règlent ses marges de sécurité et son seuil de variation de luminosité.
- Les constantes `*_GP` indiquent les broches ; `NEOPIXEL_BRIGHTNESS` règle la luminosité des LED.
- `TRAPDOOR_PULSE_RANGE` est défini dans `servo.py` et peut être adapté au servo utilisé.

Les fonctions de pilotage et de lecture des capteurs sont regroupées dans `utils.py`. Toute modification des broches ou des angles doit être vérifiée sur le montage réel avant utilisation.

## Structure du projet

```text
code.py             Point d'entrée et séquence principale
settings.py         Broches, composants et paramètres
utils.py            Fonctions de pilotage et accès aux capteurs
servo.py            Configuration du servo
available_musics.py Mélodies prédéfinies
intelligence.py     Logique expérimentale distance/luminosité
lib/                Bibliothèques embarquées et pilotes
```
