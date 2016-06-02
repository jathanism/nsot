var path = require("path");
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');

module.exports = {
  context: __dirname,
  entry: './assets/js/index',
  output: {
    path: path.resolve('./assets/bundles/'),
    filename: "[name]-[hash].js",
  },

  plugins: [
    new BundleTracker({filename: './webpack-stats.json'}),
  ],

  module: {
    loaders: [
      // {test: /\.jsx?$/, exclude: /node_modules/, loaders: ['babel'],},
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        loader: 'babel',
        query: {
          // presets: ['react']
          // es2015 is needed for "import" style vs. "require".
          // Sauce: http://stackoverflow.com/a/33608835/194311
          presets: ['react', 'es2015', 'stage-0'],
          plugins: [
            'transform-object-rest-spread', 'transform-decorators-legacy'
          ]
        }
      },
    ],
  },

  resolve: {
    modulesDirectories: ['node_modules', 'bower_components'],
    extensions: ['', '.js', '.jsx'],

  },
}
