d3.select("#query_button").attr("onclick", "query_dashboard()");

function query_dashboard() {
    console.log("Click");
    dashboard_connection(
	JSON.parse(d3.select("#query_string").property("value")),
	function(data) {
	    console.log(data);
	    d3.select("#query_response").property("value", JSON.stringify(data));
	}
    );
};
