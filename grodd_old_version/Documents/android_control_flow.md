Android et Control-flow
=======================

On ne peut pas dresser un CFG d'une application Android comme d'un programme
Java ; le papier *Testing Android Apps Through Symbolic Execution* offre un bon
aperçu des différents type de control-flow qui ont lieu dans une application.



Les points d'entrée d'une application
-------------------------------------

Une application Android n'a pas qu'un simple main comme un programme Java qui
fait point d'entrée pour tout le reste. Techniquement, on peut démarrer une
application ou des composants d'une application tout à fait séparément.

Quels sont les points d'entrée exacts d'une application ?

* Toutes les activités sont lançables séparément
* Tous les services sont lançables séparément
* Tous les receivers sont lançable séparément

Note : ces points d'entrée sont récupérables statiquement (pour la plupart, cf
les cas particuliers des receivers).

Pour chaque point d'entrée, on a heureusement un moyen de les lancer
spécifiquement.

### Activité

Une sorte de pseudo-main est l'activité qui doit se lancer quand t'appuies sur
l'icône de l'appli :

> When the user clicks on the application icon, the android system looks in the
> manifest file for the intent with both:
> 
> * action="android.intent.action.MAIN"
> * category="android.intent.category.LAUNCHER".
> 
> * MAIN action is the main entry point of the application.
> * LAUNCHER category means it should appear in the Launcher
>   as a top-level application.

Mais ça n'empêche absolument pas de lancer l'application sur une autre activité.

Le système instancie une Activité et exécute sa méthode `onCreate()`.

``` bash
# Lancer une activité
$ adb shell am start io.shgck.app/.MainActivity
```

### Service

> Services can be started with Context.startService() and Context.bindService(). 

Le système instancie un Service et exécute sa méthode `onCreate()` *puis* sa 
méthode `onStartCommand(Intent, int, int)`.

``` bash
# Lancer un service
$ adb shell am startservice io.shgck.app/.DummyService
```

### Receiver

Le système appelle directement la méthode `onReceive` du receiver, et invalide
l'objet une fois que cette méthode a fini.

Attention : en ce qui concerne les receivers, ils peuvent être enregistrés
dynamiquement (donc pas dans le manifeste) avec `Context.registerReceiver()`.

``` bash
# Lancer un broadcaster (via un intent broadcasté)
$ adb shell am broadcast -a android.intent.action.SCREEN_ON
```

### Content provider

(Est-ce important ?)



La liaison entre les différentes méthodes
-----------------------------------------

Une fois qu'on a une liste des points d'entrée, il va falloir se demander
comment on peut aller d'une méthode à une autre. Pour ça il faut monter un
*graphe d'appel de fonction* (ou *function call graph*).

C'est assez compliqué parce qu'il y a beaucoup de façons avec lesquels les
fonctions peuvent interagir entre elles, au delà des simples appels statiquement
définis :

* Appels statiques
* Appels par réflexion
* Lancement d'activité par intent
* Lancement de service par intent
* Cycle de vie spécifique à Android (appels à onPause, onResume, etc)

Papier à propos de ce problème :

* [PScout][pscout]
* [FlowDroid][flowdroid], "Taint Analysis for Android Apps"
* Spark
* [Woodpecker][woodpecker]
* TODO compléter

### PScout

Thèse faite en 2012, programme en perl qui utilise Soot, dispo sur Github, pas
encore testé.

### Flowdroid

Par les gars de Soot, ils ont fait un gros travail pour mieux comprendre les
cycles de vie et les interactions entre composants et applications spécifiques à
Android. Plus spécifiquement :

* Le problème des points d'entrée est abordé différement : pour eux, l'Activité
  de base ne semble pas être un bon choix pour démarrer une analyse.
  Un *dummy main* émulant le cycle de vie de l'app est créé pour aider à
  modéliser toutes les transitions possibles.
* Pour représenter le comportement asynchrone et imprévisible de l'exécution
  des différents composants d'une application, FlowDroid se base sur *IFDS* qui
  permet, en gros, de ne pas avoir à traverser tous les chemins possibles.

### Spark

Inclus dans Soot ?

### Woodpecker

Le but de Woodpecker est de déterminer des problèmes dûs au système de
permissions d'Android sur des terminaux disponibles sur le marché, notamment les
fuites explicites et implicites de permissions (avec un résultat assez alarmant
de 11/13 images systèmes d'usine avec des fuites)

Ils ont identifié le problème du control-flow interrompu par les interactions du
système mais semblent parvenir à le contourner car la sémantique de ces
interactions sont en fait bien spécifiées:

> Android’s event-driven nature will unavoidably cause some discontinuity in the
> CFG construction if we only focus on analyzing the app code (Figure 2). For-
> tunately, beyond CFG construction, this intervening framework code is of no
> particular value to our analysis, and its behavior is well-defined in the
> Android framework APIs. Therefore, we leverage these well-defined semantics to
> link these two methods directly in the control flow graph, resolving the
> discontinuity in the process. We have applied this strategy to a number of
> other callbacks, such as those for message queues, timers, and GPS position
> updates.

L'exemple donné est celui de l'exécution de threads : en Java on override la
méthode `run()` d'un thread, et on demande à lancer son exécution parallèle avec
`start()` ; un CFG ordinaire ne montre pas de liaison entre ces deux méthodes,
car la liaison est faite par l'OS (en particulier, son thread scheduler).
Pourtant la liaison est bien spécifiée (un appel à `start()` résultera forcément
à un appel de `run()`, tôt ou tard), il est donc possible d'ajouter cette
liaison manuellement.

Ils travaillent sur du *smali* (avec baksmali), apparemment parce qu'ils
n'étaient pas convaincus de la qualité des convertisseurs Dalvik-to-Java
bytecode. C'était peut-être vrai à l'époque, mais avec Dare je ne vois plus de
problème.





[pscout]: http://pscout.csl.toronto.edu/
[flowdroid]: https://www.informatik.tu-darmstadt.de/fileadmin/user_upload/Group_EC-Spride/Publikationen/flowdroid_pldi.pdf
[woodpecker]: http://www4.ncsu.edu/~zwang15/files/NDSS12_Woodpecker.pdf
