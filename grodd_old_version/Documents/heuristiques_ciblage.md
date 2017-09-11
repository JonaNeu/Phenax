Heuristiques pour le ciblage de code malveillant
================================================

Idées sur comment cibler le code des malwares. Je vais avoir besoin de plus de
stats sur les malwares qu'on a, si possible en demandant à Nicolas.

Il y a quelques heuristiques de ce genre dans Androguard (voir dans la source du
côté de `androguard/core/analysis/analysis.py`)



Appels JNI
----------

Utilisé par DroidKungFu2 ; le code natif est à peu près identique dans son
comportement à celui qui était en Java dans DroidKungFu1. Le but de la migration
vers la JNI est que plein de méthodes se pètent les dents sur la JNI.



Exécution de binaires
---------------------

* `Runtime.exec()`



Exécution de code dynamique
---------------------------

Quel malware utilise ça ?

En tout cas des grosses biblios utilisent ça, genre Adobe AIR...

* Utilisation de `DexClassLoader`



Réflexion
---------

Pour des raisons évidentes : ça évite toutes les détections basées sur des noms
de fonctions / API précises.

``` java
// Sans utiliser la reflexion
Foo foo = new Foo();
foo.hello();
 
// En utilisant la reflexion
Class<?> cl = Class.forName("package.name.Foo");
Object instance = cl.newInstance();
Method method = cl.getClass().getDeclaredMethod("hello", new Class<?>[0]);
method.invoke(instance);
```

* `Class`, `getClass()`
* `Object`, `newInstance()`
* `Method`, `getDeclaredMethod()`



Chiffrement
-----------

Utilisation de méthodes de chiffrement pour cacher des communications et/ou
déchiffrer des binaires planqués dans les ressources.

* `javax.crypto`
* Modules propres (cf SimpLocker)



Intents suspects
----------------

Du code qui est exécuté à la réception d'Intent particuliers, étrange vis-à-vis
de l'application.

* `BOOT_COMPLETED`
* `BATTERY_CHANGED_STATE` (je crois que c'est ça)
