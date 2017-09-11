Acteve
======

(Automated concolic testing of smartphone app)

Test concolic, je vois l'idée mais j'ai du mal à voir concrètement ce que ça
fait au final... Concrètement, 11k loc, ça utilise Soot, ya de la grosse formule
qui tâche.

Le framework Acteve est composé de 4 éléments : l'instrumenter (qui utilise
Soot), le runner, le concolic testing engine, et le subsumption analyzer.



Implémentation
--------------

### Instrumenter

L'instrumenter prend l'Android SDK en entrée avec une application (sous forme de
bytecode, .class) et rend une version instrumentée des deux ("Instr(SDK+App)").

Les instrumentations opérées sont :

* Préparer la concolic execution, en ajoutant une meta-variable qui gère les
  valeurs symboliques de chaque variable, et *avant chaque assignment*, un autre
  assignment qui assignent la métavar de la r-value à celle de la l-value.
* Gère le logging des séquences d'événements produites en réponse à un test
  précis.

### Runner

Se charge d'exécuter l'appli instrumentée avec un ému dont le SDK est également
instrumenté.

À la première run, il génère un test aléatoire, puis il prend des tests créés
par le CTE ou le subsumption analyzer. Il output des *tests inputs* (?) et pour
chaque test, un *path constraint* + *write set*.

### Concolic Testing Engine

Input : *path constraints*. Output : *new tests for current iteration*. Génère
de nouveaux tests, vérifie leur satisfiabilité, et crée ces nouveaux tests avec
un solveur de contraintes (ici, Z3).

### Subsumption analyzer

Input : *write set* = set of fields of Java classes that are written when App
responds to the last event in the event sequence corresponding to a specific
test. Output (optional) : *seed test for next iteration*.



Résultats
---------

Ça a l'air de marcher correctement niveau couverture, mais ça prend **plusieurs
heures** par application. Par exemple, 6.7h avec les constraint checks (2.7h
sans) sur RMP, une appli de lecture de musique.



Évaluation perso
----------------

Warning: aucune doc... je crois qu'il faut télécharger et build un Android SDK
mais je me lance pas là-dedans sans doc de survie.
