# Datascanner frontend architecture


## Applications

Presently, Datascanner's main web GUIs are the **admin** and **report**
modules. The source code for both resides in
[src/os2datascanner/projects](./src/os2datascanner/projects).


## HTML markup

Markup is mostly generated using [Django
templates.](https://docs.djangoproject.com/en/3.2/topics/templates/)


## CSS styling

The [README.md](./src/os2datascanner/projects/report/reportapp/README.md)
states "please use only SCSS".  An effort has been made to establish SASS as
the guiding workflow for CSS builds but it is mixed with other approaches.
Amongst others:

* CSS built from SASS and prefixed/minified with PostCSS (`bundle.css` via
  Webpack)
* CSS imported directly or from 3rd parties
* Use of CSS custom properties (CSS vars) in stead of SASS variables


## Javascript

Some JS is packaged into `bundle.js`/`bundle.min.js` via
[Webpack.](https://webpack.js.org/) Other scripts, like
[jQuery](https://jquery.com/), are just added via script tags.

Admin app uses jQuery-3.6.0, whereas Report app uses jQuery-3.5.0.

Admin app also includes [Bootstrap](https://getbootstrap.com/) Javascript but
without the accompanying bootstrap.css

* **Package management**
  [npm](https://www.npmjs.com/)
* **Old browser support**
  There are two approaches for supporting older browsers:
    * [Using Babel](https://babeljs.io/)
    * Using IE conditional comments in `<head>`


## Fonts

Admin and Report app use the "Inter" font.


## Icons

There are several icon styles and frameworks in use:

* [Google Material Icons](https://fonts.google.com/icons) Admin app links from
  base.html: https://fonts.googleapis.com/icon?family=Material+Icons Report app
  refers to local font files in `_vars.scss`.
* Admin app has [Glyphicons](https://www.glyphicons.com/sets/halflings/).
  These could be related to a Bootstrap implementation.
* Both Report and Admin apps hide a set of SVG icon files in
  `/templates/components/svg-icons/` folder.
* A small set of SVG icon files are available in [report
  app](src/os2datascanner/projects/admin/adminapp/static/src/images/) and
  [admin app](src/os2datascanner/projects/admin/adminapp/static/src/svg/)
  static folders. (/static/src/svg)


## Build & package management

[Webpack](https://webpack.js.org/) is used for building frontend assets.


## Admin app specifics

Note: Admin app has no apparant organization of static files.

* **Django template files**
    - src/os2datascanner/projects/admin/adminapp/templates
* **Templates that load JS/CSS/etc**
    - src/os2datascanner/projects/admin/adminapp/templates/partials/base.html
* **Position of `package.json` and conf files:**
    - src/os2datascanner/projects/admin/adminapp/package.json
    - src/os2datascanner/projects/admin/adminapp/postcss.config.js
    - src/os2datascanner/projects/admin/adminapp/webpack.dev.js
    - src/os2datascanner/projects/admin/adminapp/webpack.prod.js
* **Postion of JS & (S)CSS source files**
    - src/os2datascanner/projects/admin/adminapp/static/src/
* **Style files loaded in browser**
    - bundle.css - built from SASS files in src
* **Javascript files loaded in browser**
    - bootstrap.js
    - jquery-3.6.0.min.js
    - jquery.modal.min.js
    - main.js
    - svgxuse.js - for IE svg features


### Admin app module file relations

* **Bundle.js**
    - templates/os2datascanner/scanners.html and
    - templates/os2datascanner/rules.html and
    - templates/os2datascanner/scanner_askrun.html and
    - templates/designguide.html depend on 
    - static/dist/bundle.js - must be built first


## Report app specifics

* **Django template files**
    - src/os2datascanner/projects/report/reportapp/templates
* **Templates that load JS/CSS/etc**
    - src/os2datascanner/projects/report/reportapp/templates/partials/header.html
* **Position of `package.json` and conf files:**
    - src/os2datascanner/projects/report/reportapp/package.json
    - src/os2datascanner/projects/report/reportapp/postcss.config.js
    - src/os2datascanner/projects/report/reportapp/webpack.dev.js
    - src/os2datascanner/projects/report/reportapp/webpack.prod.js
    - src/os2datascanner/projects/report/reportapp/.browserslistrc **Only exists in reportapp!**
* **Postion of JS & (S)CSS source files**
    - src/os2datascanner/projects/report/reportapp/static/src/
* **Style files loaded in browser**
    - bundle.css - built from SASS files in src
* **Javascript files loaded in browser**
    - bundle.js - built from JS files in src
    - jQuery-3.5.0.js
    - clipboard.js


### Report app module file relations

* **Statistics**
    - templates/statistics.html depends on
    - static/3rdparty/chart-2.9.4.min.js and
    - static/3rdparty/chartjs-plugin-datalabels.js


----------------------


# TODOS for a simpler frontend architecture

Decisions to make:

* IE11-support by Babel/bundling vs. IE11 by old school coding (no bundling)?
* JS bundling vs decentralised JS (see above)?

One hybrid approach includes both bundling and decentralized code:

1. Decide on what is core JS/CSS. Bundle only that.
   Embed it on every page (base|index.html).
   Adding eventlisteners to certain elements is probably not core.
2. Load component-specific JS/CSS from their specific templates.
   Use script/styling/extra_head blocks.
   Most eventlisteners go here.
3. Put component-specific JS/CSS/SCSS with related templates (if possible)
4. Decide on what icon system to use. Use only that.
