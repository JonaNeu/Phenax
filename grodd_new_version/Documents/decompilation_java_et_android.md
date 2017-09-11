Décompilation Java et Android
=============================

Il y a pas mal de projets de décompilateurs, je vais essayer de faire un résumé.

Critères à noter :

* *Java / Dalvik* : vise Java et/ou Android
* *Qualité code* : qualité du code décompilé
* *Gestion fautes* : comment les fautes à la décompil sont gérées
* *Défauts* : défauts généraux du programme
* *Site* : site ou repo du projet



Déjà, la compilation
--------------------

Avant de regarder comment reverse un APK, un résumé de la procédure de création
de l'APK et tout ce qui se passe ensuite.

### Création d'un APK

Pour monter une application Android, il faut suivre les étapes suivantes :

1. Création d'un programme Java qui utilise des objets Android, avec un
   manifeste, des ressources, etc.
2. Le code Java (.java) est compilé vers du bytecode Java (.class)
   par un compilateur Java (probablement *javac*)
3. S'il y a du code natif (C/C++) dans l'application, il est compilé par le NDK
   en un binaire pour les architectures choisies.
4. Le bytecode Java est converti par l'outil *dx* en bytecode Dalvik, puis
   packagé dans le fichier *classes.dex*.
5. C'est à ce moment (je suppose) qu'est généré le fichier des ressources et que
   les diverses meta-données sont converties ; par exemple le manifeste est
   converti de texte clair à du XML binaire Android.
6. Le tout est ajouté à une archive ZIP (d'extension .apk), qui est signée avec
   *jarsigner* puis optimisée avec *zipalign*.

À ce stade, on a un APK ready to ship.

### Post-traitements à l'installation

L'APK subit des post-traitements lors de l'installation sur un terminal, et
c'est intéressant de savoir ce qui se passe à ce moment.

Avec Android 5.0, la machine virtuelle Dalvik est sensée disparaître des
terminaux. Le bytecode Dalvik contenu dans les APK devra être converti en code
natif.

**Avant Android 5.0**, le bytecode Dalvik était utilisé par la VM Dalvik
(logique), à part qu'il était optimisé par *dexopt*, qui créait un .odex
depuis le .dex.

**Après Android 5.0**, le bytecode est converti en code natif par *dex2oat*
vers un ELF classique.

Wikipédia a [un ptit schéma sympa](img/ART_view.png) pour expliquer ça.

Ça va faire foirer une bonne partie des systèmes de détection d'intrusion qui
étaient basé sur des modifications / analyse de la JVM, mais a priori les APK
seront toujours ship avec du bytecode Dalvik donc les analyses sur ce bytecode
seront toujours valides (et donc j'écris pas cet article pour rien).



Tous les projets
----------------

### dex2jar / jar2dex

Suite d'outil pour convertir des archives DEX en archive JAR (donc bytecode
Dalvik et bytecode Java). *Ça ne fait pas décompilateur Java*.

Pas très maintenu, pas très propre.

[Repo](https://code.google.com/p/dex2jar/) (google code).

### JD-Gui

Fait pour le Java. La qualité du code obtenu est pas terrible, on se retrouve
avec des bouts de code comme le suivant :

``` java
while (true)
{
  return 1;
  startUpdater();
  continue;
  startUpdater();
}
```

Les méthodes dont la décompil a échouée sont écrites en bytecode en commentaire
(donc on peut pas toujours recompiler après).

C'est pas (ou difficilement) utilisable en black-box ligne de commande parce que
la lib interne de décompilation n'est pas publique ; il faut obligatoirement
passer par la GUI.

![trashed.jpg](img/trashed.jpg)

[Site](http://jd.benow.ca/).

### Apktool

C'est un outil fait pour aider au reverse engineering des APKs tels que trouvés
dans la nature. C'est toujours activement développé.

**Apktool ne permet pas de décompiler le bytecode Dalvik vers du Java** ; en
revanche il propose une version en [Smali][smali] du code de l'application.

Dans les faits, c'est pas si robuste que ça : le dézippage des APK est fait avec
la lib standard de Java, qui a tendance à planter dès que le fichier ne lui
plaît pas trop (faut que je retrouve le sample qui me faisait ça).

Un des avantages d'Apktool est qu'il peut décoder les ressources spécifiques à
Android, alors que la plupart des autres outils se contentent de reverse le code
source d'une application. Ça veut dire qu'il permet de retrouver les fichiers
multimédia, le manifeste (et les autres XML binaires), etc. D'ailleurs c'est le
seul outil (à part JEB qui est payant) qui permet de récupérer le manifeste à ce
que je sache.

Un autre avantage est qu'il propose de *reconstruire* un APK qu'il a déconstruit
de façon assez automatique :

``` bash
# On reverse le contenu de foo.apk dans le dossier "foo"
$ apktool d foo.apk

# Après avoir modifié ce qu'on souhaitait, on reconstruit l'APK
$ apktool b foo -o new_foo.apk
```

[Site et repo](https://ibotpeaches.github.io/Apktool/).

[smali]: https://code.google.com/p/smali/

### Bytecode Viewer (BCV)

Un décompilateur Java, qui affiche une compatibilité pour Android mais en fait
ils se basent sur les algos de *dex2jar*. Se présente comme un outil de
décompilation "à la JEB".

La qualité du code décompilé a l'air correcte. En fait il se base sur d'autres
décompilateurs, donc en ce qui nous concerne (analyse plus automatisée que
manuelle), l'apport de BCV par rapport à ces décompilateurs est assez faible.

Non utilisable en ligne de commande (?) et pèse 371 Mo...

[Site](https://bytecodeviewer.com/)
et [repo](https://github.com/Konloch/bytecode-viewer).

### CFR

Un décompilateur Java assez moderne, qui supporte Java 8, minimaliste et en
ligne de commande. Les résultats obtenus avec ont l'air satisfaisant, et il est
d'ailleurs utilisé comme décompilateur de base de BCV.

*CFR semble être le meilleur décompilateur Java à disposition*, mais ça veut
dire qu'il faut faire la conversion du bytecode Dalvik au bytecode Java à côté.

[Site](http://www.benf.org/other/cfr/index.html).

### Procyon

Fait par un collègue du gars derrière CFR, qui a l'air aujourd'hui de plutôt
encourager l'utilisation de CFR, donc je me suis pas plus penché que ça dessus.

[Repo](https://bitbucket.org/mstrobel/procyon/).

### JEB

JEB, alias the Interactive Android Decompiler (blague avec le nom d'IDA, en
rot1), est un outil commercial spécialisé dans le reverse Android.

Il est fait pour **travailler directement sur le bytecode Dalvik**, et se charge
de la décompilation directement en Java, donc c'est théoriquement beaucoup plus
propre et solide que les approches classiques de transformer le Dalvik en
bytecode Java, puis à décompiler le bytecode Java (typiquement, l'approche
*dex2jar* + *jd-gui*).

Il y a l'air d'avoir une emphase particulière sur l'analyse de malwares :

> The good thing about JEB is that the Dalvik disassembler and the Java
> decompiler is written from scratch and designed from top to bottom to be able
> to analyse malware (including anti-decompilation tricks in Dalvik bytecode
> level)

Ça fournit toutes les fonctionnalités d'un gros assistant au reverse comme le
fait IDA pour les binaires x86 : renommage de variables, commentaires dans le
code, gestion de plusieurs vues (bytecode, Java), décompilation Java qui a l'air
propre, export en Smali, etc.

Malheureusement une licence perso coûte 1k$ (avec 30% réduc pour l'académie).

[Site](https://www.pnfsoftware.com/).

### ded & Dare

ded et Dare sont deux projets de la même équipe : ce sont des décompilateurs
Dalvik vers bytecode Java. Dare est la suite du projet ded et doit donc être
utilisé aujourd'hui, et il n'y a aucune raison pour continuer à utiliser ded.

Dare présente des performances excellentes dans [son papier][dare], avec un
décompilation sans problème de plus de 99.99% des classes trouvées dans les apps
libres du Google Play. Après test sur quelques malwares, ça s'installe et
s'exécute sans problème.

[dare]: http://siis.cse.psu.edu/dare/papers/octeau-fse12.pdf

### DAD

DAD (DAD is A Decompiler) est le décompilateur intégré à Androguard. Il y a peu
d'infos dessus, à part qu'il est sensé être rapide :

> DAD is the default decompiler (python) of Androguard (include in the project),
> so you have nothing to do for the installation, and DAD is very fast due to
> the fact that it is a native decompiler, and the decompilation is done on the
> fly for each class/method.

En l'absence de plus d'infos, je vais voir ailleurs.

### JAD

Java only.

D'après les comparatifs sur le site de JEB, il a tendance à mettre des goto
partout, ce qui fait carrément crade dans du Java.

Ça a l'air d'avoir eu un certain succès, mais c'est tellement pas maintenu qu'il
n'y a plus de site officiel, juste des miroirs vers des vieux binaires, donc ça
ira merci. Trashed.

[Miroirs](http://varaneckas.com/jad/)

### JadX

Projet intéressant qui s'occupe de reverse tout ce qui se trouve dans un APK :
ressources et bytecode (directement vers des sources Java). 

Le code décompilé est propre, mais il se pète les deux sur certaines apps,
probablement à cause techniques d'obfuscation : par ex, dans le sample
*ru.blogspot.playsib.savageknife.apk* (8c2f25178e80f8edfb0ade73075eb681),
la méthode `com.google.ads.util.c.c.a`.

[Repo](https://github.com/skylot/jadx).



Projets annexes
---------------

Il y a d'autres outils intéressants mais pas spécialement dédié à la
décompilation, comme Androguard.

### Androguard

Framework dédié au reverse engineering d'application Android, un peu à la
manière d'*Apktool*.

Androguard est composé de plusieurs outils en command-line, et certains peuvent
être utiliser par un shell interactif. Une liste des plus intéressants :

* Androaxml : décode les XML binaires
* Androapkinfo : affiche des infos comme celles du manifeste, avec des
  indicateurs en plus comme l'utilisation de la réflection, de code natif, etc.
* Androdd : crée des CFG pour chaque méthode, au format DOT ou PNG
* Androgexf : crée un callgraph (minimal) de l'application, au format GEXF.
  Il faut utiliser *Gephi* pour ouvrir ces graphes.
* Androrisk : donne un score de risque en fonction de certains critères :
  code natif, code dynamique, crypto, réflection, permissions louches, etc.
* Androsim : donne un score de similarité entre deux applications ;
  ça permet de trouver des applications repackagées facilement
* Androxgmml : crée un graphe XGMML qui est sensé représenter
  Il faut utiliser *Cytoscape* pour ouvrir ces graphes.
* Apkviewer : no description?

L'outil n'est pas très stable : pendant mes tests, AndroXGMML et ApkViewer ont
planté sur des APKs tout bête.

Il peut utiliser 3 décompilateurs : DAD, ded et JAD (en passant par dex2jar).
DAD est le décompilo de base d'Androguard, en Python.

Androguard peut créer des CFG de méthodes et en faire des visu assez sympa : on
peut avoir un graphe DOT classique mais aussi une vue IDA-like du bytecode (plus
d'infos sur leur [wiki][androguard-visu]).

Androguard peut également créer des *call-graphs* entre les fonctions, ce qui
est déjà assez avancé.

[androguard-visu]: https://code.google.com/p/androguard/wiki/Visualization



Meilleures combinaisons
-----------------------

Pour obtenir des sources Java dans le meilleur état et de la façon la plus
fiable, la meilleure combinaison d'outil semble être **Dare + CFR** pour les
sources, et **Apktool** pour les ressources.

```
Reverse des sources :
  Dare(bytecode_davlik) -> bytecode_java
  CFR(bytecode_java) -> source Java

Reverse des ressources :
  Apktool (ou Androguard)
```



Re-compilation
--------------

Une fois qu'on a du code / des ressources reversés, comment on peut reconstituer
un APK à partir de là ?


