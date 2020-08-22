function getCookie(cname) {
  var name = cname + "=";
  var decodedCookie = decodeURIComponent(document.cookie);
  var ca = decodedCookie.split(';');
  for(var i = 0; i <ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
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

requirejs(
    ["/static/3rd_party/d3.v5.min.js",
     "/static/3rd_party/mustache.min.js",
     "/static/3rd_party/showdown.js",
     "/static/3rd_party/fontawesome.js",
     "3rd_party/text!/static/modules/unauth.md",
     "3rd_party/text!/static/modules/login.html",
     "3rd_party/text!/static/modules/courses.html",
     "3rd_party/text!/static/modules/course.html",     
     "3rd_party/text!/static/modules/navbar_loggedin.html",     
    ],
    function(d3, mustache, showdown, fontawesome, unauth, login, courses, course, navbar_li) {
	function load_login_page() {
	    d3.select(".main-page").html(login);
	}

	function load_courses_page() {
	    d3.select(".main-page").html(courses);
	    d3.json("/webapi/courselist/").then(function(data){
		/*
		  TODO: We want a function which does this abstracted
		  our. In essense, we want to call
		  d3.json_with_auth_and_errors
		*/
		if(data["error"]!=null) {
		    if(data["error"]["status"]==="UNAUTHENTICATED") {
			load_login_page();
		    }
		    else {
			error("Unknown error!");
		    }
		} else {
		    let cdg = d3.select(".awd-course-list");
		    console.log(cdg);
		    console.log(data)
		    cdg.selectAll("div.awd-course-card")
			.data(data)
			.enter()
			.append("div")
			.html(function(d) {
			    return mustache.render(course, d);
			});
		}
	    });
	}

	function load_dashboard_page(course) {
	    d3.select(".main-page").text("dashboard");
	}

	function user_info() {
	    let userinfo = JSON.parse(atob(getCookie("userinfo").replace('"', '').replace('"', '')));
	    //console.log(userinfo);
	    return userinfo;
	}

	function authenticated() {
	    // Decode user info.
	    // I hate web browsers. There seems to be a more-or-less random addition of quotes
	    // around cookies. Really.
	    return user_info() !== null;
	}

	function course_hash() {
	    let hash = location.hash;
	    if(hash.length === 0) {
		return false;
	    }
	    if(hash.startsWith("#wd_course=")) {
		return hash.slice(8);
	    }
	    //console.log("Unrecognized hash");
	    return false;
	}

	function loggedin_navbar_menu() {
	    d3.select(".main-navbar-menu").html(mustache.render(navbar_li, {
		'user_name': user_info()['name'],
		'user_picture': user_info()['picture']
	    }));
	}

	function setup_page() {
	    if(!authenticated()) {
		//console.log("Login page");
		load_login_page();
	    } else if(!course_hash()) {
		//console.log("Courses page");
		load_courses_page(course_hash());
		loggedin_navbar_menu()
	    } else {
		load_dashboard_page(course_hash());
		loggedin_navbar_menu()
	    }
	}

	window.addEventListener('hashchange', function(){
	    setup_page();
	});

	setup_page()
    }
);
