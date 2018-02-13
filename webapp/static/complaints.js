'use strict';

$(document).ready(function() {

	var complaintRenderTr = function (c) {
		var html = '';
		html += '<tr data-complaint_id="' + c.complaint_id + '"';
		if ( c.to_ping_id ) html += ' data-to_ping_id="' + c.to_ping_id + '"';
		if ( c.to_user_id ) html += ' data-to_user_id="' + c.to_user_id + '"';
		html += '>';
		html += '<td>' + tsToDateStr(c.ts) + '</td>';
		html += '<td>' + c.user_name + '</td>';
		html += '<td>' + pingToHtml(c) + '</td>';
		html += '<td>' + userToHtml(c) + '</td>';
		html += '<td><button class="button-accept">Согласен</button>    <button class="button-reject">Удалить</button></td>';
		html += '</tr>';
		return html;
	}

	var complaintsLoadSuccess = function (data) {
		var comp, html;
		if ( data.code == 0 ) {
			for ( var i in data.complaints ) $('#complaints tbody').append( complaintRenderTr(data.complaints[i]) );
			$('#complaints').show(300);
			$('.button-accept').click(function (event) {
				var complainId = $(event.target).parents('tr').data('complaint_id');
				// START FROM HERE
				console.log(complainId);
			});
		}
		else {
			console.log("Got error while loading complaints. Code is: " + data.code);
		}
	}

	// Load complaints
	$.ajax({
		xhr: function () {
			var xhr = $.ajaxSettings.xhr();
			// прогресс скачивания с сервера
			xhr.addEventListener('progress', function (evt) {
				if ( evt.lengthComputable ) {
					var complete = evt.loaded/evt.total;
					$('h1').css('opacity', complete);
					console.log(complete);
				}
			}, false);
			return xhr;
		},
		async: true,
		type: 'GET',
		url: '/proxy/list-complaints',
		success: complaintsLoadSuccess
	});

});

function pingToHtml (data) {
	var r = '—';
	if ( data.to_ping_id ) {
		r = '<a href="/ping/?ping_id=' + data.to_ping_id + '">' + data.to_ping_id + '</a>';
		if ( data.to_ping_title ) r += ': ' + data.to_ping_title;
		r += '<br>';
		r += '<small>by ' + data.to_ping_user_id;
		if ( data.to_ping_user_name ) r += ': ' + data.to_ping_user_name;
		r += '</small>';
	}
	return r;
}

function userToHtml (data) {
	var r = '—';
	if ( data.to_user_id ) {
		r = '<a href="/ping/?ping_id=' + data.to_user_id + '">' + data.to_user_id + '</a>';
		if ( data.to_user_name ) r += ': ' + data.to_user_name;
	}
	return r;
}

function tsToDateStr (ts) {
	var date = new Date(ts*1000);
	return date.toLocaleString();
}
