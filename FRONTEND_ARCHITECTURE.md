# Datascanner frontend architecture

## Applications
Presently, Datascanner's main web GUIs are the **admin** and **report** modules.
The source code for both resides in [src/os2datascanner/projects](./src/os2datascanner/projects)

## HTML markup
Markup is mostly generated using [Django templates.](https://docs.djangoproject.com/en/3.2/topics/templates/) 

## CSS styling
The [README.md](./src/os2datascanner/projects/report/reportapp/README.md) states "please use only SCSS".
An effort has been made to establish SASS as the guiding workflow for CSS builds but it is mixed with other approaches. Amongst others:
* CSS built from SASS and prefixed/minified with PostCSS (Webpack)
* CSS imported directly or from 3rd parties

## Javascript


## Fonts


## Icons


## Build & package management
[Webpack](https://webpack.js.org/) is used for building frontend assets.

## Admin app specifics

* Django template files
  src/os2datascanner/projects/admin/adminapp/templates
* Templates that load JS/CSS/etc
  src/os2datascanner/projects/admin/adminapp/templates/partials/base.html
* Position of `package.json` and conf files:
  src/os2datascanner/projects/admin/adminapp/package.json
  src/os2datascanner/projects/admin/adminapp/postcss.config.js
  src/os2datascanner/projects/admin/adminapp/webpack.dev.js
  src/os2datascanner/projects/admin/adminapp/webpack.prod.js
* Postion of JS & (S)CSS source files
  src/os2datascanner/projects/admin/adminapp/static/src/
  

## Report app specifics

* Django template files
  src/os2datascanner/projects/report/reportapp/templates
* Templates that load JS/CSS/etc
  src/os2datascanner/projects/report/reportapp/templates/partials/header.html
* Position of `package.json` and conf files:
  src/os2datascanner/projects/report/reportapp/package.json
  src/os2datascanner/projects/report/reportapp/postcss.config.js
  src/os2datascanner/projects/report/reportapp/webpack.dev.js
  src/os2datascanner/projects/report/reportapp/webpack.prod.js
  src/os2datascanner/projects/report/reportapp/.browserslistrc **Only exists in reportapp!**
* Postion of JS & (S)CSS source files
  src/os2datascanner/projects/report/reportapp/static/src/


