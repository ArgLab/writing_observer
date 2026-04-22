# `lo_event` is the Learning Observer event library (and also `lo_assess` within it is the Learning Observer activity library, which should be factored out eventually).

# * It's a library, and there's no practical stand-alone way to do more extensive development without some use-cases. This is a good set of use cases.
# * As we develop those, we often make changes to `lo_event` and `lo_assess`. Quite a lot, actually.

# This script packages `lo_event` into a node package, wipes the `next.js` cache (which often contains relics before changes), and installs it.

# Without this, development of `lo_event` is painful. Even with this, in an ideal case, we would rerun this whenever there were changes to `lo_event` automatically with some kind of watch daemon.
rm -Rf .next/cache/
pushd ../lo_event/
npm run prebuild
npm pack
popd
npm install ../lo_event/lo_event-0.0.3.tgz  --no-save
