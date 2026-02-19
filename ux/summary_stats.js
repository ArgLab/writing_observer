const LENGTH = 30;

const width = 960;
const height = 650;
const margin = 5;
const padding = 5;
const adj = 30;

export const name = 'summary_stats';

var bar_names = {
    "speed": "Typing speed",
    "essay_length": "Length",
    "writing_time": "Writing time",
    "text_complexity": "Text complexity",
    "time_idle": "Time idle"
};

var maxima = {
    "ici": 1000,
    "speed": 1300,
    "essay_length": 10000,
    "writing_time": 60,
    "text_complexity": 12,
    "time_idle": 30
}

var test_data = {
    "ici": 729.664923175084,
    "essay_length": 2221,
    "writing_time": 42.05237247614963,
    "text_complexity": 4.002656228025943,
    "time_idle": 0.24548328432300075
};


export function summary_stats(div, data=test_data) {
    div.html("");
    div.append("p").text("In progress -- just piping data in")
    var svg = div.append("svg")
      .attr("preserveAspectRatio", "xMinYMin meet")
      .attr("viewBox", "-"
            + adj + " -"
            + adj + " "
            + (width + adj *3) + " "
            + (height + adj*3))
      .style("padding", padding)
      .style("margin", margin)
      .style("border", "1px solid lightgray")
      .classed("svg-content", true);

    data['speed'] = 60000 / data['ici']
    
    var data_ordered = [
	['essay_length', data['essay_length']],
	['time_idle', data['time_idle']],
	['writing_time', data['writing_time']],
	['text_complexity', data['text_complexity']],
	['speed', data['speed']]
    ].reverse();

    const yScale = d3.scaleBand().range([height, 0]).domain(data_ordered.map(d=>d[0])); //labels);
    const xScale = d3.scaleLinear().range([0, width]).domain([0, 1])

    var y = (d) => data[d];
    var normed_x = (x) => data[x] / maxima[x];

    function rendertime(t) {
	function str(i) {
	    if(i<10) {
		return "0"+String(i);
	    }
	    return String(i)
	}
	var seconds = Math.floor((t - Math.floor(t)) * 60);
	var minutes = Math.floor(t) % 60;
	var hours = Math.floor(t/60) % 60;
	var rendered = str(seconds);
	if (minutes>0 || hours>0) {
	    rendered = str(minutes)+":"+rendered;
	} else {
	    rendered = rendered + " sec";
	}
	if (hours>0) {
	    rendered = str(rendered)+":"+rendered;
	}
	return rendered
    }

    function label(d) {
	var prettyprint = {
	    'essay_length': (d) => String(d) +" characters",
	    'time_idle': rendertime,
	    'writing_time': rendertime,
	    'text_complexity': Math.floor,
	    'speed': (d) => Math.floor(d) + " CPM"
	}
	return bar_names[d[0]] + ": " + prettyprint[d[0]](String(d[1]));
    }

    svg.selectAll(".barRect")
	.data(data_ordered)
	.enter()
	.append("rect")
	.attr("x", xScale(0))
	.attr("y", (d) => yScale(d[0]))
	.attr("width", (d) => xScale(normed_x(d[0])))
	.attr("height", yScale.bandwidth())
	.attr("fill", "#ccccff")

    svg.selectAll(".barText")
	.data(data_ordered)
	.enter()
	.append("text")
	.attr("x", 0)
	.attr("y", (d) => yScale(d[0]) + yScale.bandwidth()/2)
	.attr("font-size", "3.5em")
	.attr("font-family", 'BlinkMacSystemFont,-apple-system,"Segoe UI",Roboto,Oxygen,Ubuntu,Cantarell,"Fira Sans","Droid Sans","Helvetica Neue",Helvetica,Arial,sans-serif')
	.text((d) => label(d))
    ;
    return svg;
}

d3.select("#debug_testing_summary").call(summary_stats).call(console.log);
