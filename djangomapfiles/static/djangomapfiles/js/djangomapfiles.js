// Requires underscore.js
// So be sure to load it!

function filter_queryset_by_fields(qset, desired_fields) { 
    var desired_data = []
    for (var i = 0; i < qset.length; i++) {
	desired_data.push(_.pick(qset[i].fields, desired_fields));
	}
    return desired_data;
}

// now I need a function to flatten the data and restore names/values
// to where they belong

function switchup(someobj) {
    return _.values(someobj)
}

function crunch_vals(data) {
    return _.map(data, switchup);
}
