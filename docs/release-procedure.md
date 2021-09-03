To release a new version of os2datascanner, first make sure to update the
version variable and our changelog:

* `git checkout main`
* `git pull`
* `git checkout -b release/%VERSION%`
* Bump version in (`os2datascanner/src/os2datascanner/__init__.py`)
* Update `CHANGELOG.md`
* Commit changes
* `git push -u origin release/%VERSION%`
* Create merge request and fill in the git template


Once the MR has been approved and merged, push a new tag:

* `git checkout main`
* `git pull`
* `git tag %VERSION%  # e.g. "3.11.2" or "3.11.2-rc"`
* `git push --tags`


Finally, please make sure all Redmine issues that are included in the release
have their status set to closed.
