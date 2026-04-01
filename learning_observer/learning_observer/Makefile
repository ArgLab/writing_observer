# Bundle up all the JavaScript into a single file
#
# We don't shrink / minify the file yet. This requires more RAM than a
# nano AWS instance can handle. If we want to do this, remove
# `optimize=none`

# We're doing something ugly and horrible with paths, but we just
# wanted minimum viable / thin red line with all the pieces in
# place. We'll clean up paths at some point.

# To use this bundle, switch from webapp to webapp-built.

js-bundle:
	rm -f static/webapp-built.js  # Remove the old file, if it exists
	rm -f static/static  # Remove hack, if left over from last run
	ln -s ../static static/static  # Hack to make paths work. TODO: Fix.
	node static/3rd_party/r.js -o build.js optimize=none  # Actual build
	rm -f static/static  # Remove hack
	mv webapp-built.js static  # And our final file
