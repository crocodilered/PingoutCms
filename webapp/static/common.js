'use strict';

$(document).ready(function() {

	$('#navbar-button-signout').click(function(e){
		$.getJSON('/proxy/sign-out')
			.done(function(data){
				window.location.href = "/";
			});
	});

});


function render (tag, content, options) {
	var html = '';
	if ( content ) {
		html += '<' + tag + '>';
		html += content;
		html += '</' + tag + '>';
	}
	return html;
}
