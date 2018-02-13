'use strict';

function loadPing (pingId, elem) {
	// Load complaints
	$.get('/proxy/list-pings?ping_ids=' + pingId).done(function (data) {
		if ( data.code == 0 && data.pings.length > 0 ) {
			var ping = data.pings[0];
			elem.append( render('h2', ping.title) );
			elem.append( render('p', ping.description) );
			console.log(ping);
		}
		else {
			console.log('Got error while loading ping (code is: ' + data.code + ') or there is no ping with ' + pingId + '.');
		}
	});
}
