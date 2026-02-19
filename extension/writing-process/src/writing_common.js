export function treeget(tree, key) {
    /*
      Retrieve an element from a tree with dotted notation

      e.g. treeget(
          {"hello": {"bar":"biff"}},
          "hello.bar"
      )

      Modified by PD to also deal with embbedded lists identified
      using notations like addedNodes[0].className.

      If not found, return null
    */
    let keylist = key.split(".");
    let subtree = tree;
    for(var i=0; i<keylist.length; i++) {
        // Don't process empty subtrees
        if (subtree == null) {
            return null;
        }
        // If the next dotted element is present,
        // reset the subtree to only include that node
        // and its descendants.
        if (keylist[i] in subtree) {
            subtree = subtree[keylist[i]];
        }
        // If a bracketed element is present, parse out
        // the index, grab the node at the index, and
        // set the subtree equal to that node and its
        // descendants.
        else {
            if (keylist[i] && keylist[i].indexOf('[')>0) {
                item = keylist[i].split('[')[0];
                idx = keylist[i].split('[')[1];
                idx = idx.split(']')[0];
                if (item in subtree) {
                    if (subtree[item][idx]!==undefined) {
                        subtree =subtree[item][idx];
                    } else {
                        return null;
                    }
                } else {
                    return null;
                }
            } else {
                return null;
            }
        }
    }
    return subtree;
}


export function googledocs_id_from_url(url) {
    /*
      Given a URL like:
        - Most common url
            https://docs.google.com/document/d/jkldfhjklhdkljer8934789468976sduiyui34778dey/edit/foo/bar
        - URL of new document
            https://docs.google.com/document/u/0/d/jkldfhjklhdkljer8934789468976sduiyui34778dey/docos/p/sync...
      extract the associated document ID:
        jkldfhjklhdkljer8934789468976sduiyui34778dey
      Return null if not a valid URL

      Regex explanation:
      1. `/.*:\/\/` - match any protocol (http/https) followed by ://
      2. `docs\.google\.com\/document\/` - match google docs domain
      3. `(?:u\/0\/)` - optionally match u/0/ which appears on new document creation
      4. `?d\/([^\/]*)\/` - match d/ until the subsequent / which holds the doc id
      5. `.*` - check for the remaining url
      6. `/i` - case insensitive
    */
    var match = url.match(/.*:\/\/docs\.google\.com\/document\/(?:u\/0\/)?d\/([^\/]*)\/.*/i);
    if(match) {
        return match[1];
    }
    return null;
}

export function googledocs_tab_id_from_url(url) {
    /*
      Given a URL like:
        https://docs.google.com/document/d/<doc_id>/edit?tab=t.95yb7msfl8ul
        https://docs.google.com/document/d/<doc_id>/edit?tab=t.95yb7msfl8ul#heading=h.abc123
      extract the associated tab ID:
        t.95yb7msfl8ul
      Return null if not a valid Google Docs URL or tab param.

      Regex explanation:
      1. `/.*:\/\/` - match any protocol (http/https) followed by ://
      2. `docs\.google\.com\/document\/` - match google docs domain
      3. `.*` - match any characters until we find the tab param
      4. `[?&]tab=` - match tab parameter in query string
      5. `([^&#]+)` - capture tab value, stopping at & (next param) or # (hash fragment)
      6. `/i` - case insensitive
    */
    var match = url.match(/.*:\/\/docs\.google\.com\/document\/.*[?&]tab=([^&#]+)/i);
    if (match) {
        return match[1];
    }
    return null;
}

var writing_lasthash = "";
function unique_id() {
    /*
      This function is used to generate a (hopefully) unique ID for
      each event. This isn't designed to be cryptosecure, since an
      untrusted client can set this to whatever it likes in either
      case. If used by a server, it ought to be rehashed with
      server-side info.

      The major planned use is debugging. In the future, this might be
      helpful for things like negotiating with the server too
      (e.g. "Have you seen this event yet?")
    */
    var shaObj = new jsSHA("SHA-256", "TEXT");
    shaObj.update(writing_lasthash);
    shaObj.update(Math.random().toString());
    shaObj.update(Date.now().toString());
    shaObj.update(document.cookie);
    shaObj.update("NaCl"); /* Salt? */
    shaObj.update(window.location.href);
    writing_lasthash = shaObj.getHash("HEX");
    return writing_lasthash;
}
