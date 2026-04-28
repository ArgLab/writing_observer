# portfolio_diff frontend

This directory contains the Next.js frontend for portfolio diff visualizations. The app is configured with `output: "export"`, so a production build generates static files in `out/` that can be copied into Python modules or archived for an external assets repository.

## Prerequisites

- Node.js + npm available locally.
- Install dependencies from this directory:

```bash
npm install
```

## Build the static site

From `modules/portfolio_diff`:

```bash
rm -rf out/
npm run build
```

After build completion, the static export is written to `out/`.

## Bundle build output into a `.tar.gz`

If you need an artifact for an assets repository, archive the exported files from `out/`:

```bash
VERSION_TAG=$(date +%Y%m%d)
tar -C out -czf "portfolio_diff_${VERSION_TAG}.tar.gz" .
```

That creates a tarball in `modules/portfolio_diff` (for example `portfolio_diff-20260710.tar.gz`) containing the static site root.

You should include copy this to the [`lo_assets` repository](github.com/ArgLab/lo_assets) and update the `portfolio_diff-current.tar.gz` link to point to the new version.

## Existing helper script

This repo also includes `build_and_add_to_module.sh`, which builds and copies `out/` into `../wo_portfolio_diff/wo_portfolio_diff/portfolio_diff/` for local module packaging:

```bash
./build_and_add_to_module.sh
```

Use that helper when updating the in-repo Python package. Use the tarball workflow above when publishing to a separate assets repository.
