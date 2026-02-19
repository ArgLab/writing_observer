# Dash/React Components

## Building and Using Components in Dashboards

In Learning Observer, we create React components and generate a Python package for them to be used with the Dash framework. These components are housed in the `lo_dash_react_components` module and enable the creation of highly customizable dashboards. This document guides you through the component development process, the build process, and using the components in your dashboards.

### Pre-built installation

These components take a bit of extra infrastructure to build (mainly `node`). If you just with to use these components, without developing new ones or changing current ones, we suggest installing the pre-built package available in the [LO Assets github repository](https://github.com/ETS-Next-Gen/lo_assets/tree/main/lo_dash_react_components).

### Requirements

TODO verify which Node versions work. Previously, we encountered dependency issues with newer versions of node.

A downstream dependency in the build process may cause breaking behavior depending on your node version. The latest version of Node `v16` (tested on `v16.19.1`) should work fine; however, we've noticed errors on Node `v18`.

If you already have `v18` on your system, install [nvm: Node Version Manager](https://github.com/nvm-sh/nvm). When running `nvm` commands within the project without specifying a specific version, it will automatically look for the version defined in the `.nvmrc` file in the root directory.

To install and activate the node version, run:

```bash
nvm install
nvm use
```

Any `npm` command will now use Node `v16`.
Next, make sure to change into the components directory and install all dependencies.
Note that all future `npm` commands should be ran from within the components directory.

```bash
cd modules/lo_dash_react_components
npm install
```

### Component Development

1. Create a React component file with the `.react.js` extension in the `src/lib/components` directory. Use a class structure instead of a function definition due to a limitation in the Dash auto-generation process.
    - Remember to use class (not functional) syntax for compatibility with `dash`.
    - Remember to use the setProps property whenever props change internally. This is used by `dash` to handle properly handle callbacks.
1. For component-specific CSS, create a file with the same name and an `.scss` extension in the `src/lib/components` directory.
1. If the component needs data, toss in a `.testdata.js` file in `src/lib/components`. Note that this file should not use modern JavaScript (we're limited to ES5.1, except for `export default`).
1. For `dash` to be aware of the component, it should be added to `src/lib/index.js`
1. Use `npm run start-all` to start the react, scss, and dash workflow (automatically refreshs on file change).
1. Run `npm run build` to generate the appropriate Python components (same as above, but without fresh capability).
1. (Optional) Package them into a distribution using the `build:python` command.

### Build Process

The build process provides various commands to build specific pieces or watch sets of files for changes, triggering auto-rebuilds. This includes converting SCSS files using SASS and building React to Dash Python packages.

Here are some useful NPM scripts for building components:

- `build:js`: Builds JavaScript files using Webpack in production mode.
- `build:backends`: Generates components in the `lo_dash_react_components` module.
- `build`: Builds CSS, JS, and backends.
- `build-css`: Converts SCSS files to CSS.
- `watch-css`: Watches and automatically rebuilds SCSS files.
- `build:python`: Cleans the `dist/` and `build/` directories and creates a Python distribution.

### Using Components in Dashboards

To use the components in your dashboards, simply import the desired component from the `lo_dash_react_components` module and use them as you would any other Dash component.

```python
import lo_dash_react_components as lodrc

ws_component = lodrc.LOConnection()
...
```

## Share

We encourage you to share your components back with us. That way:

- We're more likely to understand your use-case
- We're less likely to break them as we evolve the system.

## Issues

If ESLint errors block your app, edit `node_modules/react-dev-utils/webpackHotDevClient.js` to disable `handleWarnings`. See:

https://stackoverflow.com/questions/48714225/how-to-not-show-warnings-in-create-react-app
