'use strict';

$(document).ready(function() {

	$('#navbar-button-signout').click(function(e){
		$.getJSON('/api/sign-out')
			.done(function(data){
				window.location.href = "/";
			});
	});

});

class GlobalProgressBar {

	static show() {
		$('.progress-global').css('top', '0');
		$('.progress-global').show();
	}

	static update(value) {
		$('.progress-global .progress-bar').css('width', value + '%');
	}

	static hide() {
		setTimeout(function () { $('.progress-global').fadeOut() }, 300);
	}

};
