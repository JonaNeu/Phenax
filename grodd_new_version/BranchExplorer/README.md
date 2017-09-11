BranchExplorer
==============

BranchExplorer est un (relativement gros) programme Python qui prend en entrée
un APK et essaye de détecter du code malveillant inclus, puis tente de
l'exécuter automatiquement, possiblement en modifiant son flot de contrôle.

Les détails sur son fonctionnement son dans le papier GroddDroid ou dans mon
mémoire de stage (Adrien A.).



Installation
------------

La plupart des dépendances de BranchExplorer sont sur PyPI et peuvent donc être
installées avec pip. Attention en utilisant pip à bien utiliser la version pour
Python 3 : en installant le paquet *python3-pip* (sur Debian et sûrement sur
Ubuntu), une version pour Python 3 sera installée, pip3.

À noter que BranchExplorer essaye de détecter la présence ou non des dépendances
dans le module *imports.py*.

### Dépendances

* Python 3
* Le [SDK Android](https://developer.android.com/sdk/index.html#Other)
* NetworkX : `sudo pip3 install networkx`
* UIautomator : `sudo pip3 install uiautomator`
* APKtool : `sudo install apktool`
* PyGraphViz : see below
* AcfgTools : see below
* ManifestParser : see below

En ce qui concerne PyGraphViz, le port Python 3 est assez instable (l'export DOT
ne semble pas marcher). Il faut installer la dernière version depuis
[son repo Github](https://github.com/pygraphviz/pygraphviz).

``` bash
$ git clone https://github.com/pygraphviz/pygraphviz.git pygraphviz
$ cd pygraphviz
$ python3 setup.py build
$ sudo python3 setup.py install
```

AcfgTools et ManifestParser quant à eux sont disponibles dans le repo avec
BranchExplorer. La procédure d'installation pour chacun d'entre eux est :

``` bash
$ python3 setup.py build         # Vérifier qu'il n'y a pas d'erreur
$ sudo python3 setup.py install  # Installer les modules pour le système
```

### Dépendances optionnelles mais conseillées

* coloredlogs : `sudo pip3 install coloredlogs`
* progressbar2 (pour AcfgTools) : `sudo pip3 install progressbar2`

### Variables à ajouter au PATH

Le module *config* se charge d'ajuster le PATH pour ajouter les dossiers
contenant entre autres *adb*, *fastboot* et *aapt*. S'il y a un problème de
programme non trouvé par un subprocess, il faut voir si le PATH a bien été mis à
jour, ou alors ajouter manuellement les bons dossiers.

### Update and install all android.jar files of the Android SDK build tools

``` bash
$ cd ForceCFI/res/android-platforms$ 
$ python update-sdk-and-links.py
```

Configuration
-------------

Le fichier de configuration de BranchExplorer est *config.ini*.

Les chemins du fichier de configuration peuvent être relatif par rapport à ce
fichier ou absolus.

* branchexp
    * android_home : répertoire du SDK Android à utiliser
    * android_tools_version : version des build tools à utiliser
    * device : identifiant du téléphone à utiliser (ex : 3434D686CCDD00EF)
    * device_code : nom de l'image système du téléphone (ex : crespo)
    * max_runs : nombre maximal d'exécution à faire
    * run_type : un type de run (cf *branchexp/runners/infos.py*)
    * suspicious_db : fichier JSON contenant les données de
        l'heuristique de ciblage
    * output_dir : répertoire de travail
    * twrp_backup : répertoire où se situe les images TWRP des téléphones. Si l'image du téléphone utilisé lors de l'analyse est présent dans ce répertoire alors le téléphone sera flashé à la fin de chaque run. Les images sont disponibles via la page gforge du projet.
* tools
    * forcecfi_jar : chemin vers le JAR de ForceCFI
    * apktool : chemin vers le script de lancement d'Apktool


Images TWRP
-----------
TWRP est un recovery alternatif d'Android permettant de sauvegarder ou restaurer le contenu d'un téléphone. Les images pour le Nexus S (crespo) et le Nexus 5 (hammerhead) sont présentes sous forme d'archive tar.gz sur la forge Inria. Afin de flasher automatiquement les téléphones à la fin d'une analyse, il faut extraire le contenu de ces archives dans le répertoire défini par le paramètre twrp_backup (Voir Configuration).
<repertoire_defini_dans_twrp_backup>/
  -> hammerhead.backup
  -> crespo.backup


Usage
-----

``` bash
# Dans le dossier BranchExplorer
$ python3 -m branchexp.main <apk> [<options> ...]
$ python3 -m branchexp.main --help  # pour avoir une liste d'options
```

Les options passées en paramètres sont prioritaires par rapport aux options du
fichier de configuration.
