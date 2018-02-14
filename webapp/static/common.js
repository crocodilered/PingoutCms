'use strict';

$(document).ready(function() {

	$('.progress-global').css('top', $('.navbar').outerHeight() + 'px');

	$('#navbar-button-signout').click(function(e){
		$.getJSON('/proxy/sign-out')
			.done(function(data){
				window.location.href = "/";
			});
	});

});


function renderHtmlTag (tag, content, options) {
	var html = '';
	if ( content ) {
		html += '<' + tag + '>';
		html += content;
		html += '</' + tag + '>';
	}
	return html;
}
