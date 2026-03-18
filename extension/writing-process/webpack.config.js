const path = require('path');

module.exports = {
    entry: {
        background: path.join(__dirname, 'src', 'background.js'),
        service_worker: path.join(__dirname, 'src', 'service_worker.js'),
        writing_common: path.join(__dirname, 'src', 'writing_common.js'),
        writing: path.join(__dirname, 'src', 'writing.js'),
    },
    output: {
        path: path.join(__dirname, 'src'),
        filename: '[name].bundle.js',
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-env'],
                    },
                },
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader'],
            },
            {
                test: /\.html$/,
                use: ['html-loader'],
            }
        ],
    },
    // exclude these external packages from the bundling process
    // lo_event relies on these
    externals: {
        'sqlite3': 'sqlite3',
        'indexeddb-js': 'indexeddb-js',
        'crypto': 'crypto',
        'redux': 'redux'
    }
};
