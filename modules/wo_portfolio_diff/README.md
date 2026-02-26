# wo_portfolio_diff

This package bundles the compiled frontend output of the `portfolio_diff` project as a Python package, allowing it to be installed and served as a static asset.

## How It Works

### 1. Build the Frontend

The frontend lives in the `portfolio_diff` source directory. To produce a fresh build, run the following from that directory:

```bash
rm -rf out/
npm run build
```

This removes any previous build artifacts and compiles the project into an `out/` folder.

### 2. Copy the Build Output

Once the build is complete, the compiled assets are copied into this package:

```bash
rm -rf ../wo_portfolio_diff/wo_portfolio_diff/portfolio_diff/
mkdir ../wo_portfolio_diff/wo_portfolio_diff/portfolio_diff/
cp -r out/ ../wo_portfolio_diff/wo_portfolio_diff/portfolio_diff/
```

This replaces the previously bundled assets with the freshly built ones, placing the contents of `out/` under `wo_portfolio_diff/portfolio_diff/`.

### 3. Install the Package

With the build output in place, install the Python package in editable mode:

```bash
pip install -e modules/wo_portfolio_diff
```

The `-e` flag installs the package in editable (development) mode, meaning changes to the package directory are immediately reflected without needing to reinstall.

## Summary

| Step | Command | Purpose |
|------|---------|---------|
| Clean | `rm -rf out/` | Remove stale build artifacts |
| Build | `npm run build` | Compile the frontend into `out/` |
| Sync | `cp -r out/ ../wo_portfolio_diff/...` | Update bundled assets in this package |
| Install | `pip install -e modules/wo_portfolio_diff` | Install the package locally |

### ENV Variables

To set environment variables at build time, add them to a `.env.production` file. The build command will load these in.

| Env | Purpose |
|-----|---------|
| NEXT_PUBLIC_LO_WS_ORIGIN | Where to point communication protocol queries. |

