ForceCFI
========

La front-end maison de Soot pour manipuler des APKs et les modifier pour leur
faire faire ce qu'on veut.

Pour l'instant, ForceCFI peut servir à :

* Tagger les APK avec des logs à chaque branche / méthode
* Forcer des branches selon une liste de tags
* Générer des control-flow graphs de chaque méthode au format DOT
* Identifier des blocs de codes suspects à partir d'un JSON
  (cf dossier SuspiciousHeuristics)

Attention : la version de Soot (lib/soot.jar) utilisée a été modifiée pour
pouvoir générer des graphes avec plus d'attributs, le fork est dispo sur
[ce repo](https://github.com/Shgck/soot).



Installation
------------

Il suffit de créer un fichier JAR exécutable avec les dépendances intégrées.

ForceCFI et Soot utilisent Java 7. La classe SignerAligner nécessite d'avoir
*jarsigner* et *zipalign* dans le PATH. Dans la plupart des installations Java,
*jarsigner* est déjà dans le PATH, mais *zipalign* doit être ajouté
manuellement.



Utilisation
-----------

La commande minimale qui ne fait rien :

```
$ java -jar forcecfi.jar   -inputApk <apk>   -outputDir <dir>
```

Options :

```
  -addTags                      # ajoute des tags aux méthodes et aux branches
  -branches <fichier_branches>  # donner une liste de tag à de branches à forcer
  -dotOutputDir <dir>           # générer des CFGs
  -heuristics <bdd.json>        # appliquer des heuristiques de ciblage de code
```

Fichiers en sortie :

* *.{adb,jarsigner,zipalign}_log* : logs de ce que ces outils ont affiché
* *all_tags.log* : liste de tous les tags ajoutés à l'APK (méthodes et cond)
* *targets.json* : JSON regroupant toutes les méthodes ciblées
* *suspicious.log* : informations similaires à *targets.json* mais plus lisible



Signature des APKs
------------------

Pour installer l'appli modifiée il faut qu'elle soit signée et alignée. J'ai
ajouté une classe *SignerAligner* qui se charge de le faire avec le keystore
contenu dans *res/*, mais on peut le faire manuellement.

```
$ jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 \
    -keystore ~/.android/debug.keystore \
    -storepass android -keypass android \
    app.apk \
    androiddebugkey
$ zipalign 4 app.apk app-aligned.apk
```

J'ai aussi fait [un script](https://gitlab.com/Shgck/sign-align-dummy) qui fait
tout "sans keystore" depuis un seul fichier.
