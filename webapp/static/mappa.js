'use strict';

$(document).ready(function() {

	mapboxgl.accessToken = 'pk.eyJ1Ijoic2VyZ2V6b2xvdHVraGluIiwiYSI6ImNqNHRtYzF1ZjA2dncyd3FtcXRwajA0NWwifQ.dSvjI3CO2qXbR1qzSdv0HQ';

	var MODAL_COLOR_SWATCHES = ['#ffffff', '#5bc44c', '#3cc29f', '#1cb9d4', '#247dd0', '#7248c4', '#f071ba', '#c54141', '#fba735', '#e9ca2a', '#5e6a6b', '#b9c9ca'],
		PINGS = [];

	$('#modal-input-datetime').datetimepicker({locale: 'ru'});

	var MAP = new mapboxgl.Map({
		container: 'map',
		style: 'mapbox://styles/mapbox/dark-v9',
		center: {'lng': 37.61764775504926, 'lat': 55.753812934171464}, // starting position
    	zoom: 12 // starting zoom
	})
		.addControl(new mapboxgl.GeolocateControl(), 'bottom-right')
		.addControl(new mapboxgl.NavigationControl(), 'bottom-right')
		.on('zoomend', function(){
			if( MAP.getZoom() > 16 ) {
				if( MAP.getStyle().name != 'Satellite' ) MAP.setStyle('mapbox://styles/mapbox/satellite-v9');
			}
			else {
				if( MAP.getStyle().name != 'Mapbox Dark' ) MAP.setStyle('mapbox://styles/mapbox/dark-v9');
			}
		})
		.on('load', function () {

			var layers = MAP.getStyle().layers;
			for( var i=0; i<layers.length; i++ ) {
				if( MAP.getLayoutProperty(layers[i].id, 'text-field') )
					MAP.setLayoutProperty(layers[i].id, 'text-field', '{name_ru}');
			}

			// загрузить и отобразить пинги
			$.getJSON('/proxy/list-pings').done(function(data){
				if( data.code != 0 ) return false;
				// трансформировать данные
				var i;
				for( i in data.posts ) {
					data.posts[i].id = data.posts[i].post_id;
					data.posts[i].type = 'post';
					PINGS.push(data.posts[i]);
				}
				for( i in data.events ) {
					data.events[i].id = data.events[i].event_id;
					data.events[i].type = 'event';
					PINGS.push(data.events[i]);
				}
				for( i in PINGS ) createMarker(PINGS[i]);

			});
		})
		.on('click', openModal);

	$('#modal-input-tags').keyup(function(e){
		var tags = $(this).val()
		tags = tags.replace(/#/g, ' ').trim();
		tags = tags.replace(/  +/g, ' ');
		tags = tags.replace(/\s/g, ' #');
		if( e.keyCode == 32 ) tags = tags + ' #'
		$(this).val('#' + tags)
	});

	// Удаление пинга
	$('#modal-button-delete').click(function(e){
		if( !confirm("Речь об удалении пинга. Вы уверены?") ) return false;
		deletePing($('#modal-input-id').val(), $('#modal-input-type').val());
	});

	$('#modal').on('shown.bs.modal', function () {
		$('#modal-input-title').focus();
	});

	$("#modal-button-update").click(function(e){
		$('#modal-button-update span').removeClass('glyphicon-ok');
		$('#modal-button-update span').addClass('glyphicon-refresh glyphicon-refresh-animate');

		var pingId = $('#modal-input-id').val(),
			pingType = $('#modal-input-type').val(),
			file = document.getElementById('modal-input-file').files[0];
		if( file ) {
			// одно на всех действие, вынесем наверх
			var reader = new FileReader();
			reader.readAsDataURL(file);
		}

		if( pingId ) {
			// пинг есть, нужно просто сохранить
			if( file ) {
				reader.onload = function(e) {
					updatePing(
						pingId, pingType, $("#modal-input-title").val(), $("#modal-input-description").val(),
						dtPickerVal(), $("#modal-input-color").val(), $("#modal-input-tags").val(), e.target.result
					);
        		}
    		}
    		else {
				updatePing(
					pingId, pingType, $("#modal-input-title").val(), $("#modal-input-description").val(),
					dtPickerVal(), $("#modal-input-color").val(), $("#modal-input-tags").val(), null
				);
    		}
		} else {
			// новый пинг, нужно создать
			if( file ) {
				reader.onload = function(e) {
					createPing(
						$("#modal-input-lon").val(), $("#modal-input-lat").val(), $("#modal-input-title").val(),
						$("#modal-input-description").val(), dtPickerVal(), $("#modal-input-color").val(), $("#modal-input-tags").val(), e.target.result
					);
        		}
    		}
    		else {
				createPing(
					$("#modal-input-lon").val(), $("#modal-input-lat").val(), $("#modal-input-title").val(),
					$("#modal-input-description").val(), dtPickerVal(), $("#modal-input-color").val(), $("#modal-input-tags").val(), null
				);
    		}
		}
	});

	function lookupPingInCache(id, type) {
		for( var i in PINGS )
			if( PINGS[i].id == id && PINGS[i].type == type ) return PINGS[i];
		return null;
	}

	function setModalDatetime(visible) {
		if( visible ) {
			$('#form-group-datetime').show();
		}
		else {
			$('#form-group-datetime').hide();
		}
	}

	function setModalFile(filename) {
		if( filename ) {
			$('#form-group-file img').attr('src', filename);
			$('#form-group-file img').show();
		}
		else {
			$('#form-group-file img').hide();
		}
	}

	function setModalColor(colorNum) {
		if( !colorNum || (colorNum < 0 && colorNum >= MODAL_COLOR_SWATCHES.length) ) colorNum = 0;
		$('#modal-wrapper-color').remove();
		$('#form-group-color').append('<span id="modal-wrapper-color"></span>');
		$('#modal-input-color').val(colorNum);
		var c = $('#modal-wrapper-color').ColorPickerSliders({
			swatches: MODAL_COLOR_SWATCHES,
			customswatches: false,
			flat: true,
			invalidcolorsopacity: 0,
			order: {},
			color: MODAL_COLOR_SWATCHES[colorNum],
			onchange: function(container, color) { $('#modal-input-color').val(MODAL_COLOR_SWATCHES.indexOf(color.tiny.toHexString())); }
		});
	}

	function createMarker(ping) {
		var el = document.createElement('div'), r;
		el.id = ping.type + '-' + ping.id;
		el.setAttribute('data-ping-id', ping.id );
		el.innerHTML = '<span>' + (ping.title ? ping.title : '_без заголовка') + '</span>';
		el.setAttribute('class', 'ping-type-' + ping.type );
		r = new mapboxgl.Marker(el, {offset:[-3, -3]})
			.setLngLat([ping.lng, ping.lat])
			.addTo(MAP);
		$('#map .mapboxgl-canvas-container .mapboxgl-marker').click(openModal);
		return r;
	}

	function openModal(e) {
		if( e.originalEvent ) {
			// тыркнули по карте
			e.originalEvent.preventDefault();
			e.originalEvent.stopPropagation();
		}
		else {
			// тыркнули по маркеру
			e.preventDefault();
			e.stopPropagation();
		}

		$('#modal form input').val(null);
		$('#modal form textarea').val(null);

		var ping = lookupPingInCache($(this).data('ping-id'), $(this).hasClass('ping-type-post') ? 'post' : 'event');
		if( ping ) {
			$('.modal-dialog .modal-title').html('Редактировать пинг');
			$('#modal-input-id').val( ping.id );
			$('#modal-input-type').val( ping.type );
			$('#modal-input-title').val( ping.title );
			$('#modal-input-description').val( ping.description );
			$('#modal-input-tags').val( ping.tags );
			dtPickerVal(ping.fire_ts);
			setModalFile(ping.file_name);
			setModalColor(ping.color);
			setModalDatetime( ping.type == 'event' );
			$('#modal-button-delete').attr('disabled', false);
		}
		else {
			$('.modal-dialog .modal-title').html('Создать пинг');
			$('#modal-input-lon').val(e.lngLat.lng);
			$('#modal-input-lat').val(e.lngLat.lat);
			setModalColor();
			setModalDatetime(true);
			$('#modal-button-delete').attr('disabled', true);
		}
		$('#modal').modal();
	}

	function createPing(lon, lat, title, description, dt, color, tags, file_data) {
		$.post("/proxy/create-ping", {
			"ping_lon": lon,
			"ping_lat": lat,
			"ping_title": title,
			"ping_description": description,
			'ping_timestamp': dt,
			"ping_color": color,
			"ping_tags": tags,
			'ping_file_data': file_data
		}).done(function(data){
			if( data.code == 0 ) {
				PINGS.push({
					'id': data.ping_id,
					'type': data.ping_type,
					'title': $("#modal-input-title").val(),
					'lng': $("#modal-input-lon").val(),
					'lat': $("#modal-input-lat").val(),
					'description': $("#modal-input-description").val(),
					'color': $("#modal-input-color").val(),
					'tags': $("#modal-input-tags").val(),
					'fire_ts': dtPickerVal()
				});
				createMarker(PINGS[PINGS.length-1]);
				$('#modal').modal('hide');
			}
			else {
				alert("Ошибка на сервере, код: " + data.code);
			}
			$('#modal-button-update span').addClass('glyphicon-ok');
			$('#modal-button-update span').removeClass('glyphicon-refresh glyphicon-refresh-animate');
		});
	}

	function updatePing(id, type, title, description, dt, color, tags, file_data) {
		var args = {
			'ping_id': id,
			'ping_type': type,
			'ping_title': title,
			'ping_description': description,
			'ping_timestamp': dt,
			'ping_color': color,
			'ping_tags': tags,
			'ping_file_data': file_data
		};
		$.post("/proxy/update-ping", args)
			.done(function(data){
				if( data.code == 0 ) {
					var id = $('#modal-input-id').val(),
						type = $('#modal-input-type').val(),
						ping = lookupPingInCache(id, type);
					// обновить данные в PINGS
					ping.title = $("#modal-input-title").val();
					ping.description = $("#modal-input-description").val();
					ping.color = $("#modal-input-color").val();
					ping.tags = $("#modal-input-tags").val();
					ping.fire_ts = dtPickerVal();
					ping.file_name = data.file_name
					// Обновить маркер
					$( '#' + type + '-' + id + ' span').html( $("#modal-input-title").val() );
					$('#modal').modal('hide');
				}
				else {
					alert("Ошибка на сервере, код: " + data.code);
				}
				$('#modal-button-update span').addClass('glyphicon-ok');
				$('#modal-button-update span').removeClass('glyphicon-refresh glyphicon-refresh-animate');
			});
	}

	function deletePing(id, type) {
		$.getJSON('/proxy/delete-ping', { 'ping_id': id, 'ping_type': type })
			.done(function(data){
				if( data.code == 0 ) {
					// удаляем пинг с карты и закрываем диалог
					$('#' + type + '-' + id).remove();
					$('#modal').modal('hide');
				}
				else {
					// какая-то ошибка на сервере, сообщим
					alert("Ошибка на сервере, код: " + data.code);
				}
			});
	}

	function dtPickerVal(ts) {
		if( ts ) {
			console.log(ts);
			$('#modal-input-datetime').data('DateTimePicker').date(moment(ts*1000)); // coz of millisecs
		}
		else {
			var dt = $('#modal-input-datetime').data('DateTimePicker').date();
			return dt ? dt.utc().unix() : null
		}
	}

});

