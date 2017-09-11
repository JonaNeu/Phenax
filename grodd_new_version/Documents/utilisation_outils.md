BytecodeViewer
==============

Une application qui permet de reverse du Bytecode. 
Il prend en entrée des `APK`, du `Dex`, des `.class` ou des `Jar` et affiche le tout en code Java lisible avec l'arborescence des packages.
Il peut aussi afficher le code Smali ou le Bytecode directement.
On a le choix entre 5 décompilateurs : CFR, Procyon, FernFlower, Krakatau et le décompilateur de JD-GUI. On peut changer à tout moment.
Il est possible d'afficher côte à côte plusieurs fenêtres, pour par exemple afficher le code Java et le code Smali en même temps.
BytecodeViewer supporte l'ajout de plugins écrits en Groovy, Python et Ruby.
(On peut par exemple imaginer un plugin qui dans l'arborescence surligne en couleur les classes potentiellement malveillantes)

[Site](http://bytecodeviewer.com/)

##### Utilisation

Pour l'utiliser il suffit juste de lancer le .jar avec `java -jar` ou de double-cliquer sur le fichier.
On accède ensuite à l'interface graphique et on lui donne le fichier d'entrée. (File/Add..)



Dex2Jar
=======

Description : voir `decompilation_java_et_android.md`

##### Utilisation

* Transformer un fichier .dex en archive Jar :

	`sh ~/dex2jar-0.0.9.15/dex2jar.sh ~/classes.dex -o ~/archive.jar`

* Transformer une archive Jar en fichier .dex :

	`sh ~/dex2jar-0.0.9.15/d2j-jar2dex.sh ~/archive.jar -o ~/out.dex`


JD-Gui
======

Description : voir `decompilation_java_et_android.md`

##### Utilisation

Pour l'utiliser il suffit juste de lancer le .jar avec `java -jar`.
On accède ensuite à l'interface graphique et on lui donne le fichier d'entrée. (File/Open File...)


Jad
===

Description : voir `decompilation_java_et_android.md`

##### Utilisation

* Décompiler un fichier .class :

	`~/jad158e.linux.intel/jad -sjava example1.class`

* Décompiler tous les fichiers .class de l'arborescence :

	`~/jad158e.linux.intel/jad -r -sjava -d src_directory ./**/*.class`


Apktool
=======

Description : voir `decompilation_java_et_android.md`

##### Utilisation

On suppose que l'installation a été faite et donc que le fichier 'apktool' se trouve dans '/usr/local/bin/'

* Dépackager un apk (avec Manifest lisible) :

	`apktool d malware-sample.apk`

* Repackager un apk :

	`apktool b malware-sample/ -o out.apk`



Androguard
==========

Description : voir `decompilation_java_et_android.md`

##### Utilisation

* Obtenir une analyse intéréssante de l'apk (permissions douteuses, utilisation de code natif, de code dynamique, de réflexion, ...) :

	`python ~/Androguard/androapkinfo.py -i ~/malware-sample.apk > ~/analyse.txt`

* Obtenir l'indicateur de risque de l'application :

	`python ~/Androguard/androrisk.py -i ~/malware-sample.apk`

* Obtenir le manifest en XML lisible à partir de l'apk :

	`python ~/Androguard/androaxml.py -i ~/malware-sample.apk > ~/out.xml`

* Convertir un XML binaire en XML lisible :

	`python ~/Androguard/androaxml.py -i ~/AndroidManifest.xml > ~/out.xml`




aapt
====

[Lien](https://developer.android.com/sdk/index.html)



Droidbox
========

DroidBox est un outil permettant l’analyse dynamique d’applications Android dans un émulateur.
Durant l’exécution de l’application, l’outil enregistre les communications réseaux effectuées par l’application, 
les accès aux fichiers, les services lancés, les classes chargées, les opérations cryptographiques via l’API Android,
les SMS et les appels émis.
DroidBox est assez limité, il se contente de lancer l’application en exécutant son Activity principal, ne cherchant aucun autre point d'entrée.
C'est ensuite à l'utilisateur d'utiliser l'application dans l'émulateur (pas toujours pratique).
Les captures qu'il fait ne sont pas toujours très bonnes, par exemple certaines requêtes envoyées à des serveurs ne sont pas complètes,
la chaine est coupée avant la fin. De plus les données capturées sont toutes en hexa, c'est à l'utilisateur de les convertir en ASCII si besoin.

[Lien](https://code.google.com/p/droidbox/)

##### Utilisation

* Lancer l'émulateur :

	`sh ~/DroidBox_4.1.1/startemu.sh <nom-virtual-device>`

* Lancer l'application :

	`sh ~/DroidBox_4.1.1/droidbox.sh ~/absolute-path/malware.apk`

* Le résultat de l'analyse sera affiché dans le terminal au format JSON.

