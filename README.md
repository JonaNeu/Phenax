# Phenax

Phenax is an open source framework to test Android applications whether they are
malicious or not. Using a tool called GroddDroid and machine learning algorithms
this framework repeatedly runs a number of goodware and malware applications
forcing a different execution path in each application in each run.

The idea behind this is to repeatedly force different parts within an application
until the malicious behavior is triggered. This tool especially focuses on finding
repackaged malware applications.

This framework was developed as part of my bachelors thesis. You can find the whole thesis [here](https://github.com/JonaNeu/Phenax/blob/master/Repackaged%20Malware%20Detection%20in%20Android.pdf).

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.


### Installing

The installation of GroddDroid is described on http://kharon.gforge.inria.fr/grodddroid.html. Other than that no special installations are required.


## Built With

* [GroddDroid](http://kharon.gforge.inria.fr/grodddroid.html) - The framework used to find and trigger malicious parts within an Android application

## Contributing

If you want to contribute you can simply create a pull request.
