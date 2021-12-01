# Datascanner frontend architecture


## Applications

Presently, Datascanner's main web GUIs are the **admin** and **report**
modules. The source code for both resides in
[src/os2datascanner/projects](./src/os2datascanner/projects).


## HTML markup

Markup is mostly generated using [Django
templates.](https://docs.djangoproject.com/en/3.2/topics/templates/)


## Shared static resources

The static resources are located in
[src/os2datascanner/projects/static](./src/os2datascanner/projects/static). Django is configured to look in this path (actually on the corresponding `dist` path in the Docker container) when it collects static resources.
This allows both apps to use the same set of static resources without
having to maintain duplicate copies. Static resources are bundled up via
Webpack and output in a `dist` subfolder; consult
[src/os2datascanner/projects/static/webpack.base.js](./src/os2datascanner/projects/static/webpack.base.js)
for the configuration. Note that since the JS code isn't really modularized,
most of what Webpack does is statically copy over the folders `js`&dagger;, `3rdparty`, `admin`, `css`, `favicons`, `fonts`, `recurrence` and `svg` with `CopyWebpackPlugin`. &dagger; The exception to the JS files is the file `index.js` which serves as the Webpack entry point. Finally, the `scss` folder is also not copied over, as its contents need to be transpiled into CSS first. This is achieved by importing `master.scss` into `index.js` and then using `sass-loader` for Webpack to handle that import statement.


## CSS styling

An effort has been made to establish SASS as the guiding workflow for CSS builds
but it is mixed with other approaches.
Amongst others:

* CSS built from SASS and bundled up via Webpack (via plugins)
* CSS imported directly or from 3rd parties

## JavaScript

A minimal set of JS is bundled as described in "Shared static resources" above. Other scripts are just added via script tags in the Django templates.

Admin app also includes [Bootstrap](https://getbootstrap.com/) Javascript but
without the accompanying bootstrap.css

* **Package management**
  [npm](https://www.npmjs.com/). At the time of writing, NPM packages are exclusively used for the bundling setup (you'll only see `devDependencies` in `package.json`, no `dependencies`). JS code imports no modules.
* **Old browser support**
  Babel is currently neither installed nor configured. IE support is achieved via conditional comments in `<head>`.


## Fonts

Admin and Report app use the "Inter" font.


## Icons

There are several icon styles and frameworks in use:

* [Google Material Icons](https://fonts.google.com/icons) is self-hosted—see [src/os2datascanner/projects/static/fonts/materialicons](src/os2datascanner/projects/static/fonts/materialicons) and the accompanying CSS file.
* Admin app has [Glyphicons](https://www.glyphicons.com/sets/halflings/).
  These are most likely a leftover from the webscanner incarnation of the project. They may still be in use, however.
* Both Report and Admin apps hide a set of SVG icon files in their respective
  `templates/components/svg-icons/` folders.
* A small set of SVG icon files are available in the shared static files in `src/os2datascanner/projects/static/svg`


## Build & package management

[Webpack](https://webpack.js.org/) is used for building frontend assets.


## Admin app specifics

* **Django template files**
    - src/os2datascanner/projects/admin/adminapp/templates
* **Templates that load JS**
    - src/os2datascanner/projects/admin/adminapp/templates/components/user.html
    - src/os2datascanner/projects/admin/adminapp/templates/os2datascanner/regexrule_form.html
    - src/os2datascanner/projects/admin/adminapp/templates/os2datascanner/rules.html
    - src/os2datascanner/projects/admin/adminapp/templates/os2datascanner/scanner_askrun.html
    - src/os2datascanner/projects/admin/adminapp/templates/os2datascanner/scanner_form.html
    - src/os2datascanner/projects/admin/adminapp/templates/os2datascanner/scanner_run.html
    - src/os2datascanner/projects/admin/adminapp/templates/os2datascanner/scanners.html
    - src/os2datascanner/projects/admin/adminapp/templates/partials/base.html
* **Templates that load CSS**
    - src/os2datascanner/projects/admin/adminapp/templates/os2datascanner/scanner_form.html
    - src/os2datascanner/projects/admin/adminapp/templates/partials/base.html


## Report app specifics

* **Django template files**
    - src/os2datascanner/projects/report/reportapp/templates
* **Templates that load JS**
    - src/os2datascanner/projects/report/reportapp/templates/components/user.html
    - src/os2datascanner/projects/report/reportapp/templates/partials/header.html
    - src/os2datascanner/projects/report/reportapp/templates/partials/scripts.html
    - src/os2datascanner/projects/report/reportapp/templates/statistics.html
* **Templates that load CSS**
    - src/os2datascanner/projects/report/reportapp/templates/partials/header.html


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
