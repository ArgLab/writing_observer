/*
  TODO: FSM

  +----------------------+
  | Load server settings |
  | from chrome.storage  |
  +----------------------+
            |
            v
  +-------------------+
  | Connect to server |
  +-------------------+

    Load events queue
   from chrome.storage


Dequeue events
*/

var loggers_enabled;

// Kinda a hack, but this is a browser ID of sorts.
if(localStorage.getItem("logger_id") === null) {
    localStorage.setItem("logger_id", Math.random(1)+Date.now());
}

if(sessionStorage.getItem("logger_id") === null) {
    sessionStorage.setItem("logger_id", Math.random(1)+Date.now());
}

const browser_id = localStorage.getItem("logger_id");
const session_id = sessionStorage.getItem("logger_id");
const logger_id = Math.random(1)+Date.now();

var event_source;
var event_source_version
var metadata_header;

function console_logger() {
    /*
      Log to browser JavaScript console
     */
    return console.log;
}

function prepare_event(event_type, event) {
    /*
      TODO: Should we add user identity?
     */
    event['event'] = event_type;
    event['browser_id'] = browser_id;
    event['session_id'] = session_id;
    event['logger_id'] = logger_id;

    event['source'] = event_source;
    event['version'] = event_source_version;
    event['ts'] = Date.now();
    event['human_ts'] = Date();
    event['iso_ts'] = new Date().toISOString;
    return JSON.stringify(event);
}

function no_metadata() {
    return [];
}

function guest_identity_metadata() {
    /*
      Just identify as guest. Mostly useful for debugging.

      In most anonymous applications, we'd still rather generate a
      per-session or per-browser unique guest ID
     */
    return [
	prepare_event("test_framework_fake_identity", {"user_id": 'da-guest'})
    ];
}

function hash_identity_metadata() {
    /*
      Collect the identity from the page hash. 

      Convenient for secure / one-off settings, like user studies /
      cognitive labs.
     */
    return [
	prepare_event("hash_auth", {hash: location.hash})
    ];
}

function websocket_logger(server) {
    /*
       Log to web socket server.

       Optional:
       * We could send queued events on socket open (or on a timeout)
       * Or we could just wait for the next event (what we do now)

       The former would be a little bit more robust.
    */
    var socket;
    var state = new Set()
    var queue = [];

    // Default server is same host as request is coming from,
    // same port, same SSL setting, under /wsapi/in
    if((server === null) || (server === undefined)) {
	const protocol_map = {"https:": "wss:", "http:": "ws:"};
	const protocol = protocol_map[document.location.protocol];
	const host = document.location.host;

	server = protocol + "//" + host + "/wsapi/in/";
    }
    console.log(server);

    function new_websocket() {
	state = new Set();
	socket = new WebSocket(server);
	socket.onopen=prepare_socket;  // auth, metadata, set state to ready
	socket.onerror = function(event) {
	    console.log("Could not connect");
	    var event = { "issue": "Could not connect" };
	    event = prepare_event("warning", event);
	    queue.push(event);
	};
	socket.onclose = function(event) {
	    console.log("Lost connection");
	    var event = { "issue": "Lost connection", "code": event.code };
	    event = prepare_event("warning", event);
	    queue.push(event);
	};
	return socket;
    }

    socket = new_websocket();

    function are_we_done() {
	/*
	  This used to be a long list of things we wanted to do before
	  we were ready to send stuff. Now it's short, but I expect it
	  will lengthen again.
	 */
	if (state.has("metadata")) {
	    state.add("ready");
	}
	dequeue();
    }

    function prepare_socket() {
	// Send the server the metadata (e.g. auth)
	// This should be made asynchronous
	console.log("Connected");
	metadata = metadata_header();
	queue.unshift(prepare_event("metadata_finished", {}));
	while(metadata.length > 0) {
	    queue.unshift(metadata.pop());
	}
	state.add("metadata");
	are_we_done();
    }

    function dequeue() {
	console.log("dequeue");
	if(socket === null) {
	    // Do nothing. We're reconnecting.
	    console.log("Event squelched; reconnecting");
	} else if(socket.readyState === socket.OPEN &&
		  state.has("ready")) {
	    console.log("Sending event...");
	    while(queue.length > 1) {
		var event = queue.shift();
		socket.send(event);  /* TODO: We should do receipt confirmation before dropping events */
	    }
	} else if((socket.readyState == socket.CLOSED) || (socket.readyState == socket.CLOSING)) {
	    /*
	      If we lost the connection, we wait a second and try to open it again.

	      Note that while socket is `null` or `CONNECTING`, we don't take either
	      branch -- we just queue up events. We reconnect after 1 second if closed,
	      or dequeue events if open.
	    */
	    console.log("Re-opening connection in 1s");
	    socket = null;
	    state = new Set();
	    setTimeout(function() {
		console.log("Re-opening connection");
		socket = new_websocket();
	    }, 1000);
	}
    }

    return function(data) {
	queue.push(data);
	dequeue();
    }
}

function ajax_logger(ajax_server) {
    /*
      HTTP event per request.

      To do: Handle failures / dropped connections
     */
    var server = ajax_server;
    return function(data) {
	/*
	  Helper function to send a logging AJAX request to the server.
	  This function takes a JSON dictionary of data.
	*/

	httpRequest = new XMLHttpRequest();
	//httpRequest.withCredentials = true;
	httpRequest.open("POST", ajax_server);
	httpRequest.send(data);
    }
}

/*
logger takes a list of loggers. For example, if we want to send to the server twice, and log on console:

logger([
    console_logger(),
    ajax_logger("https://localhost/webapi/"),
    websocket_logger("wss://localhost/wsapi/in/")
]);

loggers_enabled = [
    console_logger(),
    //ajax_logger("https://writing.hopto.org/webapi/")//,
    websocket_logger("wss://writing.hopto.org/wsapi/in/")
];
*/

function log_event(event_type, event) {
    event = prepare_event(event_type, event);
    // TODO: Add username
    for (var i=0; i<loggers_enabled.length; i++) {
	loggers_enabled[i](event);
    }
}

function browser_info() {
    /*
      Browser data. Helpful for debugging browser issues.
     */
    const fields = [
	'appCodeName',
	'appName',
	'buildID',
	'cookieEnabled',
	'deviceMemory',
	'language',
	'languages',
	'onLine',
	'oscpu',
	'platform',
	'product',
	'productSub',
	'userAgent',
	'webdriver'
    ];
    let bro_info = {};
    for(var i=0; i<fields.length; i++) {
	bro_info[fields[i]] = navigator[fields[i]];
    }

    // We'll get a subset....
    const cfields = [
	'effectiveType',
	'rtt',
	'downlink',
	'type',
	'downlinkMax',
    ];
    bro_info['connection'] = {};
    if(navigator['connection'] != null) {
	for(var i=0; i<cfields.length; i++) {
	    bro_info['connection'][cfields[i]] = navigator['connection'][cfields[i]];
	}
    }
    bro_info['document'] = {};
    let dfields = [
	'URL',
	'baseURI',
	'characterSet',
	'charset',
	'compatMode',
	'cookie',
	'currentScript',
	'designMode',
	'dir',
	'doctype',
	'documentURI',
	'domain',
	'fullscreen',
	'fullscreenEnabled',
	'hidden',
	'inputEncoding',
	'isConnected',
	'lastModified',
	'location',
	'mozSyntheticDocument',
	'pictureInPictureEnabled',
	'plugins',
	'readyState',
	'referrer',
	'title',
	'visibilityState',
    ];
    for(var i=0; i<dfields.length; i++) {
	bro_info['document'][dfields[i]] = document[dfields[i]];
    }
    bro_info['window'] = {}
    let wfields = [
	'closed',
	'defaultStatus',
	'innerHeight',
	'innerWidth',
	'name',
	'outerHeight',
	'outerWidth',
	'pageXOffset',
	'pageYOffset',
	'screenX',
	'screenY',
	'status',
    ];
    for(var i=0; i<wfields.length; i++) {
	bro_info['window'][wfields[i]] = window[wfields[i]];
    }

    return bro_info;
}

function init_logger(loggers, source, version, metadata_function) {
    event_source = source;
    event_source_version = version;
    loggers_enabled = loggers;
    metadata_header = metadata_function;
    log_event("browser_info", browser_info());
    return log_event;
}

// We'd like to work with and without require.js
if(typeof define !== "undefined") {
    define([],
	   function() {
               return {
		   "console_logger": console_logger,
		   "ajax_logger": ajax_logger,
		   "websocket_logger": websocket_logger,
		   "guest_identity_metadata": guest_identity_metadata,
		   "hash_identity_metadata": hash_identity_metadata,
		   "no_metadata": no_metadata,
		   "logger": init_logger
               }
	   }
	  );
}
