Harvester
=========



Idée et principes
-----------------

Le dernier projet de l'équipe de Soot (Steven Arzt, Eric Bodden, etc). C'est un
technical report pour le moment mais ça reste un papier important pour nous
parce qu'ils ont quasiment la même idée que nous, en plus poussé et en déjà
implémenté...

L'idée est d'utiliser Soot pour modifier des applications afin de ne conserver
que les parties qui intéressent un analyste, en supprimant le reste du code. On
peut désigner des instructions précises au préalable, et lorsque l'application
réduite est exécutée, les valeurs concrètes sont relevées pour l'analyste. Ça
permet de contourner les techniques d'obfuscation et de résoudre le problème de
la réflexion.



Automatisation
--------------

Un énorme avantage de Harvester est sa capacité à modifier une application pour
que le code ciblé soit automatiquement exécuté : il n'y a pas besoin de simuler
des événements sur l'interface car un faux point d'entrée s'occupe d'appeler les
bonnes méthodes. Le control-flow est modifié de façon à ce que le code ciblé
soit accédé automatiquement.

L'idée principale est similaire à notre idée de départ : forcer les branches qui
nécessitent d'être parcourues en remplaçant les conditions par des booléens
initialisés avec les valeurs souhaitées. Dans certains cas, cela peut poser
problème car changer le control-flow peut modifier la valeur qu'on cherche à
obtenir (passage dans une certaine boucle, un certain bloc, etc).

Les choix pris pour la modification sont très justes : si on a placé 4 booléens
dans une slice vers une valeur, on va tester les 2^4 = 16 combinaisons
différentes et rapporter la valeur trouvée à chaque fois. Pour éviter de se
faire coincer par des booléens qu'on ne devrait pas changer et ainsi trop
modifier la sémantique du programme, les conditions dépendantes d'une façon ou
d'une autre de la valeur recherchée ne sont pas modifiées.

``` java
int x = 1;
while (true) {
  if (x >= 10)       // dépend de x : pas de forcing
    break;

  if (a) {           // <- if (EXECUTOR_1)
    x = x * 2;
  }
  else if (b) {      // <- else if (EXECUTOR_2)
    x = x + 3;
    if (x % 2 == 0)  // dépend de x : pas de forcing
      x = x * 2;
  }
  else {
    x = 42;
  }
}
send(x);
```

Comme nous, ils ont besoin d'un call graph de l'application pour trouver le bon
control-flow menant à tel ou tel bloc de code, et ils utilisent Spark, le
générateur de call graph de Soot, qui n'est pas parfait mais fait l'affaire dans
le cadre de ce projet.

En ce qui concerne l'exécution, il faut qu'un environnement régulier soit
fournit à l'application : respect du lifecycle d'Android, initialisation des
activités nécessaires au code ciblé, etc.

> If the code was originally executed after the user clicks on a button, it may
> expect the hosting activity to be initialized. HARVESTER must thus emulate
> this activity’s lifecycle at runtime. Naive calls to lifecycle methods,
> however, can cause problems, as the Android operating system expects certain
> internal variables such as the used Context to be set which cannot be achieved
> through the normal interface. HARVESTER therefore uses reflection to inject
> these initialization values.

Il y a également une gestion des crashs lors de l'utilisation de certains points
d'entrée, en ajoutant la capture d'exception qui ne serait sinon pas capturée
(et donc remontant jusqu'à l'OS, qui couperait l'appli).



Résultats
---------

Le bilan est très positif, ils arrivent à obtenir les valeurs qu'ils ciblent au
préalable avec un faible taux d'échec de *23 fails sur 1817 valeurs cherchées*
(soit 99% de réussite). Le processus de slicing et d'exécution est suffisamment
rapide pour être utilisé à la chaîne, entre 25 et 45 secondes par sample.

La présentation du dataset de test est un peu floue, ils ont apparemment
utiliser des datasets différents pour leurs différents tests : 150 samples de 18
familles du Genome Project pour le test qualitatif, plusieurs milliers de
plusieurs sources pour le test d'efficacité.

Il y a plein d'infos intéressantes sur les pratiques des malwares dans la partie
V-Q4.

Ils ont aussi fait des tests pour voir si des outils de l'état de l'art comme
FlowDroid et TaintDroid sont plus efficaces avec les versions slicées des
malwares, et le résultat est très positif aussi, ce qui plutôt une bonne
nouvelle pour nous.

Le projet n'a pas l'air disponible encore (28/04/2015) mais vu les résultats
qu'ils montrent je pense qu'ils ne sont plus très loin de la release.
