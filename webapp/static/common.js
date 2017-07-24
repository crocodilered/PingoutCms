'use strict';

$(document).ready(function() {

}
	$('#button-signout').click(function(e){
		$.getJSON('/proxy/sign-out')
			.done(function(data){
				window.location.href = "/";
			});
	});

}
