# OS2datascanner - Admin module

## To install everything for frontend assets building:

`$ npm install`

## To run webpack for frontend asset bundling and watching on development:

`$ npm run dev`

This will bundle JS files in the `static/src/js/` folder to `static/dist/bundle.js` and CSS/CSSS/SASS (please use only SCSS) files from the `static/src/css/` folder to `static/dist/bundle.css`

## To run webpack for frontend asset bundling on production:

`$ npm run prod`

This will bundle JS files in the `static/src/js/` folder to `static/dist/bundle.min.js` and CSS/CSSS/SASS (please use only SCSS) files from the `static/src/css/` folder to `static/dist/bundle.min.css`
