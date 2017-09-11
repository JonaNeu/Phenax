.. Je l'ai compilé en pdf par la commande: rst2pdf howto.rst howto.pdf
.. role:: bash(code)
   :language: bash

GroddDroid: How-To
==================

Howto written by:

- Mourad Leslous
- Jean-Francois Lalande

Install procedure
-----------------

GroddDroid is a program that takes an APK, find suspicious parts of code, instruments it, and runs it in a runner such as *grodd* or *monkeyrunner* to allow a better dynamic analysis of that APK. For further information about GroddDroid please refer to the paper "GroddDroid: a Gorilla for Triggering Malicious Behaviors" at https://hal.inria.fr/IRISA/hal-01201743v1. Note that this how-to is written basing on an experiment performed on a Ubuntu 14.04 PC. 

Requirements:

- 32-bit libraries for 64-bit machines:

  - :bash:`sudo dpkg --add-architecture i386`
  - :bash:`sudo apt-get update`
  - :bash:`sudo apt-get install libc6:i386 libncurses5:i386 libstdc++6:i386 ia32-libs`
  
- Java 1.7: quick check with: :bash:`java -version`, if not installed just run: :bash:`sudo apt-get install default-jre` and: :bash:`sudo apt-get install openjdk-7-jdk`
- Git: can be installed with: :bash:`sudo apt-get install git`
- Apktool: manually installed from: http://ibotpeaches.github.io/Apktool/install/
- Graphviz: can be installed by: :bash:`sudo apt-get install graphviz`
- Android SDK: installed manually from: https://developer.android.com/sdk/index.html#Other
- Adroid SDK Build-tools: can be installed with the tool *android* from the Android SDK:

  - :bash:`./android list sdk --all` to list all available packages
  - :bash:`./android update sdk -u -a -t <package no.>`

The source code of GroddDroid is available on line, we clone its repository like
this: ::

  $ git clone https://scm.gforge.inria.fr/anonscm/git/kharon/kharon.git

Then we open the downloaded folder: ::

  $ cd kharon

As we can see that the project is split into several components such as:

- **BranchExplorer**: The main program, written in Python 3, it calls the other modules to perform some tasks like forcing branches and running instrumented APKs.
- **ForceCFI**: A simplified interface of the Soot framework, written in Java. It is used to instrument the APK by tagging it, forcing branches, generating DOT graphs for each method ..etc.
- **AcfgTools**: A tool written in python, used to generate the interconnected control graph of the application.
- **ManifestParser**: A small python library to extract basic information from the manifest file.

To get the whole project work we need some dependencies:

- Python 3
- pip3
- NetworkX
- PyGraphViz
- pydotplus
- UIautomator

Most of GroddDroid is written in Python 3 that can be installed along with pip3 simply by running the command: ::

  $ sudo apt-get install python3 python3-pip

Then, pip3 is used to install NetworkX, UIautomator and pydotplus that are specified in the *requirements.txt* file: ::

  $ sudo pip3 install -r requirements.txt

Nevertheless, the prepackaged PyGraphViz for Ubuntu is unstable, so we need to install it from the GitHub repository: ::

  $ sudo apt-get install graphviz libgraphviz-dev pkg-config 
  $ 				   # A required dependency to compile pygraphviz
  $ git clone https://github.com/pygraphviz/pygraphviz.git pygraphviz
  $ cd pygraphviz
  $ python3 setup.py build
  $ sudo python3 setup.py install

There are also two optional modules that enhance the visibility of the logs:

- coloredlogs, to install it run: :bash:`sudo pip3 install coloredlogs`
- progressbar2, to install it run: :bash:`sudo pip3 install progressbar2`

We return to the *malware-trigger* folder. Now we build and install the GroddDroid modules AcfgTools and ManifestParser that are needed by the main module BranchExplorer. These two modules can be installed by accessing each of there directory and running: ::

  $ cd AcfgTools
  $ python3 setup.py build         # Check that there is no error
  $ sudo python3 setup.py install  # Install module on the system
  $ cd ../ManifestParser
  $ python3 setup.py build         # Check that there is no error
  $ sudo python3 setup.py install  # Install module on the system
  $ cd ..

The next step is to update the Android SDK and to link each jar API. This can be done automatically be the provided script update-sdk-and-links.py of the AndroidPlatforms directory. The script requries to provide the path to the Android SDK and makes the hypothesis that this path does not need root priviledges: ::

  $ cd AndroidPlatforms
  $ python3 update-sdk-and-links.py --sdk <path_to_sdk>

Now we enter the main module's folder *BranchExplorer*: ::

  $ cd BranchExplorer
    
To get an idea how to run GroddDroid, we launch this command to get help: ::

  $ python3 -m branchexp.main --help

We obtain: ::

    usage: main.py [-h] [--device DEVICE] [--device-code DEVICE_CODE]
                   [--run-type RUN_TYPE] [--max-runs MAX_RUNS]
                   [--output-dir OUTPUT_DIR]
                   apk_path                                                                                                                                        
    Manager for APK instrumentation and branch-forcing.
    
    positional arguments:
      apk_path              path to the APK
    
    optional arguments:
      -h, --help            show this help message and exit
      --device DEVICE       name of the device to use
      --device-code DEVICE_CODE
                            device code to use
      --run-type RUN_TYPE   type of automatic run to do
      --max-runs MAX_RUNS   maximum limit on number of runs
      --output-dir OUTPUT_DIR
                            output directory of run_# subdirs

So we can either specify the arguments explicitly or load them from the branchexp/config.ini file (except for the APK file path): ::

    # Config file for BranchExplorer
    # 
    # Known devices:
    # 3034D685CCDD00EC (Nexus S)
    # 0640a4980acd72e1 (Nexus 5 rooted)
    # 
    # Known device codes:
    # Nexus S: soju
    # Nexus 5: hammerhead
    
    [branchexp]
    android_home = ~Android/Sdk/
    android_tools_version = 21.1.2
    device = 3034D685CCDD00EC
    device_code = crespo
    max_runs = 2
    run_type = grodd
    suspicious_db = ../../SuspiciousHeuristics/heuristics/suspicious2.json
    output_dir = /tmp/branchexp/
    twrp_backup = ~/backups/crespo.backup
    
    [tools]
    forcecfi_jar = ../../../ForceCFI/forcecfi.jar
    apktool = /usr/local/bin/apktool

As we see we can set the Android SDK home directory, the version of Android 
tools, the device serial number that can be obtained by running the command :bash:`adb devices`, and the device codename that can be obtained by running :bash:`adb -s <serialNumber> shell getprop ro.build.product`, the number of runs of the instrumented APK, the runner (you can for example set monkey instead of grodd), the input json file that contain suspected Java classes and their risk scores, the output directory where log, dot ..etc. files go and finally the system backup that will be used to restore the phone.

To do its job, BranchExplorer needs ManifestParser to extract essential information about the app. It calls also AcfgTools to make graphs of the app and its methodes. 

To launch GroddDroid, we execute for example this command: ::

  $ python3 -m branchexp.main <apk>

.. figure:: MalwareWebsite/malware-infos/WipeLocker/screenshot_locker.png
  :scale: 100 %
  :alt: WipeLocker screenshot
  :align: right
  
  A screenshot of the WipeLocker malware launched by GroddDroid

We can summarize the work of GroddDroid in the following steps:

- Load the APK file
- Extract information from the AndroidManifest.xml file
- Tag all the branches and the beginnings of methods 
- Set a score risk for methods using the suspicious2.json file
- Identify target tags to force
- Run the instrumented APK without forcing any branch
- If the number of runs equal to 1, there will be no branch forcing. So, to force any branches in the APK, the number of runs must be greater than 1. Then, each run of the instrumented APK is done by forcing all necessary branches to execute one target method.

The output directory contain for each run:

- *all_tags.log*: List of all tags
- *blare.log*: Blare log (if activated)
- *seen_tags.log*: Tags that are seen in this run
- *suspicious.log*: list of suspected methods and their risk scores
- *targets.json*: list of suspected statements and their risk scores
- *to_force.log*: list of branches to force
- The instrumented APK
- *dot* directory: contains methods CFGs

Testing GroddDroid
------------------

We have included 2 demo apps that have used for the presentation at Malcon 2015.  These two apps show the ability of GroddDroid to execute a suspicious code (sending an SMS) and to force a condition.

Of course, the first step is to be sure of the configuration of the config.ini file before launching GroddDroid.

Demo 1: triggering UI elements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Demo1 is an application constituted of 3 activities. Activity 1 (home) has two buttons that lead to Screen 2 and Screen 3. Screen 3 is an empty activity. Screen 2 contains the SMS sending code. In this activity, there are 3 radio buttons and only the second radio button enables the button that sends the SMS.

.. figure:: MalwareWebsite/resources/images/demo1-pic.png
  :scale: 100 %
  :align: center

To launch demo1, do: ::

  $ cd BranchExplorer
  $ python3 -m branchexp.main ../Demos/demo1.apk 

Demo 2: forcing a condition
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Demo 2 has only 1 activity. In the onCreate() method, the code test if the current year is greater than the installation year (for example the activity should be launched in 2016 after being installed in 2015). In this case, the SMS is sent. The demo shows that GroddDroid first fails to execute the code that sends the SMS but then rebuild the apk and force the execution to make it happen.

.. figure:: MalwareWebsite/resources/images/demo2-pic.png
  :scale: 100 %
  :align: center

To launch demo2, do: ::

  $ cd BranchExplorer
  $ python3 -m branchexp.main ../Demos/demo2.apk

:)


