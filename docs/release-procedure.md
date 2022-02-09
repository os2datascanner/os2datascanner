## Release a new version of os2datascanner

#### First make sure to update the version variable and our changelog:
* `git checkout main`
* `git pull`
* `git checkout -b release/%VERSION%`
* Bump version in (`os2datascanner/src/os2datascanner/__init__.py`)
* Update `CHANGELOG.md`

#### Run translations and check migrations
* Run django-admin command for translations
  * `docker-compose run <report|admin> django-admin makemessages --all`
* Ensure migrations are up-to-date (checked by pipeline as well)
* Commit changes
* `git push -u origin release/%VERSION%`
* Create merge request and fill in the git template


#### Once the MR has been approved and merged, push a new tag:

* `git checkout main`
* `git pull`
* `git tag %VERSION%  # e.g. "3.11.2" or "3.11.2-rc"`
* `git push --tags`

#### Close existing GitLab milestone and create a new one.
These are found in the top "Menu" in the GitLab UI and are Group Milestone's.
They are named according to release version.
Start day is usually day of closing the previous and end day 14 days ahead.


#### Create a Release in GitLab
In the left-hand side of GitLab, click Releases and create a new one.

* Provide tag
* Release title from release notes
* Set Milestone
* Paste release notes into Release notes


### Finally
Please make sure all Redmine issues that are included in the release
have their status set to closed.
