'''
Handler to serve files from a git repo from an aiohttp server.

For experimental use only. This code would need to be optimized for
production use. It is blockingm, non-caching, and generally, not
designed for scale. It would be a few days work to make this code
scalable.

It doesn't do auth/auth, but that could be handled in the calling code
via a middleware or decorator, or in the web server.

It would be nice to have more graceful error handling. There are
files like media and 3rd party libraries which we need to serve up
too. Some kind of callback?
'''

import mimetypes
import os.path

import aiohttp.web

import gitserve.gitaccess


WARNED = False


def git_handler_wrapper(
        repo,
        cookie_prefix="",
        prefix="",
        bare=True,
        working_tree_dev=False
):
    '''
    Returns a handler which can serve files from a git repo, from
    different branches. This should obviously only be used with
    non-private repos. It also sets a cookie with the hash from git,
    so it's nice for science replicability. If we're serving data
    for a coglab, we can record which version we served from.

    Parameters:
         repo: git URL of the repo
         cookie_prefix:
    '''
    repo = gitserve.gitaccess.GitRepo(repo, bare=bare)

    def git_handler(request):
        global WARNED
        branch = request.match_info['branch']
        if working_tree_dev:
            branch = gitserve.gitaccess.WORKING_DIR
            if not WARNED:
                print("Serving from working tree. "
                      "This should not be used in prod.")
                WARNED = True
        filename = os.path.join(prefix, request.match_info['filename'])
        body = repo.show(branch, filename)
        mimetype = mimetypes.guess_type(filename)[0]
        if mimetype is None:
            mimetype = "text/plain"

        if mimetype.startswith("text/"):
            response = aiohttp.web.Response(
                text=body.decode('utf-8'),
                content_type=mimetype
            )
        else:
            response = aiohttp.web.Response(
                body=body,
                content_type=mimetype
            )
        response.set_cookie(
            cookie_prefix + "githash",
            repo.rev_hash(branch)
        )
        return response
    return git_handler
