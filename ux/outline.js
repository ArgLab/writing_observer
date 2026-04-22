const LENGTH = 30;

const width = 960;
const height = 650;
const margin = 5;
const padding = 5;
const adj = 30;

export const name = 'outline';

var test_data = { "outline": [
    { "section": "Problem 1", "length":  300},
    { "section": "Problem 2", "length":   30},
    { "section": "Problem 3", "length":  900},
    { "section": "Problem 4", "length": 1200},
    { "section": "Problem 5", "length":  400}
]};

var maximum = 1500;

export function outline(div, data=test_data) {
    div.html("");
    //div.append("p").text("In progress -- just piping data in")
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

    console.log(data.outline);

    var outline_data = data.outline.reverse();
    const yScale = d3.scaleBand().range([height, 0]).domain(outline_data.map(d=>d['section']));
    const xScale = d3.scaleLinear().range([0, width]).domain([0, 1])

    var normed_x = (x) => x / maximum;

    svg.selectAll(".barRect")
     	.data(outline_data)
     	.enter()
     	.append("rect")
     	.attr("x", (d) => xScale(1-normed_x(d['length'])))
     	.attr("y", function(d) { return yScale(d['section']);})
     	.attr("width", function(d) { return xScale(normed_x(d['length']));})
     	.attr("height", yScale.bandwidth())
     	.attr("fill", "#ccccff");

    svg.selectAll(".barText")
    	.data(outline_data)
    	.enter()
    	.append("text")
    	.attr("x", 0)
    	.attr("y", (d) => yScale(d['section']) + yScale.bandwidth()/2)
    	.attr("font-size", "3.5em")
    	.attr("font-family", 'BlinkMacSystemFont,-apple-system,"Segoe UI",Roboto,Oxygen,Ubuntu,Cantarell,"Fira Sans","Droid Sans","Helvetica Neue",Helvetica,Arial,sans-serif')
    	.text((d) => d['section']);

    return svg;
}

d3.select("#debug_testing_outline").call(outline).call(console.log);
