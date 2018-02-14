'use strict';

var COMPLAINTS = [];

$(document).ready(function() {

	GlobalProgressBar.show();

	$.ajax({
		xhr: function () {
			var xhr = $.ajaxSettings.xhr();

			xhr.addEventListener('progress', function (evt) {
				if ( evt.lengthComputable ) {
					var complete = 100*evt.loaded/evt.total;
					GlobalProgressBar.update(complete);
				}
			}, false);

			return xhr;
		},
		async: true,
		type: 'GET',
		url: '/proxy/list-complaints',
		success: complaintsLoadSuccess
	});

	$('#modal-button-accept').click(function(){ modalButtonClick(1); });
	$('#modal-button-reject').click(function(){ modalButtonClick(2); });

});

function modalButtonClick (action) {
	var complaintId = $('#modal').data('complaint_id');
	$.get('/proxy/respond-to-complaint', {complaint_id: complaintId, action: action})
		.done(function(){
			$('.complaints tr[data-complaint_id="' + complaintId + '"]').remove();
			$('#modal').modal('hide');
		});
}

function complaintRenderTr (c) {
	var html = '';
	html += '<tr data-complaint_id="' + c.complaint_id + '">';
	html += '<td>' + tsToStr(c.ts) + '</td>';
	html += '<td>' + c.user_name + '</td>';
	if ( c.to_ping_id ) html += '<td>' + pingToHtml(c) + '</td>'; 
	else if ( c.to_user_id ) html += '<td>' + userToHtml(c) + '</td>';
	html += '</tr>';
	return html;
}

function complaintsLoadSuccess (data) {
	if ( data.code == 0 ) {

		COMPLAINTS = data.complaints;

		for ( var i in COMPLAINTS ) {
			if ( COMPLAINTS[i].to_ping_id ) $('#pings tbody').append( complaintRenderTr(COMPLAINTS[i]) );
			if ( COMPLAINTS[i].to_user_id ) $('#users tbody').append( complaintRenderTr(COMPLAINTS[i]) );
		}

		$('#pings tr, #users tr').click(openModal);

		GlobalProgressBar.hide();

		$('#pings').fadeIn();
		$('#users').fadeIn();
	}
	else {
		console.log("Got error while loading complaints. Code is: " + data.code);
	}
}

function openModal (event) {
	var complaintId = $(event.target).parents('tr').data('complaint_id'),
		complaint = getComplaint(complaintId);

	if ( complaint ) {
		$('#modal').data('complaint_id', complaint.complaint_id);
		if ( complaint.to_ping_id ) {
			$('#modal h4.modal-title').text('Жалоба на пинг');
			$('#modal .modal-body h1').text(complaint.to_ping_title);
			$('#modal .modal-body p').text(complaint.to_ping_description);
			$('#modal .modal-body img').attr('src', complaint.to_ping_image);
		}
		if ( complaint.to_user_id ) {
			$('#modal h4.modal-title').text('Жалоба на пользователя');
			$('#modal .modal-body h1').text(complaint.to_user_name);
			$('#modal .modal-body p').text(complaint.to_user_about);
			$('#modal .modal-body img').attr('src', complaint.to_user_avatar);
		}
		$('#modal').modal();
	}
}

function pingToHtml (data) {
	var r = '';
	if ( data.to_ping_id ) {
		r = data.to_ping_id;
		if ( data.to_ping_title ) r += ': ' + data.to_ping_title;
		r += '<br>';
		r += '<small>by ' + data.to_ping_user_id;
		if ( data.to_ping_user_name ) r += ': ' + data.to_ping_user_name;
		r += '</small>';
	}
	return r;
}

function userToHtml (data) {
	var r = '';
	if ( data.to_user_id ) {
		r = data.to_user_id;
		if ( data.to_user_name ) r += ': ' + data.to_user_name;
	}
	return r;
}

function tsToStr (ts) {
	var date = new Date(ts*1000);
	return date.toLocaleString().slice(0,-3);
}

function getComplaint(id) {
	for( var i in COMPLAINTS ) if( COMPLAINTS[i].complaint_id == id ) return COMPLAINTS[i];
	return null;
}

