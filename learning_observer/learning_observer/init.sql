reset: |
  DROP TABLE IF EXISTS USERS;
  DROP TABLE IF EXISTS WRITING_EVENTS;
  DROP TABLE IF EXISTS DOCUMENTS;
  DROP TABLE IF EXISTS CLASSES;
  DROP FUNCTION IF EXISTS insert_event;

init: |
  CREATE TABLE IF NOT EXISTS USERS (
         idx          SERIAL PRIMARY KEY,
         username     text UNIQUE,
         email        text,
         date_created timestamp NOT NULL DEFAULT NOW()
  );
  
  CREATE TABLE IF NOT EXISTS DOCUMENTS (
         idx       SERIAL PRIMARY KEY,
         docstring char(48) UNIQUE,
         date_created timestamp NOT NULL DEFAULT NOW()
  );
  
  CREATE TABLE IF NOT EXISTS WRITING_EVENTS (
         idx           SERIAL PRIMARY KEY,
         user_id       integer REFERENCES USERS (idx),  -- Who is editing?
         document      integer REFERENCES DOCUMENTS (idx), -- Which document?
         date_created  timestamp NOT NULL DEFAULT NOW(),
         event         json,
         ft            text     -- For debugging: Ongoing reconstruction of full text
  );

  CREATE TABLE IF NOT EXISTS CLASSES (
  	 teacher      integer REFERENCES USERS (idx),
	 student      integer REFERENCES USERS (idx),
  	 classname    text
   );

--   CREATE OR REPLACE FUNCTION insert_event(
--          gusername  text,
--          gdocstring char(48),
--          event      json,
--          ft         text     -- For debugging: Ongoing reconstruction of full text
--   ) RETURNS text
--   LANGUAGE plpgsql
--   AS $$
--   DECLARE
--     strresult text;
--     affected_rows integer;
--   BEGIN
--     strresult := '';
--     -- If the user does not exist, create the user. Add 'New User' to the return value
--     if NOT EXISTS (SELECT 1 FROM USERS where USERS.username = gusername) THEN
--       strresult := strresult || '[New User]';
--       INSERT INTO USERS (username) VALUES (gusername);
--     END IF;
    
--     -- If the document does not exist, create the document. Add "New Document" to the return value
--     if NOT EXISTS (SELECT 1 FROM DOCUMENTS where DOCUMENTS.docstring = gdocstring) THEN
--       strresult := strresult || '[New Document]';
--       INSERT INTO DOCUMENTS (docstring) VALUES (gdocstring);
--     END IF;
--     -- Insert the event into the database
--     with INSERT_ROW_COUNT as
--        (INSERT INTO WRITING_EVENTS
--          (user_id, document, event)
--          (SELECT
--               users.idx, documents.idx, event
--           FROM
--              users, documents where users.username=gusername and documents.docstring=gdocstring)
--           RETURNING 1)
--        SELECT COUNT(*) INTO affected_rows FROM INSERT_ROW_COUNT;
    
--     -- This is a little bit awkward, but we return:
--     -- 1. Number of rows inserted
--     -- 2. Whether a new user or document was created
--     -- As a string.
--     return cast(affected_rows as varchar) || ' ' || strresult;
--     COMMIT;
--   END;
--   $$;
--   -- Example: SELECT insert_writing_delta('pmitros', 'random-google-doc-id', 'is', 7,8,4,'hello','temp');

-- stored_procedures:
--   insert_event: |
--     -- PREPARE insert_writing_delta (text, char(48), char(2), integer, integer, integer, text, text) AS
--       SELECT insert_event($1, $2, $3, '');

--   fetch_events: |
--     -- PREPARE fetch_writing_deltas (text, char(48)) AS  -- username, document string
--       SELECT
--         WRITING_EVENTS.idx, WRITING_EVENTS.date_created, event
--       FROM
--         WRITING_EVENTS, USERS, DOCUMENTS
--       WHERE
--         WRITING_EVENTS.user_id = USERS.idx AND
--         WRITING_EVENTS.document = DOCUMENTS.idx AND
--         DOCUMENTS.docstring = $2 AND
--         USERS.username = $1
--       ORDER BY
--         WRITING_EVENTS.idx;
