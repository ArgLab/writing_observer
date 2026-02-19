'''
This can reconstruct a Google Doc from Google's JSON requests. It
is based on the reverse-engineering by James Somers in his blog
post about the Traceback extension. The code is, obviously, all
new.

See: `http://features.jsomers.net/how-i-reverse-engineered-google-docs/`
'''

import json

"""
The placeholder character is used to fill gaps in the document, particularly
when there's a mismatch between the index and the length of the document's text (doc._text).
In an empty document, the insertion index (from the insert event `is`) is 1. However,
when the extension is started on a non-empty document, the first insertion index will be
greater than 1. This can lead to inconsistencies in indexing.
This placeholder is used to fill the 'gap' between len(doc._text) and the first insertion
index recorded in the logs.
This is done for the delete event ('ds') as well.
Say the first insert event in the logs is of a character 'a' with an index of 10.
This placeholder will be used to fill the gap between 1 and 10. Internally doc._text will
have 10 characters and when returning the output, all placeholders will be removed from
doc._text leaving only the character 'a'.
"""
PLACEHOLDER = '\x00'


class google_text(object):
    '''
    We encapsulate a string object to support a Google Doc snapshot at a
    point in time. Right now, this adds cursor position. In the future,
    we might annotate formatting and similar properties.
    '''
    def __new__(cls):
        '''
        Constructor. We create a blank document to be populated.
        '''
        new_object = object.__new__(cls)
        new_object._text = ""
        new_object._position = 0
        new_object._edit_metadata = {}
        new_object._tabs = {}
        new_object.fix_validity()
        return new_object

    def assert_validity(self):
        '''
        We do integrity checks. We store cursor length and text length in
        two lists for efficiency, and for now, this just confirms they're
        the same length.
        '''
        cursor_array_length = len(self._edit_metadata["cursor"])
        textlength_array_length = len(self._edit_metadata["length"])
        length_difference = cursor_array_length - textlength_array_length
        if length_difference != 0:
            raise Exception(
                "Edit metadata length doesn't match. This should never happen."
            )

    def fix_validity(self):
        '''
        Check we satisify invariants, and if not, fix them. This is helpful
        for graceful degredation. We also use this to initalize the object.
        '''
        errors_found = []

        if "cursor" not in self._edit_metadata:
            self._edit_metadata["cursor"] = []
            errors_found.append("No cursor array")
        if "length" not in self._edit_metadata:
            self._edit_metadata["length"] = []
            errors_found.append("No length array")

        # We expect edit metadata to be the same length. We went
        # from tabular to columnar which does not guarantee this
        # invariant, unfortunately. We should evaluate if this
        # optimization was premature, but it's a lot more compact.
        cursor_array_length = len(self._edit_metadata["cursor"])
        textlength_array_length = len(self._edit_metadata["length"])
        length_difference = cursor_array_length - textlength_array_length
        if length_difference > 0:
            print("Mismatching lengths. This should never happen!")
            self._edit_metadata["length"] += [0] * length_difference
            errors_found.append("Mismatching lengths")
        if length_difference < 0:
            print("Mismatching lengths. This should never happen!")
            self._edit_metadata["cursor"] += [0] * -length_difference
            errors_found.append("Mismatching lengths")
        return errors_found

    def from_json(json_rep):
        '''
        Class method to deserialize from JSON

        For null objects, it will create a new Google Doc.
        '''
        new_object = google_text.__new__(google_text)
        if json_rep is None:
            json_rep = {}
        new_object._text = json_rep.get('text', '')
        new_object._position = json_rep.get('position', 0)
        new_object._edit_metadata = json_rep.get('edit_metadata', {})

        if 'tabs' in json_rep and json_rep['tabs']:
            new_object._tabs = {}
            for tab_id, tab_data in json_rep['tabs'].items():
                new_object._tabs[tab_id] = google_text.from_json(tab_data)
        else:
            new_object._tabs = {}

        new_object.fix_validity()
        return new_object

    def update(self, text):
        '''
        Update the text. Note that we should probably combine this
        with updating the cursor position, since if text updates,
        the cursor should always update too.
        '''
        self._text = text

    def len(self):
        '''
        Length of the string
        '''
        return len(self._text)

    @property
    def position(self):
        '''
        Cursor postion. Perhaps we should rename this?
        '''
        return self._position

    @position.setter
    def position(self, p):
        '''
        Update cursor position.

        Side effect: Update Deane arrays.
        '''
        self._edit_metadata['length'].append(len(self._text))
        self._edit_metadata['cursor'].append(p)
        self._position = p

    @property
    def edit_metadata(self):
        '''
        Return edit metadata. For now, this is length / cursor position
        arrays, but perhaps we should rename this as we expect more
        analytics.
        '''
        return self._edit_metadata

    def __str__(self):
        '''
        This returns __just__ the text of the document (no metadata)
        '''
        return self._text

    @property
    def json(self):
        '''
        This serializes to JSON.
        '''
        result = {
            'text': self._text,
            'position': self._position,
            'edit_metadata': self._edit_metadata
        }
        if self._tabs:
            result['tabs'] = {tab_id: tab.json for tab_id, tab in self._tabs.items()}
        return result


def get_parsed_text(self):
    '''
    Returns the text ignoring the normal placeholders
    '''
    return self._text.replace(PLACEHOLDER, "")


def dispatch_command(doc, cmd):
    if cmd['ty'] in dispatch:
        doc = dispatch[cmd['ty']](doc, **cmd)
    else:
        print("Unrecogized Google Docs command: " + repr(cmd['ty']))
        # TODO: Log issue and fix it!
    return doc


def command_list(doc, commands):
    '''
    This will process a list of commands. It is helpful either when
    loading the history of a new doc, or in updating a document from
    new `save` requests.
    '''
    for item in commands:
        doc = dispatch_command(doc, item)
    return doc


def multi(doc, mts, ty):
    '''
    Handles a batch of commands.

    `mts` is the list of commands
    `ty` is always `mlti`
    '''
    doc = command_list(doc, mts)
    return doc


def insert(doc, ty, ibi, s):
    '''
    Insert new text.
    * `ty` is always `is`
    * `ibi` is where the insert happens
    * `s` is the string to insert
    '''
    # The index of the next character after the last character of the text
    nextchar_index = len(doc._text) + 1
    # If the insert index is greater than nextchar_index, insert placeholders to fill the gap
    # This occurs when the document has undergone modifications before the logger has been initialized
    if ibi > nextchar_index:
        insert(doc, ty, nextchar_index, PLACEHOLDER * (ibi - nextchar_index))
    doc.update("{start}{insert}{end}".format(
        start=doc._text[0:ibi - 1],
        insert=s,
        end=doc._text[ibi - 1:]
    ))

    doc.position = ibi + len(s)

    return doc


def delete(doc, ty, si, ei):
    '''
    Delete text.
    * `ty` is always `ds`
    * `si` is the index of the start of deletion
    * `ei` is the end
    '''
    # Index of the last character in the text. `si` and `ei` shouldn't go beyond that
    lastchar_index = len(doc._text)
    # If the deletion indexes are greater than nextchar_index, insert placeholders to fill the gap
    # This occurs when the document has undergone modifications before the logger has been initialized
    if si > lastchar_index:
        insert(doc, ty, lastchar_index + 1, PLACEHOLDER * (si - lastchar_index))
    if ei > lastchar_index:
        insert(doc, ty, lastchar_index + 1, PLACEHOLDER * (ei - lastchar_index))
    doc.update("{start}{end}".format(
        start=doc._text[0:si - 1],
        end=doc._text[ei:]
    ))

    doc.position = si

    return doc


def replace(doc, ty, snapshot):
    for entry in snapshot:

        # The index of the next character after the last
        # character of the text
        nextchar_index = len(doc._text) + 1
        if 'ty' in entry and entry['ty'] == 'is':

            s = entry['s']
            ibi = entry['ibi']
            if 'sl' in entry:
                sl = entry['sl']
            else:
                sl = len(s)

            # If the insert index is greater than
            # nextchar_index, insert placeholders
            # to fill the gap.
            #
            # This occurs when the document has undergone
            # modifications before the logger has been
            # initialized
            if ibi > nextchar_index:
                insert(doc,
                       ty,
                       nextchar_index,
                       PLACEHOLDER * (ibi - nextchar_index))

            doc.update("{start}{insert}{end}".format(
                start=doc._text[0:ibi - 1],
                insert=s,
                end=doc._text[ibi + sl - 1:]
            ))

    return doc


def alter(doc, si, ei, st, sm, ty):
    '''
    Alter commands change formatting.

    We ignore these for now.
    '''
    return doc


def null(doc, **kwargs):
    '''
    Do nothing. Google sometimes makes null requests. There are also
    requests we don't know how to process.

    I'm not quite sure what these are. The command is not JavaScript's
    `null` but the string `'null'`
    '''
    return doc


def nm(doc, nmc, nmr, **kwargs):
    '''
    Handle named commands for tabs (sub-documents).

    * `nmc` is the command to execute
    * `nmr` is the name/reference list, which contains the target tab ID
    '''
    # Find the target tab from the nmr list
    target_tab = None
    for item in reversed(nmr or []):
        if isinstance(item, str) and item.startswith("t."):
            target_tab = item
            break

    if target_tab is None:
        # No tab specified, apply to main document
        doc = dispatch_command(doc, nmc)
    else:
        # Ensure the tab exists
        if target_tab not in doc._tabs:
            doc._tabs[target_tab] = google_text()

        # Apply the command to the sub-document
        doc._tabs[target_tab] = dispatch_command(doc._tabs[target_tab], nmc)

    return doc


# This dictionary maps the `ty` parameter to the function which
# handles data of that type.

# TODO: `ae,``ue,` `de,` and `te` need to be
# reverse-engineered. These happens if we e.g. make a new bullet
# list, or add an image.

# TODO: 'iss' and 'dss' are generated when suggested text is inserted or deleted.
# these can't be handled like plain 'is' or 'ds' because the include different fields
# (e.g., 'sugid', presumably, suggestion id.)
dispatch = {
    'ac': null, # new tab title
    'ae': null,
    'ase': null,  # suggestion
    'ast': null,  # suggestion. Image?
    'astss': null,  # suggestion. Autospell?
    'ue': null,
    'de': null,
    'dse': null,  # suggestion
    'dss': null,  # suggested deletion
    'te': null,
    'as': alter,
    'ds': delete,
    'is': insert,
    'iss': null,  # suggested insertion
    'mefd': null,  # suggestion
    'mkch': null,  # name of the first tab
    'mlti': multi,
    'msfd': null,  # suggestion
    'nm': nm,   # named command for tabs
    'null': null,
    'ord': null,
    'ras': null,  # suggestion. Autospell?
    'rplc': replace,  # rplc is called as the first edit
                      # when the document is created from
                      # a template, so if you want to know
                      # what text was NOT written by the author,
                      # logging the text buffer after the initial
                      # rplc action will give you that.
    'rte': null,  # suggestion
    'rue': null,  # suggestion
    'rvrt': replace,  # apparently logged after an undo
    'sas': null,  # suggestion. Autospell?
    'sl': null,
    'ste': null,  # suggestion
    'sue': null,  # suggestion
    'ucp': null,  # updated tab title
    'uefd': null,  # suggestion
    'use': null,  # suggestion
    'umv': null,
    'usfd': null,  # suggestion
}

if __name__ == '__main__':
    google_json = json.load(open("sample3.json"))
    docs_history = google_json['client']['history']['changelog']
    docs_history_short = [t[0] for t in docs_history]
    doc = google_text()
    doc = command_list(doc, docs_history_short)
    print(doc)
    print(doc.position)
    print(doc.edit_metadata)
