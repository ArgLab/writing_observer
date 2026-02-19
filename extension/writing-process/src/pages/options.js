/*
  Documentation on how to create an options page

  TODO: Add logging of when options change
 */

const option_keys = ["teacher_tag", "user_tag", "process_server", "unique_id"];

function saveOptions(key) {
    /*
      Callback when user hits "save" on the options page

      We save to storage. When we're done, we refresh the
      text (and the input) to make sure we've saved right and
      to show current status.
    */
    const value = document.querySelector("input.input-text."+key).value;
    let new_setting={};
    new_setting[key] = value;
    chrome.storage.sync.set(
	new_setting,
	(e)=>restoreOptions([key])
    );
}

function removeOptions(key) {
    /*
      Callback when user hits "remove" on the options page

      We just remove they key.
    */
    chrome.storage.sync.remove(
	key,
	(e)=>restoreOptions([key])
    );
}

function restoreOptions(keys = option_keys) {
    /*
      Initialize the options page for the extension. Eventually, we'd
      like to also use chrome.storage.managed so that school admins 
      can set these settings up centrally, without student overrides
    */
    chrome.storage.sync.get(keys, function(result){
	for(const key_index in keys) {
	    const key = keys[key_index];
	    console.log(key);
	    const r=result[key] || "none";
	    console.log(r);
	    document.querySelector(".value-display."+key).innerText = r;
	    document.querySelector("input."+key).value = r;
	}
    });
}

function initialize() {
    for(const key_index in option_keys) {
	const key = option_keys[key_index];
	console.log(key);
	document.querySelector("button.save-button."+key)
	    .addEventListener("click", (e) => saveOptions(key));
	document.querySelector("button.remove-button."+key)
	    .addEventListener("click", (e) => removeOptions(key));
    }
    restoreOptions(option_keys);
}

document.addEventListener('DOMContentLoaded', initialize);

