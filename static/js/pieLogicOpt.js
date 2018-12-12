/*
- starting parameters: empirically derived (Jira tickets, PRT, ...)
- employee ID = username; project ID = PRT number
- possible "modes" of the game: 
	1. emphasize existing resources (be conservative in adding new team members)
	2. ?
- set employee roles (project lead, technical lead)
- if needed, add new employees to project based on skills and budget
*/



function getInitData() {
	return init;
}

var initData = getInitData();


// Employee and project data
const employees = [
	{
		name: "John Developer",
		username: "develop.joh",
		skills: ["JavaScript", "C++"],
		seniority: 2,
		costPerDayZscore: 2.5,
		color: "#1f77b4"
	},
	{
		name: "Jane Consultant",
		username: "consult.jan",
		skills: ["Atlassian", "Project management"],
		seniority: 1,
		costPerDayZscore: 0.6,
		color: "#ff7f0e"
	},
	{
		name: "Jill Workingstudent",
		username: "workstu.jil",
		skills: ["Design"],
		seniority: 0,
		costPerDayZscore: -1.9,
		color: "#2ca02c"
	},
	{
		name: "Judy Backender",
		username: "backend.jud",
		skills: ["php", "SQL"],
		seniority: 1,
		costPerDayZscore: 1.1,
		color: "#d62728"
	}
];

const projects = [
	{
		name: "MeeIntranet",
		prtID: "0449",
		skills: ["Atlassian"],
		budget: 1000,
		PT: 100,
		members: ["consult.jan", "workstu.jil", "backend.jud"],
		lead: ["consult.jan"]
	},
	{
		name: "RD/IM",
		prtID: "0584",
		skills: ["Atlassian", "JavaScript"],
		budget: 2000,
		PT: 40,
		members: ["develop.joh", "consult.jan", "backend.jud"],
		lead: ["consult.jan"]
	},
	{
		name: "PRT",
		prtID: "9999",
		skills: ["JavaScript", "php", "SQL"],
		budget: 800,
		PT: 70,
		members: ["develop.joh", "backend.jud"],
		lead: ["develop.joh"]
	}
];


// -----------------------------------------------------------------------------------------------------------------------------------------------
// Set data variables
var projEmplMap = createProjEmplMap(initData);
var projEmplMap_original = createProjEmplMap(initData);

var numEmpl = employees.length,
	numProj = projects.length,
	projIDs = Array.from( projEmplMap.keys() );

// Initialize variables for current selections
var oldValues = [],
    currentProj = "",
    currentEmpl = "",
    delta = 0; // change in employee data effected by a slider


// -----------------------------------------------------------------------------------------------------------------------------------------------
// Initialize pie charts

var m = 10,
    r = 50,
    mycolors = function(empl) { return getEmplObj(empl).color; };
   
  	
var arc = d3.svg.arc()
      .innerRadius(r / 2)    
      .outerRadius(r);

var pie = d3.layout.pie()
    .value(function(d) { return d; })
    .sort(null);  

var svg = d3.select("#pies").selectAll("svg")
    .data(makeDataMatrix())
    // .data(initData)
  .enter()
    .append("svg")
    .attr("width", (r + m) * 2)
    .attr("height", (r + m) * 2)
    .attr("id", function(d,i) { return 'pie' + i; })
    .attr("data-id", function(d,i) { return projIDs[i]; })
    .append("svg:g")
      .attr("transform", "translate(" + (r + m) + "," + (r + m) + ")");

var path = svg.selectAll("path")
    .data(pie)
  .enter()
    .append("svg:path")
    .attr("d", arc)
    .style("fill", function(d, i) {
    		var currPie = d3.select(this.parentNode.parentNode).attr("data-id");
    		var empl = Array.from ( projEmplMap.get(currPie).keys() );
    		return mycolors(empl[i]);
    	})
        .each(function(d) { this._current = d; }); // store the initial angles

var titles = svg.append("svg:text") 
  .attr("class", "title") 
  .text(function(d,i) { return projects[i].name; }) 
  .attr("dy", "5px")  
  .attr("text-anchor", "middle")
  
// When clicking on a pie chart, make its sliders appear
d3.selectAll('svg').on('click', function() {
  // Draw border around selected pie chart
  d3.selectAll("svg").attr("style", "");
  d3.select(this).attr("style", "border: 1px solid black;");
  // Create sliders
  currentProj = d3.select(this).attr('data-id');
  oldValues = getProjectData(projEmplMap, currentProj);
  createSliderTable();
  // printEmployeeTable();
});


// -----------------------------------------------------------------------------------------------------------------------------------------------
function createProjEmplMap(data) {
	/*
		"projEmplMap": map where keys are project names, values are themselves maps with employees as keys and PTs as values.
		The goal is to feed the pie chart functions an iterable data structure for easy access (rather than bulky arrays of objects).
	*/
	var projEmplMap = new Map();
	var empls = [];
	for ( var p of data ) {
		projEmplMap.set( Object.keys(p)[0], new Map() );
		empls = Object.entries( Object.entries(p)[0][1] );
		for ( var m of empls ) {
			projEmplMap.get( Object.keys(p)[0] ).set( m[0], m[1] );
		}
	}
	console.log(projEmplMap)
	return projEmplMap;
}


function updatePies() {
  var i = 0;
  projEmplMap.forEach( function(val, key) {
  	var arrValues = Array.from( val.values() );
    var npath = d3.select("#pie" + i).selectAll("path").data( pie(arrValues) );
    npath.transition().duration(200).attrTween("d", arcTween); // redraw the arcs
    i++;
  })
}

function updateSliders() {
  // Update sliders
  d3.selectAll('.range').each(function(d, i) {
    d3.select(this).attr('value', "" + Math.round(oldValues[i]));
  });
  // Update slider values labels
  d3.selectAll('.range_value').each(function(d, i) {
    d3.select(this).text( Math.round(oldValues[i]) );
  });
}


function updateEmplInProj(empl, proj, PT) {
	// "empl" is an employee username, "proj" is a project's PRT number
	var projMap = projEmplMap.get(proj);
	if ( PT === 0 ) {
		projMap.delete(empl);
	} else {
		projMap.set(empl, PT);
	}
}


function getMaxPTForProj(proj) {
	// totalPT - degrees of freedom
	return getProjObj(proj).PT - (projEmplMap.get(proj).size - 1);
}


function createSliderTable() {
	var i = 0;
	d3.select('#rangebox tbody').html('');
	for ( var [emplName, emplData] of projEmplMap.get(currentProj).entries() ) {
	var tr = d3.select('#rangebox tbody').append('tr');
  // Append delete buttons
  tr.append('td')
  	.append('button')
    	.attr('type', 'button')
      .text('-');
	// Append employee labels
	tr.append('td')
	  .attr('class', 'edit')
	  .attr('bgcolor', mycolors(emplName))
	  .text(emplName);
	// Append sliders  
	tr.append('td')
	  // .append('form')
	  // 	.attr('id', 'range_form_' + i)
	  // 	.attr('action', '/slide_data')
	  // 	.attr('method', 'POST')
	  .append('input')
	  .attr('class', 'range')
	  .attr('type', 'range')
	  .attr('data-id', emplName)
	  .attr('step', 1)
	  .attr('min', 1)
	  .attr('max', getMaxPTForProj(currentProj))
	  .attr('value', emplData);
	// Append slider values
	tr.append('td')
	  .attr('class', 'range_value')
	  .text( Math.round(emplData) );
	i++;
	}
  	// When one slider is changed, update pie charts and other sliders
    moveSlider();
}


function map2json(map) {
	
}


function moveSlider() {
	d3.selectAll('.range').on('input', function() {
		var newVal, oldVal;
		newVal = parseInt(this.value);
		currentEmpl = d3.select(this).attr('data-id');
		oldVal = projEmplMap.get(currentProj).get(currentEmpl);
		
		delta = newVal - oldVal;

		console.log(currentEmpl)
		console.log("new_val=" + newVal + ", old_val=" + oldVal)

		if ( delta ) {
			// projEmplMap = slideData();
			projEmplMap.get(currentProj).set(currentEmpl, newVal);

			// Create output JSON object for POST request data
			var jsonOut, idx_proj, idx_empl;
			idx_empl = [...projEmplMap.get(currentProj).keys()].indexOf(currentEmpl);
			idx_proj = [...projEmplMap.keys()].indexOf(currentProj);

			jsonOut = {
				idx_selected: [idx_empl, idx_proj],
				arrNew: makeDataMatrix()
			};

			// POST request
		    $.ajax({
		      url: "/slide_data",
		      type: "post",
		      data: JSON.stringify( jsonOut ),
		      contentType: "application/json",
        	  dataType: 'json',
		      success: function(response) {
		      	console.log("Success!");
        		projEmplMap = createProjEmplMap(response);
				oldValues = getProjectData(projEmplMap, currentProj);
				updatePies();
				updateSliders();
				// printEmployeeTable()
				setStatusMsg();
		      },
		      error: function(xhr) {
		      	$("#req-res").html("Could not retrieve response!")
		      	console.log("Error in POST request!")
		      }
		    });
		}
	});
}

function setStatusMsg() {
	var statusMsgStr, statusMsgColor;
	if ( !(isWithinBudget(projEmplMap, currentProj)) ) {
		statusMsgStr = "Budget Exceeded!";
		statusMsgColor = "red";
	} else {
		statusMsgStr = "Within Budget";
		statusMsgColor = "green";
	}
	$( "#status-msg" ).html(`<p>${getProjObj(currentProj).name}: <span>${statusMsgStr}</span></p>`);
	$( "#status-msg span" ).css("color", statusMsgColor);
}

function filterMapByValue(map, func) {
	for ( var [key, val] of map.entries() ) {
		if ( !(func(val)) ) { map.delete(key); }
	}
	return map;
}

function slideData() {
	var temp = new Map(projEmplMap),
		compensatorEmpl = "",
		compensatorProj = "",
		excludedEmpl = [];
		excludedProj = [];
		exclEmpl = [],
		exclProj = [],
		isValid = undefined,
		unitIncr = Math.sign(delta);
		recursDepth = 0;

	// Simulate consequences of increment using temporary map
	for ( var i = 0; i < Math.abs(delta); i++ ) {
		recursDepth = 0;
		exclEmpl = [currentEmpl];
		exclProj = [currentProj];
		// Change current employee in current project
		isValid = addDelta(currentEmpl, currentProj, unitIncr);
		if ( !(isValid) ) { 
			addDelta(currentEmpl, currentProj, -unitIncr);
			break;
		}
		doUnitSlide(currentEmpl, currentProj, unitIncr);
	}
	return temp;

	
	function doUnitSlide(currentEmpl, currentProj, unitIncr) {
		recursDepth++;
		console.log(`${recursDepth} - ${currentEmpl}, ${getProjObj(currentProj).name}`);
		excludedEmpl = [];
		excludedProj = [];

		excludedEmpl = excludedEmpl.concat(exclEmpl);
		excludedProj = excludedProj.concat(exclProj);

		isValid = undefined;
		//if ( recursDepth !== 2 ) {
		if ( sum(Array.from(temp.get(currentProj).values())) !==
			sum(Array.from(projEmplMap_original.get(currentProj).values())) ) {
		// Re-scale another employee in current project
		while ( !(isValid) && [...new Set(excludedEmpl)].length < temp.get(currentProj).size )  {
			console.log(excludedEmpl);
			compensatorEmpl = getCompensatorEmpl(currentEmpl, currentProj, unitIncr);
			console.log("compensatorEmpl = " + compensatorEmpl)
			if ( compensatorEmpl ) {
				excludedEmpl.push(compensatorEmpl);
				isValid = addDelta(compensatorEmpl, currentProj, -unitIncr);
			} else { break; }
		}
		// If no valid compensEmpl found, undo move for (currEmpl,currProj)
		if ( !(isValid) ) {
			addDelta(currentEmpl, currentProj, -unitIncr);
			console.log("! Undid user input move !")
			i = Math.abs(delta);
			return isValid;
		}
	}

		// Re-scale current employee in other projects
		isValid = undefined;
		while ( !(isValid) && [...new Set(excludedProj)].length < temp.size )  {
			console.log(excludedProj);
			compensatorProj = getCompensatorProj(currentEmpl, currentProj, unitIncr);
			console.log("compensatorProj = " + compensatorProj)
			if ( compensatorProj ) {
				excludedProj.push(compensatorProj);
				isValid = addDelta(currentEmpl, compensatorProj, -unitIncr);
			} else { break; }
		}
		// If no valid compensProj found, undo move for (currEmpl,currProj)
		// 	AND for (compensEmpl,currProj)
		if ( !(isValid) ) {
			addDelta(compensatorEmpl, currentProj, unitIncr);
			addDelta(currentEmpl, currentProj, -unitIncr);
			console.log("! Undid user input move and fEmpl !")
			i = Math.abs(delta);
			return isValid;
		}

		// Run function recursively on other changed employees and projects
		//exclEmpl.push(compensatorEmpl);
		//exclProj.push(compensatorProj);
		if ( recursDepth < 10 ) {
		if ( sum(Array.from(temp.get(currentProj).values())) !==
			sum(Array.from(projEmplMap_original.get(currentProj).values())) ) {
			console.log("*** Recursing into fEmpl");
			doUnitSlide(compensatorEmpl, currentProj, -unitIncr);
		}
		if ( sum(Array.from(temp.get(compensatorProj).values())) !==
			sum(Array.from(projEmplMap_original.get(compensatorProj).values())) ) {
			console.log("*** Recursing into fProj");
			doUnitSlide(currentEmpl, compensatorProj, -unitIncr);
		}
		}	
		
		isValid = true;
		return isValid;
	}

	function isAllowed(empl, proj, delta) {
		if ( empl && proj ) {
			var oldVal = temp.get(proj).get(empl);
			var newVal = oldVal + delta;
			if ( !(newVal) || newVal < 1 || newVal > getMaxPTForProj(proj) ) { return false; }
			else { return true; }
		}
		return false;
	}

	function addDelta(empl, proj, delta) {
		var oldVal;
		if ( isAllowed(empl, proj, delta) ) {
			oldVal = temp.get(proj).get(empl);
			temp.get(proj).set(empl, oldVal + delta);
			return true;
		}
		return false;
	}

	function getCompensatorEmpl(currEmpl, currProj, delta) {
		// Minimum PT value is 1, maximum is (totalPT-nEmpl).
		// In case of ties, will pick the candidate listed first in the map.
		// !! TODO !! resolve the tie based on optimizing budget!
		var candVals = [],
			compensatorIx = null,
			candidates = new Map(temp.get(currProj));
		candidates.delete(currEmpl);
		excludedEmpl.forEach( function(d) { candidates.delete(d); } );
		if ( delta > 0 ) {
			filterMapByValue(candidates, a => a > 1 );
			candVals = Array.from( candidates.values() );
			compensatorIx = candVals.indexOf( Math.max(...candVals) );
		} else if ( delta < 0 ) {
			filterMapByValue(candidates, a => a < getMaxPTForProj(currProj) );
			candVals = Array.from( candidates.values() );
			compensatorIx = candVals.indexOf( Math.min(...candVals) );
		}
		return Array.from( candidates.keys() )[compensatorIx] || "";
	}

	function getCompensatorProj(currEmpl, currProj, delta) {
		// In case of ties, will pick the project listed first in the map.
		// !! TODO !! resolve the tie based on optimizing budget!
		var candVals = [],
			compensatorIx = null,
			candidates = new Map(temp);
		candidates.delete(currProj);
		excludedProj.forEach( function(d) { candidates.delete(d); } );
		filterMapByValue(candidates, a => a.has(currEmpl) );
		for ( var [key, value] of candidates.entries() ) {
			candVals.push( value.get(currEmpl) );
		}
		if ( delta > 0 ) {
			filterMapByValue(candidates, function(a) {
				for ( var k of a.values() ) { return k => k > 1; }
			} );
			compensatorIx = candVals.indexOf( Math.max(...candVals) );
		} else if ( delta < 0 ) {
			compensatorIx = candVals.indexOf( Math.min(...candVals) );
		}
		return Array.from( candidates.keys() )[compensatorIx] || "";
	}
}

function findSkilledEmployees(proj) {}

function isWithinBudget(map, proj) {
	var totalPT = sum( getProjectData(map, proj) );
	if ( totalPT > getProjObj(proj).PT ) { return false; }
	else { return true; }
}

function computeEmplScore(empl, proj) {
	var emplObj = getEmplObj(empl);
	var projObj = getProjObj(proj);
	var score = 0,
		skills = false,
		leadFactor = 1,
		costPerDay = 0;

	// Check if employee has necessary skill(s) for project
	for ( let s of projObj.skills ) {
		if ( emplObj.skills.includes(skill) ) { skills = true; break; }
	}
	// Check if employee is project lead
	if ( projObj.lead === empl ) { leadFactor = 10; }

	score = skills * leadFactor * emplObj.seniority * emplObj.costPerDayZscore;
	return score;
}

function getEmplObj(empl) {
	return employees.find( function(obj) { return obj.username === empl; } );
}

function getProjObj(proj) {
	return projects.find( function(obj) { return obj.prtID === proj; } );
}


function computeEmplTotalPT(map, empl) {
	var totalPT = 0;
	for ( var [key, value] of map.entries() ) {
		if ( value.has(empl) ) {
			totalPT += value.get(empl);
		}
	}
	return totalPT;
}



// -----------------------------------------------------------------------------------------------------------------------------------------------
// Helper functions
$("#reset-btn").click(function(){
    $.ajax({
      url: "/reset_data",
      type: "get",
      success: function(response) {
      	console.log("Success!");
      	var parsed_data = JSON.parse(response);
        // $("#req-res").html(response)
        projEmplMap = createProjEmplMap(parsed_data);
        if ( currentProj ) {
        	oldValues = getProjectData(projEmplMap, currentProj);
        	updateSliders();
        	setStatusMsg();
        }
        updatePies();
		// printEmployeeTable();
      },
      error: function(xhr) {
      	$("#req-res").html("Could not retrieve response!")
      	console.log("Error in response!")
      }
    });
});

$("#optim-btn").click(function(){
    $.ajax({
      url: "/optimize_data",
      type: "get",
      success: function(response) {
      	console.log("Success!");
      	var parsed_data = JSON.parse(response);
        // $("#req-res").html(response)
        projEmplMap = createProjEmplMap(parsed_data);
        if ( currentProj ) {
        	oldValues = getProjectData(projEmplMap, currentProj);
        	updateSliders();
        	setStatusMsg();
        }
        updatePies();
		// printEmployeeTable();
      },
      error: function(xhr) {
      	$("#req-res").html("Could not retrieve response!")
      	console.log("Error in response!")
      }
    });
});


function makeDataMatrix() {
	var data = [];
	projEmplMap.forEach( function(val, key) {
		data.push( Array.from( val.values() ) );
	});
	return data;
}

function printEmployeeTable() {
	d3.select('#emptab tbody').html('');
	d3.select('#emptab tbody').append('tr')
		.append('th').text('Employee')
		.append('th').text('Current PT')
		.append('th').text('Original PT');
	employees.forEach( function (val, idx) {
		var tr = d3.select('#emptab tbody').append('tr');
		// Append employee labels
		tr.append('td')
		  .attr('class', 'edit')
		  .attr('bgcolor', mycolors(val.username))
		  .text(val.username);
		// Append current PT count  
		tr.append('td')
		  .text( computeEmplTotalPT(projEmplMap, val.username) );
		// Append original PT count
		tr.append('td')
		  .text( computeEmplTotalPT(projEmplMap_original, val.username) );
	});

	d3.select('#projtab tbody').html('');
	d3.select('#projtab tbody').append('tr')
		.append('th').text('Project')
		.append('th').text('Current PT')
		.append('th').text('Original PT');
	projects.forEach( function (val, idx) {
		var tr = d3.select('#projtab tbody').append('tr');
		// Append project labels
		tr.append('td')
		  .text( val.name );
		// Append current PT count  
		tr.append('td')
		  .text( sum(Array.from(projEmplMap.get(val.prtID).values())) );
		// Append original PT count
		tr.append('td')
		  .text( sum(Array.from(projEmplMap_original.get(val.prtID).values())) );
	});
}


function getProjectData(map, proj) {
	return Array.from( map.get(proj).values() );
}

function getSliderValues() {
  var sval = [];
  d3.selectAll('.range').each(function() {
    sval[d3.select(this).attr('data-id')] = parseInt(d3.select(this).attr('value'));
  });
  return sval;
}


function sum(arr) {
  return arr.reduce(function(a,b) { return parseInt(a) + parseInt(b); }, 0);
}
  
function arcTween(a) {
  var i = d3.interpolate(this._current, a);
  this._current = i(0);
  return function(t) {
    return arc(i(t));
  };
}
