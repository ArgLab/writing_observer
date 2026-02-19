export const name = 'typing';

const SAMPLE_TEXT = "I like the goals of this petition and the bills, but as drafted, these bills just don't add up. We want to put our economy on hold. We definitely need a rent freeze. For that to work, we also need a mortgage freeze, not a mortgage forbearance. The difference is that in a mortgage forbearance, interest adds up and at the end, your principal is higher than when you started. In a mortgage freeze, the principal doesn't change -- you just literally push back all payments by a few months.";

export function typing(div, ici=200, text=SAMPLE_TEXT) {
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

    function sample_ici(typing_delay=200) {
	/* 
	   Intercharacter interval -- how long between two keypresses
	   
	   We do an approximate Gaussian distribution around the 
	*/
	return typing_delay * randn_bm() * 2;
    }

    var start = 0;
    var stop = 1;
    const MAXIMUM_LENGTH = 250;

    function updateText() {
	//document.getElementsByClassName("typing")[0].innerText=text.substr(start, stop-start);
	div.text(text.substr(start, stop-start));
	stop = stop + 1;
	
	if(stop > text.length) {
	    stop = 1;
	    start = 0;
	}
    
	start = Math.max(start, stop-MAXIMUM_LENGTH);
	while((text[start] != ' ') && (start>0) && (start<text.length) ) {
	    start++;
	}
	if(start>stop) {
	    start=stop;
	}

	if(div.size() > 0) {
	    setTimeout(updateText, sample_ici(ici));
	};
    }
    setTimeout(updateText, sample_ici(50));
};

//typing();

d3.select(".typingdebug-typing").call(typing);

