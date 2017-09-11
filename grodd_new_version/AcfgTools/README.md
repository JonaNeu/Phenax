ACFG Tools
==========

Génération et parcours de control flow graphs d'application.



Génération d'ACFG
-----------------

La génération de graphe est faite par le package *acfg_tools.builder*. On peut
générer un graphe DOT comprenant tous les control-flow graphs d'une application
avec un code couleur et une indication concernant le risque de malveillance
estimé pour chaque instruction.

Pour l'utiliser, il faut une liste de graphes DOT (générés par ma version
modifiée de Soot, via ForceCFI) et le manifeste de l'application en XML lisible.

``` bash
# Dans le répertoire cfg_analyser
python3 main.py <répertoire_dot> <manifeste>
```

Les instructions sont des nœuds carrés et les nœuds sphériques sont des
informations annexes, comme la signature de la fonction. Les signatures vertes
représentent des points d'entrée de la plateforme Android, avec un vert plus
foncé pour le point d'entrée centrale (activité démarrée lorsque l'utilisateur
ouvre l'application). Un indicateur de risque (RS) non nul est affiché à la fin
de la signature des méthodes.

Les nœuds oranges représentent des instructions qui ont été ciblées comme étant
suspectes.

**Attention**: pour avoir les attributs nécessaires sur les nœuds à la création
de ces graphes, il faut utiliser ma version modifiée de Soot, qui a un
générateur de DotGraph amélioré.



Parcours et recherche de chemin d'exécution
-------------------------------------------

La recherche de chemin d'exécution est faite par le package
*acfg_tools.exec_path_finder*.

Il y a potentiellement beaucoup de choses à améliorer ici ! La recherche est
très basique, pas forcément stable, etc.
