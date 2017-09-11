Concolic Testing
================

> Concolic testing is a hybrid software verification technique that performs
> symbolic execution, a classical technique that treats program variables as
> symbolic variables, along a concrete execution (testing on particular inputs)
> path.

Utilisation de symbolic execution et d'un theorem prover :

> Symbolic execution is used in conjunction with an automated theorem prover or
> constraint solver based on constraint logic programming to generate new
> concrete inputs (test cases) with the aim of maximizing code coverage. Its
> main focus is finding bugs in real-world software, rather than demonstrating
> program correctness.

Il y a une équipe de l'Université de Georgie qui fait des travaux qui ont l'air
bien, et dispos ; c'est l'équipe avec Mayur Naik, Saswat Anand, etc. Les papiers
intéressants :

* 2012: *Automated concolic testing of smartphone app*, premier jet sur le test
  auto sur Android. Le code est dans un repo nommé [Acteve][acteve].
  [Review ici](review_ActeveAutoConcolicTesting.md).
* 2013: *Dynodroid*, version plus avancée (?),
  page de présentation [ici][dynodroid], code [là][dynodroid-repo].
  [Review ici](review_Dynodroid.md).

En ce qui concerne nos usages, l'apport de ces outils est intéressant, surtout
d'un point de vue théorique, mais pas suffisamment avantageux par rapport à un
vulgaire Monkey.





[acteve]: https://code.google.com/p/acteve/
[dynodroid]: http://pag.gatech.edu/dynodroid.html
[dynodroid-repo]: https://code.google.com/p/dyno-droid/
