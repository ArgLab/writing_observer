const width = 960;  // svg width
const height = 500; // svg height
const margin = 5;   // svg margin
const padding = 5;  // svg padding
const adj = 30;

/*-------------------------*\
*                           *
| Generic utility functions |
| for testing and debugging |
*                           *
\*-------------------------*/


function consecutive_array(n) {
    /* 
       This creates an array of length n [0,1,2,3,4...n] 
     */
    return Array(n).fill().map((e,i)=>i+1);
};

function zip(a1, a2) {
    /*
      Clone of Python's zip.
      [[1,1],[2,3],[4,5]] => [[1,2,4],[1,3,5]]
     */
    return a1.map(function(e, i) {
	return [e, a2[i]];
    });
}



/*-------------------------*\
*                           *
|     Deane graph code      |
*                           *
\*-------------------------*/

export const name = 'deane3';

const LENGTH = 30;

function dummy_data(length) {
    /*
      Create sample data for a Deane graph. This is basically a random
      upwards-facing line for the length, with the cursor somewhere
      in between. Totally non-realistic.
    */
    function randn_bm() {
	/* Approximately Gaussian distribution, mean 0.5
	   From https://stackoverflow.com/questions/25582882/javascript-math-random-normal-distribution-gaussian-bell-curve */
	let u = 0, v = 0;
	while(u === 0) u = Math.random(); //Converting [0,1) to (0,1)
	while(v === 0) v = Math.random();
	let num = Math.sqrt( -2.0 * Math.log( u ) ) * Math.cos( 2.0 * Math.PI * v );
	num = num / 10.0 + 0.5; // Translate to 0 -> 1
	if (num > 1 || num < 0) return randn_bm(); // resample between 0 and 1
	return num;
    }


    function length_array(x) {
	/*
	  Essay length
	*/
	return x.map((e,i)=> (e*randn_bm(e) + e)/2);
    }

    function cursor_array(x) {
	/*
	  Essay cursor position
	*/
	var length_array = x.map((e,i)=> (e*Math.random()/2 + e*randn_bm()/2));
	return length_array;
    }

    var x_edit = consecutive_array(length);  // edit number, for X axis
    var y_length = length_array(x_edit);     // total essay length
    var y_cursor = cursor_array(y_length);   // cursor position
    return {
	'cursor': y_cursor,
	'length': y_length
    };
};


export function setup_deane_graph(div) {
    /*
      Create UX elements, without data
     */
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

    // Line graph for essay length
    svg.append('g')
	.append('path')
	.attr('class', 'essay-length-lines')
	.attr('fill', 'none')
	.attr('stroke', 'black')
	.attr('stroke-width','2');

    // Line graph for cursor position
    svg.append('g')
	.append('path')
	.attr('class', 'essay-cursor-lines')
	.attr('fill', 'none')
	.attr('stroke', 'blue')
	.attr('stroke-width','3');

    // Add x-axis
    svg.append('g')              // create a <g> element
	.attr("transform", "translate(0, "+height+")")
	.attr('class', 'x-axis'); // specify classes

    // Add y-axis
    svg.append('g')              // create a <g> element
	.attr('class', 'y-axis') // specify classes
    return svg;
};

export function populate_deane_graph_data(div, data, max_x=null, max_y=null) {
    var svg = div.select('svg');
    if(max_x === null) {
	max_x = data['length'].length;
    }
    if(max_y === null) {
	max_y = Math.max(...data['length']);
    }

    const yScale = d3.scaleLinear().range([height, 0]).domain([0, max_y])
    const xScale = d3.scaleLinear().range([0, width]).domain([0, max_x])

    var lines = d3.line();

    var x_edit = consecutive_array(data['length'].length);

    var length_data = zip(x_edit.map(xScale), data['length'].map(yScale));
    var cursor_data = zip(x_edit.map(xScale), data['cursor'].map(yScale));
    
    var pathData = lines(length_data);
    svg.select('.essay-length-lines')
    	.attr('d', pathData);

    pathData = lines(cursor_data);
    svg.select('.essay-cursor-lines')
	.attr('d', pathData)

    var xAxis = d3.axisBottom()
	.ticks(4) // specify the number of ticks
	.scale(xScale);
    var yAxis = d3.axisLeft()
	.ticks(4)
	.scale(yScale); // specify the number of ticks

    svg.select('.x-axis')
	.call(xAxis);            // let the axis do its thing

    svg.select('.y-axis')
	.call(yAxis);            // let the axis do its thing

}

export function deane_graph(div) {
    var svg = setup_deane_graph(div);

    var data = dummy_data(LENGTH);

    var y_length = data['length'];
    var y_cursor = data['cursor'];

    populate_deane_graph_data(div, data);
    return svg;
}

d3.select("#debug_testing_deane").call(deane_graph);
