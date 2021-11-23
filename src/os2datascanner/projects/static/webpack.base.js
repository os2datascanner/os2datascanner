// Webpack uses this to work with directories
const path = require('path');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CopyWebpackPlugin = require('copy-webpack-plugin');

// This is main configuration object.
// Here you write different options and tell Webpack what to do
module.exports = {

  // Path to your entry point. From this file Webpack will begin his work
  // entry: './static/src/js/index.js',
  entry: {
    app: [
      './js/index.js'
    ]
  },

  // Path and filename of your result bundle.
  // Webpack will bundle all JavaScript into this file
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'js/index.js'
  },

  // Default mode for Webpack is production.
  // Depending on mode Webpack will apply different things
  // on final bundle. For now we don't need production's JavaScript
  // minifying and other thing so let's set mode to development
  mode: 'production',

  module: {
    rules: [
      {
        test: /\.js$/,
        /* ... */
      },
      {
        // Apply rule for .sass, .scss or .css files
        test: /\.(sa|sc|c)ss$/,

        // Set loaders to transform files.
        // Loaders are applying from right to left(!)
        // The first loader will be applied after others
        use: [
          {
            // After all CSS loaders we use plugin to do his work.
            // It gets all transformed CSS and extracts it into separate
            // single bundled file
            loader: MiniCssExtractPlugin.loader
          },
          {
            // This loader is necessary to prevent webpack from choking
            // on @import and url() inside (S)CSS files.
            loader: "css-loader",
            options: {
              // don't resolve @import and url() as we will be statically copying over the resources they point to
              import: false,
              url: false
            }
          },
          {
            // First we transform SASS to standard CSS
            loader: "sass-loader",
            options: {
              implementation: require("sass")
            }
          }
        ]
      }
    ]
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: "css/master.css"
    }),
    // Statically copy over the assets we don't want to process
    new CopyWebpackPlugin({
      patterns: [
        {
          from: 'js/**/*', // specify this as a glob pattern since the folder will get created by Webpack, leading to conflict if we just specify the entire folder here
          to: '[path][name][ext]',
          noErrorOnMissing: true,
          globOptions: {
            ignore: [
              'js/index.js' // don't copy index.js since it's our entry point for webpack
            ]
          }
        },
        {
          from: '3rdparty',
          to: '3rdparty',
          noErrorOnMissing: true // prevent build from failing if this input folder happens to be empty
        },
        {
          from: 'admin',
          to: 'admin',
          noErrorOnMissing: true
        },
        {
          from: 'css/**/*', // specify this as a glob pattern since the folder will get created by Webpack in MiniCssExtractPlugin, leading to conflict if we just specify the entire folder here
          to: 'css/[path][name][ext]',
          noErrorOnMissing: true
        },
        {
          from: 'favicons',
          to: 'favicons',
          noErrorOnMissing: true
        },
        {
          from: 'fonts',
          to: 'fonts',
          noErrorOnMissing: true
        },
        {
          from: 'recurrence',
          to: 'recurrence',
          noErrorOnMissing: true
        },
        {
          from: 'svg',
          to: 'svg',
          noErrorOnMissing: true
        }
      ]
    })
  ]
};
