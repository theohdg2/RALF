# Fonctionnement de l'intelligence

`intelligence.py` contient un prototype qui fait avancer le robot et cherche successivement deux repères de distance : le repère de départ à **20 cm**, puis celui d'arrêt à **10 cm**. La détection combine la distance ultrasonique et une baisse de luminosité. Ce module n'est pas appelé par le programme principal actuel (`code.py`).

## Paramètres actuels

Les constantes sont définies dans `settings.py` :

| Paramètre | Valeur | Utilisation |
| --- | ---: | --- |
| `START_PROPAGATION_HEIGHT` | 20 cm | Cible du premier repère |
| `END_PROPAGATION_HEIGHT` | 10 cm | Cible du second repère |
| `SECURITY_LEEWAY` | 2 cm | Largeur de la zone de détection autour de chaque cible |
| `BRIGHTNESS_DROP_DETECTION` | 30 % | Baisse relative exigée dans la zone de détection |

La baisse est calculée par rapport à la luminosité moyenne mesurée avant le repère. Une baisse de 30 % signifie que la mesure courante doit être inférieure ou égale à 70 % de cette référence.

## Déroulement du code

1. `run_intelligence()` commande d'abord le moteur à 100 %.
2. **Approche du repère de départ :** au-dessus de 22 cm, le code cumule les mesures de luminosité et calcule une moyenne. Entre 18 et 22 cm, il fige cette référence. Si la luminosité atteint le seuil de baisse, il recueille trois mesures de distance, puis utilise leur médiane. Une médiane entre 19 et 21 cm déclenche `run_start_actions()`.
3. **Secours au départ :** si la distance atteint 18 cm ou moins, `run_start_actions()` est appelée sans attendre la baisse de luminosité ni confirmer la distance par la médiane.
4. Après le déclenchement du départ, le code réinitialise la moyenne lumineuse lorsqu'il est au-dessus de 12 cm, puis la recalcule entre 12 et 18 cm.
5. **Approche du repère d'arrêt :** entre 8 et 12 cm, il fige la nouvelle moyenne. Si la luminosité baisse suffisamment, il prend trois mesures et vérifie que leur médiane est entre 9 et 11 cm. Lorsque cette condition est satisfaite, `run_end_actions()` est appelée et la boucle se termine.
6. **Secours à l'arrêt :** à 8 cm ou moins, `run_end_actions()` est appelée sans confirmation lumineuse ni médiane, puis la boucle se termine.

La médiane est la valeur centrale après tri des trois distances recueillies. Elle réduit l'influence d'une mesure isolée incorrecte. Dans les zones sensibles, la collecte s'effectue sur plusieurs passages de boucle ; une mesure suivante satisfaisant encore le seuil lumineux déclenche la vérification des trois mesures enregistrées.

## État et limites du prototype

- Les appels à `get_height(True)` et `get_brightness(True)` utilisent des nombres aléatoires de test (`utils.py`), pas les capteurs physiques. Il faut les remplacer par des lectures réelles pour une utilisation sur le robot.
- `run_start_actions()` et `run_end_actions()` affichent uniquement `TODO`. L'ouverture de la trappe et l'arrêt du moteur ne sont donc pas réalisés par ces fonctions. En particulier, la boucle se termine après le repère d'arrêt, mais le code actuel n'envoie pas de commande d'arrêt au moteur à cet endroit.
- `test_values()` retourne actuellement toujours `False`, même si ses contrôles réussissent. Le constructeur affiche donc `this is an error` à chaque instanciation.
- Les seuils sont paramétrés autour de 20 cm et 10 cm ; le commentaire historique conservé dans le fichier décrit d'autres seuils. Les constantes et conditions du code sont la référence pour le comportement actuel.

Ce module doit donc être considéré comme expérimental et non comme la séquence de fonctionnement réellement lancée par `code.py`. Le programme principal utilise actuellement une autre séquence : après l'appui sur le bouton, il avance et arrête le moteur lorsque la distance mesurée est inférieure à 10 cm.
