# Datascanner frontend architecture

## Applications
Presently, Datascanner's main web GUIs are the **admin** and **report** modules.
The source code for both resides in [src/os2datascanner/projects](./src/os2datascanner/projects)

## HTML markup
Markup is mostly generated using [Django templates.](https://docs.djangoproject.com/en/3.2/topics/templates/) 

## CSS styling
The [README.md](./src/os2datascanner/projects/report/reportapp/README.md) states "please use only SCSS".
An effort has been made to establish SASS as the guiding workflow for CSS builds but it is mixed with other approaches. Amongst others:
* CSS built from SASS and prefixed/minified with PostCSS (`bundle.css` via Webpack)
* CSS imported directly or from 3rd parties
* Use of CSS custom properties (CSS vars) in stead of SASS variables

## Javascript
Some JS is packaged into `bundle.js`/`bundle.min.js` via Webpaack.
Other scripts, like [jQuery](https://jquery.com/), are just added via script tags.

* **Package management**
  [npm](https://www.npmjs.com/)
* **Old browser support**
  * There are two approaches for supporting older browsers
    [Babel](https://babeljs.io/)
  * IE conditional comments in `<head>`


## Fonts


## Icons
There are several icon styles and frameworks in play



## Build & package management
[Webpack](https://webpack.js.org/) is used for building frontend assets.

## Admin app specifics

* **Django template files**
  src/os2datascanner/projects/admin/adminapp/templates
* **Templates that load JS/CSS/etc**
  src/os2datascanner/projects/admin/adminapp/templates/partials/base.html
* **Position of `package.json` and conf files:**
  src/os2datascanner/projects/admin/adminapp/package.json
  src/os2datascanner/projects/admin/adminapp/postcss.config.js
  src/os2datascanner/projects/admin/adminapp/webpack.dev.js
  src/os2datascanner/projects/admin/adminapp/webpack.prod.js
* **Postion of JS & (S)CSS source files**
  src/os2datascanner/projects/admin/adminapp/static/src/
* **Style files loaded in browser**
  bundle.css - built from SASS files in src
* **Javascript files loaded in browser**
  bundle.js - built from JS files in src

## Report app specifics

* **Django template files**
  src/os2datascanner/projects/report/reportapp/templates
* **Templates that load JS/CSS/etc**
  src/os2datascanner/projects/report/reportapp/templates/partials/header.html
* **Position of `package.json` and conf files:**
  src/os2datascanner/projects/report/reportapp/package.json
  src/os2datascanner/projects/report/reportapp/postcss.config.js
  src/os2datascanner/projects/report/reportapp/webpack.dev.js
  src/os2datascanner/projects/report/reportapp/webpack.prod.js
  src/os2datascanner/projects/report/reportapp/.browserslistrc **Only exists in reportapp!**
* **Postion of JS & (S)CSS source files**
  src/os2datascanner/projects/report/reportapp/static/src/
* **Style files loaded in browser**
  bundle.css - built from SASS files in src
* **Javascript files loaded in browser**
  bundle.js - built from JS files in src
  jQuery-3.5.0.js
  clipboard.js

### Report app module file relations
* **Statistics**
  templates/statistics.html depends on
  static/3rdparty/chart-2.9.4.min.js and
  static/3rdparty/chartjs-plugin-datalabels.js


