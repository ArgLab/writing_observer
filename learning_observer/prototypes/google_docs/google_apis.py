# TODO/HACK/Unfinished:
#
# * We do *not* handle pagination in this prototype.

import argparse
import os.path

import json

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]


def list_files(creds):
    service = build('drive', 'v3', credentials=creds)

    # Call the Drive v3 API
    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    print(items)


def document(creds, document_id):
    service = build('docs', 'v1', credentials=creds)

    # This is an optional keyword parameter we should play with
    # later.
    suggestion_modes = [
        "DEFAULT_FOR_CURRENT_ACCESS",
        "SUGGESTIONS_INLINE",
        "PREVIEW_SUGGESTIONS_ACCEPTED",
        "PREVIEW_WITHOUT_SUGGESTIONS"
    ]

    SUGGESTION_MODE = suggestion_modes[0]

    document = service.documents().get(
        documentId=document_id
    ).execute()
    print('The title of the document is: {}'.format(document.get('title')))
    return document


def document_revisions(creds, document_id):
    service = build('drive', 'v3', credentials=creds)
    r = service.revisions()
    return r.list(fileId=document_id).execute()


def document_comments(creds, document_id):
    service = build('drive', 'v3', credentials=creds)
    return service.comments().list(
        fileId=document_id,
        fields="*",
        includeDeleted=True
    ).execute()


def authenticate():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if False and creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def main(document_id):
    """Shows basic usage of the Docs API.
    Prints the title of a sample document.
    """
    creds = authenticate()
    print(list_files(creds))
    print("Document:")
    print(document(creds, document_id))
    with open("doc.json", "w") as fp:
        fp.write(json.dumps(document(creds, document_id), indent=2))
    print("Document revisions:")
    print(document_revisions(creds, document_id))
    print("Document comments:")
    print(document_comments(creds, document_id))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "document_id", help="Google document ID. Usually 44 characters long"
    )
    args = parser.parse_args()
    main(args.document_id)
