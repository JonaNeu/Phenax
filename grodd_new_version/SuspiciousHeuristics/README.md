Heuristiques de détection de code suspicieux
============================================

Dans le dossier *heuristics* se trouve des fichiers de descriptions de patterns.

Les descriptions de patterns sont des fichiers JSON décrivant différentes
caractéristiques à identifier dans un bout de code.

Ces descriptions ont premièrement servi à ajouter des informations visuelles et
sémantiques aux control-flow graphs d'une application, mais elles fournissent un
moyen général d'identifier des patterns. Ces patterns sont recherchées dans un
code qui peut être d'un format peu régulier, comme un graphe, un programme
Smali, etc, l'important c'est de comprendre que ces patterns sont juste des
idées qui peuvent être utilisées par n'importe quel script pour chercher ce
qu'il veut où il veut.

Bien qu'on puisse décrire un peu n'importe quoi avec ces patterns, celles qui
nous intéressent présentement sont des patterns dîtes suspicieuses, c'est à dire
correspondant généralement (mais pas forcément) à un comportement malveillant.

Un fichier de description est au format JSON. Il contient une liste de
dictionnaire, un par pattern, comportant les clés suivantes :

* *category*: nom de la pattern
* *description*: description de la pattern
* *classes*: liste de classes à chercher (sensible à la casse)
* *grep*: liste de pattern à grepper dans le code (non sensible à la casse)
* *score*: nombre

La liste de noms de classes sert à chercher par exemple dans la liste des objets
initialisés à chaque instruction si un objet de tel type a été déclaré. On peut
spécifier toutes les classes d'un package avec un wildcard
(e.g. "javax.crypto.*").

La liste des patterns à grepper va juste servir à chercher parmi chaque
instruction telle ou telle chaîne de caractère (pour l'instant, sans expression
régulière), il faut donc mettre des éléments assez précis pour éviter d'avoir
trop de faux matchs. Évidemment, si l'application est obfusquée, les patterns
type "encrypt" ne vont probablement pas donner grand chose.

Le score est purement indicatif mais peut être utilisé par d'autres programmes.



TODO

Ajouter des listes d'exceptions aux patterns ? (pas des exceptions au sens
Java). Par exemple des cas communs qui utilisent la réflexion, pour éviter des
faux positifs. Un exemple typique est la création d'intent qui prend un objet de
type Class. Soit ça soit virer cette classe.
