/*
  Main visualization for The Writing Observer

  This is the meat of the system.
*/

var student_data;
var summary_stats;
var tile_template;
var d3;


var first_time = true;

function update_time_idle_data(d3tile, data) {
    /*
      We'd like time idle to proceed smoothly, at 1 second per second,
      regardless of server latency.

      When the server updates idle time, we update data attributes
      associated with the element, if necessary. We do this here. Then,
      we use an interval timer to update the display itself based on
      client-side timing.

      We maintain data fields for:

      * Last access
      * Server and client time stamps at last access

      When new data comes in, we /only/ update if last access
      changed. Otherwise, we compute.
    */

    /* Old data */
    let serverside_update_time = d3.select(d3tile).attr("data-ssut");
    let clientside_time = (new Date()).getTime() / 1000;
    let new_serverside_update_time = Math.round(data['writing_observer.writing_analysis.time_on_task']['saved_ts']);

    if(new_serverside_update_time == Math.round(serverside_update_time)) {
	// Time didn't change. Do nothing! Continue using the client clock
	return;
    }

    d3.select(d3tile).attr("data-ssut", summary_stats["current-time"]);
    d3.select(d3tile).attr("data-sslat", data['writing_observer.writing_analysis.time_on_task']['saved_ts']);
    d3.select(d3tile).attr("data-csut", clientside_time);
}

function update_time_idle() {
    /*
      TODO: We should call this once per second to update time idle. Right now, we're calling this from `populate_tiles`

      The logic is described in update_time_idle_data().
     */
    var tiles = d3.selectAll("div.wo-col-tile").each(function(d) {
	let serverside_update_time = d3.select(this).attr("data-ssut");
	let ss_last_access = d3.select(this).attr("data-sslat");
	let clientside_update_time = d3.select(this).attr("data-csut");
	let clientside_time = (new Date()).getTime() / 1000;
	/* Time idle is computed as: */
	let idle_time = (serverside_update_time - ss_last_access) + (clientside_time - clientside_update_time);
	/*              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
			How long student was idle when we               How long ago we were told
			last learned their last access time
	*/
	// 0, -1, etc. indicate no data
	console.log(serverside_update_time , ss_last_access, clientside_time , clientside_update_time);
	console.log((serverside_update_time - ss_last_access), (clientside_time - clientside_update_time), 1)
	console.log(idle_time);
	if(ss_last_access < 1000000000) {
	    d3.select(this).select(".wo-tile-idle-time").select("span").text("N/A");
	} else {
	    d3.select(this).select(".wo-tile-idle-time").select("span").text(rendertime2(idle_time));
	}
    });
}

function populate_tiles(tilesheet) {
    /* Create rows for students */
    console.log("Populating data");
    console.log(student_data);
    if(first_time) {
	var rows=tilesheet.selectAll("div.wo-row-tile")
	    .data(student_data)
	    .enter()
	    .append("div")
	    .attr("class", "tile is-ancestor wo-row-tile");

	/* Create individual tiles */
	var cols=rows.selectAll("div.wo-col-tile")
	    .data(function(d) { return d; })  // Propagate data down from the row into the elements
	    .enter()
	    .append("div")
	    .attr("class", "tile is-parent wo-col-tile wo-flip-container is-3")
	    .html(tile_template)
	    .each(function(d) {
		d3.select(this).select(".wo-tile-name").text(d.profile.name.fullName);
		var photoUrl = d.profile.photoUrl;
		if(photoUrl.startsWith("//")) {
		    photoUrl = "https:"+d.profile.photoUrl;
		}
		d3.select(this).select(".wo-tile-photo").attr("src", d.profile.photoUrl);
		d3.select(this).select(".wo-tile-email").attr("href", "mailto:"+d.profile.emailAddress);
		d3.select(this).select(".wo-tile-phone").attr("href", "");          // TODO
	    });
	first_time = false;
    }
    else {
	var rows=tilesheet.selectAll("div.wo-row-tile")
	    .data(student_data)
	var cols=rows.selectAll("div.wo-col-tile")
	    .data(function(d) { return d; })  // Propagate data down from the row into the elements
    }
    /* Populate them with data */
    var cols_update=rows.selectAll("div.wo-col-tile")
	.data(function(d) { console.log(d); return d; })
    	.each(function(d) {
	    console.log(d.profile);
	    // Profile: Student name, photo, Google doc, phone number, email
	    d3.select(this).select(".wo-tile-doc").attr("href", "");            // TODO
	    // Summary stats: Time on task, time idle, and characters in doc
	    let compiled = d["writing-observer-compiled"];
	    let text = compiled.text;
	    d3.select(this).select(".wo-tile-character-count").select("span").text(compiled["character-count"]);
	    //d3.select(this).select(".wo-tile-character-count").select("rect").attr("width", 15);
	    let tot = d["writing_observer.writing_analysis.time_on_task"];
	    d3.select(this).select(".wo-tile-time-on-task").select("span").text(rendertime2(tot["total-time-on-task"]));
	    //d3.select(this).select(".wo-tile-time-on-task").select("rect").attr("width", 15);
	    d3.select(this).select(".wo-tile-idle-time").select("span").text("Hello");

	    //d3.select(this).select(".wo-tile-idle-time").select("rect").attr("width", 15);
	    update_time_idle_data(this, d);
	    // Text
	    d3.select(this).select(".wo-tile-typing").text(compiled.text);
	});
    update_time_idle();
}

var dashboard_template;
var Mustache;

function initialize(D3, div, course, config) {
    /*
      Populate D3 with the dashboard for the course
    */
    d3=D3;
    console.log(config);

    div.html(dashboard_template);
    dashboard_connection(
	{
	    module: "writing_observer",
	    course: course
	},
	function(data) {
	    console.log("New data!");
	    student_data = data["student-data"];
	    summary_stats = data["summary-stats"];
	    console.log(summary_stats);
	    d3.select(".wo-tile-sheet").call(populate_tiles, student_data);
            d3.selectAll(".wo-loading").classed("is-hidden", true);
	    console.log("Hide labels?");
	    if(config.modules.wobserver['hide-labels']) {
		console.log("Hide labels");
		d3.selectAll(".wo-desc-header").classed("is-hidden", true);
	    }
	});
    /*
    var tabs = ["typing", "deane", "summary", "outline", "timeline", "contact"];
    for(var i=0; i<tabs.length; i++) {
	d3.select(".tilenav-"+tabs[i]).on("click", select_tab(tabs[i]));
    }*/

    this.terminate = function() {
	ws.close();
    }

    return {
	'terminate': this.terminate
    };
}

define([
    requireconfig(),
    requireexternallib("mustache.min.js"),
    requiremoduletext("wo_dashboard.html"),
    requiremoduletext("tile.html"),
],
       function(config, mustache, dashboard, tile) {
	   Mustache = mustache;
	   dashboard_template = dashboard;
	   tile_template = tile;
	   return {
	       "initialize": initialize
	   };
       });
