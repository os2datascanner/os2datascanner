// It is handy to not have those transformations while we developing
// TODO: Make this work in production environments
if (process.env.NODE_ENV === 'development') {
  module.exports = {
    plugins: [
      require('autoprefixer')({
        grid: true
      }),
      require('cssnano'),
      // More postCSS modules here if needed
    ]
  };
}
