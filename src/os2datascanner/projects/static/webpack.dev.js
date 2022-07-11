const config = require('./webpack.base');

config.mode = 'development';
config.watch = true;
config.watchOptions = {
  aggregateTimeout: 300,
  ignored: ['node_modules']
};

module.exports = config;
