/*
  This ought to be packaged up at some point....
 */

function encode_query_string(obj) {
    /*
       Create a query string from a dictionary

       {a:'b', c:'d'} ==> "a=b&c=d"

       dictionary -> string
    */
    var str = [];
    for (var p in obj)
	if (obj.hasOwnProperty(p)) {
	    str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
	}
    return str.join("&");
}


function dashboard_connection(key, callback, params) {
    /*
       Create a web socket connection to the server.
     */
    const course = key.course;
    const module = key.module;
    const get_params = encode_query_string(key);
    // TODO: Course should be abstracted out
    const protocol = {"http:": "ws:", "https:": "wss:"}[window.location.protocol];
    var ws = new WebSocket(`${protocol}//${window.location.host}/wsapi/dashboard?${get_params}`);
    ws.onmessage = function (event) {
	console.log("Got data");
	let data = JSON.parse(event.data);
	if(data.logged_in === false) {
	    window.location.href="/";  // TODO: System.go_home() or something
	} else {
	    callback(data);
	}
    }
}

function decode_string_dict(stringdict) {
    /*
      Decode a string dictionary of the form:
        `key1=value1; key2=value2;key3=value3`
      This is used both to encode document hashes and for cookies.

      This is inspired by a (buggy) cookie decoder from w3cschools. We
      wrote out own since that one starts out with decodeURIComponent,
      potentially allowing for injections.
     */
    var decoded = {};
    var splitstring = stringdict.split(';');
    for(var i = 0; i<splitstring.length; i++) {
	var pair = splitstring[i];
	while (pair.charAt(0) == ' ') {
	    pair = pair.substring(1);
	}
	pair = pair.split('=');
	let key = decodeURIComponent(pair[0]);
	let value = decodeURIComponent(pair[1]);
	decoded[key] = value;
    }
    return decoded;
}

function getCookie(cookie_name) {
    /*
      Shortcut to grab a cookie. Return null if no cookie exists.
     */
    return decode_string_dict(document.cookie)[cookie_name];
}

function go_home() {
    /*
      Load the homepage.
     */
    window.location.href="/";
}

function error(error_message) {
    /*
      Show an error message.

      TODO: Do this at least somewhat gracefully.
     */
    alert("Error: "+error_message);
    go_home();
}

function user_info() {
    // I hate web browsers. There seems to be a more-or-less random addition of quotes
    // around cookies. Really.
    let userinfo = JSON.parse(atob(getCookie("userinfo").replace('"', '').replace('"', '')));
    return userinfo;
}

function authenticated() {
    // Decode user info.
    return user_info() !== null;
}

function authorized() {
    return user_info()['authorized'];
}

function decode_hash() {
    let hash = location.hash;
    if(hash.length === 0) {
	return false;
    } else {
	return decode_string_dict(location.hash.slice(1));
    }
    //console.log("Unrecognized hash");
    return false;
}
