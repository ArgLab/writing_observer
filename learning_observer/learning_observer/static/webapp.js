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

function ajax(config)
{
    return function(url) {
	// Do AJAX calls with error handling
	return new Promise(function(resolve, reject) {
	    config.d3.json(url)
		.then(function(data){
		    resolve(data);
		})
		.catch(function(data){
		    reject(data);
		});
	});
    }
}

function initializeBurgerMenu() {
    document.querySelectorAll('.navbar-burger').forEach(burger => {
        burger.addEventListener('click', () => {
            const target = burger.dataset.target;
            const targetMenu = document.getElementById(target);
            burger.classList.toggle('is-active');
            targetMenu.classList.toggle('is-active');
        });
    });
}



requirejs(
    // TODO: Clean up absolute paths. We hardcoded these for now, due to refactor.
    ["/static/3rd_party/text.js!/config.json",
     "/static/3rd_party/text.js!/webapi/course_dashboards",  // Perhaps this belongs in config.json?
     "/static/3rd_party/d3.v5.min.js",
     "/static/3rd_party/mustache.min.js",
     "/static/3rd_party/showdown.js",
     "/static/3rd_party/fontawesome.js",
     "/static/3rd_party/text.js!/static/modules/unauth.md",
     "/static/3rd_party/text.js!/static/modules/login.html",
     "/static/3rd_party/text.js!/static/modules/courses.html",
     "/static/3rd_party/text.js!/static/modules/course.html",
     "/static/3rd_party/text.js!/static/modules/tool.html",
     "/static/3rd_party/text.js!/static/modules/navbar_loggedin.html",
     "/static/3rd_party/text.js!/static/modules/informational.html",
	 "/static/3rd_party/text.js!/auth/userinfo"
    ],
    function(config, tool_list, d3, mustache, showdown, fontawesome, unauth, login, courses, course, tool, navbar_li, info, auth_info) {
	// Parse client configuration.
	config = JSON.parse(config);
	// console.log(tool_list);
	tool_list = JSON.parse(tool_list);
	// console.log(tool_list);
	// console.log(auth_info);
	// console.log(JSON.stringify(auth_info));

	// Add libraries
	config.d3 = d3;
	config.ajax = ajax(config);
	auth_info = JSON.parse(auth_info);

	// Reload user info
	function reload_user_info() {
		config.ajax("/auth/userinfo")
		.then(function(data) {
		    auth_info = data;
		    console.log(auth_info);
		    console.log(JSON.stringify(auth_info));
		    console.log("reloaded user info");
		});
		console.log(auth_info);
	}


	function password_authorize() {
	    d3.json("/auth/login/password", {
		method: 'POST',
		headers: {
		    "Content-type": "application/json; charset=UTF-8"
		},
		body: JSON.stringify({
		    username: d3.select(".lo-login-username").property("value"),
		    password: d3.select(".lo-login-password").property("value")
		})
	    }).then(function(data) {
			reload_user_info();
			if (data['status'] === 'authorized') {
			    load_courses_page();
			} else if (data['status'] === 'unauthorized') {
		    	// TODO: Flash a nice subtle message
			    alert("Invalid username or password!");
			}
			else {
		    	console.log(data);
			}
	    });
	}

	function load_login_page() {
	    d3.select(".main-page").html(mustache.render(login, config['theme']));
	    d3.select(".lo-google-auth").classed("is-hidden", !config['google_oauth']);
	    d3.select(".lo-http-auth").classed("is-hidden", !config['http_basic_auth']);
	    d3.select(".lo-password-auth").classed("is-hidden", !config['password_auth']);
		d3.select('.lo-google-auth p a').attr('href', function () {
			const currentHref = d3.select(this).attr('href');
			if (!currentHref) { return null; }
			return currentHref + window.location.search + window.location.hash;
		});
	    d3.select(".lo-login-button")
		.on("click", function() {
		    password_authorize();
		});
	}

	function load_courses_page() {
	    /*
	      Listing of Google Classroom courses
	      */
	    d3.select(".main-page").html(courses);
	    config.ajax("/webapi/courselist/").then(function(data){
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
		    cdg.selectAll("div.awd-course-card")
				.data(data)
				.enter()
				.append("div")
				.html(function(course_json) {
			    	console.log(course_json);
			    	let tools = "";
			    	for(var i=0; i<tool_list.length; i++) {
					// Computer icon CSS class
						tool_list[i]["icon_class"] = tool_list[i].icon.type +
				    		" " +
				    		tool_list[i].icon.icon;
						// This does a union.
						// * tool_list[i] are the tool properties
						// * course_json are the course properties
						// Merged, we can render tools for courses!
						joined = Object.assign({}, course_json, tool_list[i]);
					// console.log(joined);
					tools += mustache.render(tool, joined);
			    }
			    course_json['tools'] = tools;
			    return mustache.render(course, course_json);
			});
			loggedin_navbar_menu();
		}
	    });
	}

	function load_dashboard_page(course) {
	    /*
	      Classroom writing dashboard
	     */
	    console.log(wobserver);
	    d3.select(".main-page").text("Loading Writing Observer...");
	    wobserver.initialize(d3, d3.select(".main-page"), course);
	}

	function load_unauthorized_page() {
	    /*
	      If an unauthenticated teacher logs in, we will show this
	      page.
	    */
	    sd = new showdown.Converter();
	    bodytext = sd.makeHtml(mustache.render(unauth, user_info()));
	    d3.select(".main-page").html(
		mustache.render(info,
				{text:bodytext}));

	}

	function user_info() {
		return auth_info;
		/*try {
		    let userinfo = JSON.parse(atob(getCookie("userinfo").replace('"', '').replace('"', '')));
		    //console.log(userinfo);
	    	return userinfo;
		}
		catch(err) {
		    return {};
		}*/
	}

	function authenticated() {
	    // Decode user info.
	    // I hate web browsers. There seems to be a more-or-less random addition of quotes
	    // around cookies. Really.
		const ui = user_info();
		if(ui == null || Object.keys(ui).length == 0) {
			return false;
		}
		console.log(ui);
	    return true;
	}

	function authorized() {
	    return user_info()['authorized'] == true;
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

	function loggedin_navbar_menu() {
		const navbarMenu = d3.select("#mainNavbar");
		const navbarBurger = d3.select(".navbar-burger");

		navbarMenu.html(mustache.render(navbar_li, {
			'user_name': user_info()['name'],
			'user_picture': user_info()['picture']
		}));
		navbarMenu.classed("is-hidden", false);
		navbarBurger.classed("is-hidden", false);
		initializeBurgerMenu();
	}

	function setup_page() {
	    const hash_dict = decode_hash();
	    if(!authenticated()) {
			//console.log("Login page");
		load_login_page();
	    } else if(!authorized()) {
			load_unauthorized_page();
	    }
	    else if(!hash_dict) {
		//console.log("Courses page");
			load_courses_page();
	    } else {
		error("Invalid URL");
	    }
	}

	window.addEventListener('hashchange', function(){
	    setup_page();
	});

	setup_page()
    }
);
