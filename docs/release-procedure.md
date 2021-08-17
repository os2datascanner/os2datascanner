Proceduren var oprindeligt nedskrevet i #42725. OS2datascanner release
procedure:

* `git checkout development`
* `git pull`
* `git checkout -b release/%VERSION%`
* Bump VERSION (`os2datascanner/src/os2datascanner/__init__.py`) and update NEWS
* `git push release/%VERSION%`
* Opret merge request og udfyld git template.
* Når merge request er godkendt og flettet til development fast-forward master.
* Opret nyt tag på gitlab - https://git.magenta.dk/os2datascanner/os2datascanner/-/tags/new
* Push nyeste release og ændringer til Github
    - git remote set-url origin https://github.com/os2datascanner/os2datascanner.git
    - git push origin master
    - git push origin VERSION
* Kør build på readthedocs: https://readthedocs.org/projects/os2datascanner/builds
* Tjek at docs er opdateret https://os2datascanner.readthedocs.io/en/latest/news.html (husk at cleare cache)
* Sæt redmine sager som er med i release til status closed.
