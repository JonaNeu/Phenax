Repository Android Malware
==========================

Je vais essayer de tenir à jour une description de ce dossier pour éclairer les
futurs pèlerins arrivant dans l'équipe. Si possible, il faudrait un README dans
chaque répertoire pour expliquer le minimum sur un programme, comme son
utilisation, ses dépendances, et un mail d'appel au secours ;)

Le repo contient plusieurs submodules de Git, pour ne pas l'encombrer avec des
sources gérées par d'autres repos. Pour récupérer le code de ces sous-dossiers :

``` bash
$ git submodule init
$ git submodule update
```

À noter que le repo s'est pris beaucoup de fichiers binaires dans la tronche, et
donc l'index pèse plus d'1 Go... Il sera peut être sage un jour de faire un
nouveau repo avec uniquement les sources et les documents texte, et de
télécharger les binaires (JAR, APK, etc) depuis BigFour ou un autre serveur FTP.



Programmes et outils
--------------------

### BranchExplorer

Programme s'occupant de manipuler un APK pour exécuter des portions de code
précises. Le principe est de tagger un APK, regarder les branches parcourues, en
forcer certaines autres, relancer, etc. Des statistiques sont produites à chaque
fois.

Il est basé sur plusieurs autres programmes du repo (ForceCFI, les runners,
etc), donc il faut s'assurer d'avoir un environnement avec toutes ses
dépendances avant de le lancer. Cette procédure est détaillée dans son readme.

### ForceCFI

Outil Java basé sur Soot permettant de manipuler les APK pour les différents
besoins qu'on a, à savoir :

* Tagger les APK avec des logs à chaque branche / méthode
* Forcer des branches selon une liste de tags
* Générer des control flow graphs de chaque méthode au format DOT
* etc... plus d'infos dans le README du rep

ForceCFI doit être considéré comme un programme indépendant qui permet
d'interfacer nos programmes avec Soot, quelqu'en soit les langages.

### AcfgTools

Outils d'exploration de graphes basés sur NetworkX pour générer un ACFG (cf
master d'Adrien A.) et trouver des chemins d'exécutions.

### ManifestParser

Petite lib Python (3, compatible 2) pour récupérer des informations basiques
depuis un manifeste d'application. Le manifeste doit être au format XML texte
(donc décodé par Androguard ou Apktool).



Documents / Site web
--------------------

### Documents

Juste un ensemble de documents texte / PDF / ce que vous voulez qui est
important, qui pourrait être ajouter à un papier, etc.

### MalwareWebsite

Base de données pour le projet Kharon, contenant des infos précises sur des
malwares finement analysés par notre équipe d'experts ! Contient aussi le
générateur de site web en Python.

### SuspiciousHeuristics

Contient les fichiers JSON des descriptions de classes suspectes d'Android et
Java.



Ressources et autres trucs
--------------------------

### AndroidPlatforms

Liste de JAR Android pour chaque version du SDK. Ces JAR permettent à Soot
d'utiliser la version la plus adaptée de l'API Android pour l'analyse de
n'importe quelle application.

### LogParser

J'ai mis logparser en tant que sousmodule git. 
Afin de vous assurer que le script python logconverter.py soit bien appelé, 
veuillez lancer au moins une fois 
    $ git submodule update
Cette commande est censée récupérer le contenu du repo git de logparser.

Update: c'est toujours un sous-module, mais je l'ai déplacé à la racine du repo.
D'ailleurs il est toujours sur Google Code, faudra penser à le déplacer sur
Github ou ailleurs.

### MiniApp

Appli Android minimale : 2 activités, 1 bouton permettant d'aller de la première
à la deuxième, un service lançable avec un BroadcastReceiver. Sert à juste à
faire des tests avec une appli la plus simple possible.

Si je la laisse dans le repo c'est pour qu'elle puisse être modifiée par
n'importe qui pour faire ses tests, donc n'hésitez pas à faire des branches
dessus.

### Soot

C'est une version modifiée de Soot. L'*origin* de ce repo est vers mon compte
Github, mais libre à vous de le déplacer ailleurs. Les changements apportés sont
principalement situés dans le package `soot.util.cfg`, pour ajouter des
informations aux générateur de CFG (CFGToDotGraph, un truc comme ça).

Il est possible de mettre à jour facilement ce Soot en récupérant les
modifications depuis le repo officiel. Il faut faire une branche nommée par
exemple *upstream*, puis pull les modifications de la branche *develop*.
