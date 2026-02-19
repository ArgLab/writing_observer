import { deane_graph } from './deane.js'
import { typing } from './typing.js'
import { summary_stats } from './summary_stats.js'
import { outline } from './outline.js'

var student_data = [[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16],[17,18,19]];

const tile_template = document.getElementById('template-tile').innerHTML

function populate_tiles(tilesheet) {
    var rows=tilesheet.selectAll("div.wa-row-tile")
	.data(student_data)
	.enter()
	.append("div")
	.attr("class", "tile is-ancestor wa-row-tile");

    var cols=rows.selectAll("div.wa-col-tile")
	.data(function(d) { return d; })
	.enter()
	.append("div")
	.attr("class", "tile is-parent wa-col-tile wa-flip-container is-3")
	.html(function(d) {
	    return Mustache.render(tile_template, d);
	    /*{
		name: d.name,
		body: document.getElementById('template-deane-tile').innerHTML
	    });*/
	})
	.each(function(d) {
	    d3.select(this).select(".typing-text").call(typing, d.ici, d.essay);
	})
	.each(function(d) {
	    d3.select(this).select(".deane").call(deane_graph);
	})
	.each(function(d) {
	    d3.select(this).select(".summary").call(summary_stats, d);
	})
	.each(function(d) {
	    d3.select(this).select(".outline").call(outline, d);
	});
}

function select_tab(tab) {
    return function() {
	d3.selectAll(".tilenav").classed("is-active", false);
	d3.selectAll(".tilenav-"+tab).classed("is-active", true);
	d3.selectAll(".wa-tilebody").classed("is-hidden", true);
	d3.selectAll("."+tab).classed("is-hidden", false);
    }
};

var tabs = ["typing", "deane", "summary", "outline", "timeline", "contact"];
for(var i=0; i<tabs.length; i++) {
    d3.select(".tilenav-"+tabs[i]).on("click", select_tab(tabs[i]));
}

d3.json("api/student_data.js").then(function(data) {
    student_data = data;
    console.log("Loaded");
    d3.select(".wa-tile-sheet").html("");
    d3.select(".wa-tile-sheet").call(populate_tiles);
});
