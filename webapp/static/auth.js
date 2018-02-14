$(document).ready(function() {

	$('#button-getcode').click(function(e) {

		e.preventDefault();

		var inputEl = $('#input-phone'),
			buttonEl = $(this),
			phone = extractPhone(inputEl.val());

		if( phone ) {
			// есть номер, фигачим запрос на сервер
			inputEl.parent('.input-group')
				.removeClass('has-error')
				.addClass('has-success');

			buttonEl
				.attr('disabled', 'disabled')
				.find('.glyphicon')
					.removeClass('glyphicon-arrow-right')
					.addClass('glyphicon-refresh glyphicon-refresh-animate');

			$.getJSON('/api/get-code', {phone:phone})
				.done(function(data) {
					if( data.code != 0 ) {
						alert("Ошибка!\nСервер вернул код " + data.code + ".");
						inputEl.parent('.input-group').removeClass('has-success');
						buttonEl
							.attr('disabled', null)
							.find('.glyphicon')
								.removeClass('glyphicon-refresh glyphicon-refresh-animate')
								.addClass('glyphicon-arrow-right');
						return false;
					}
					buttonEl
						.removeClass('btn-primary')
						.addClass('btn-success')
						.find('.glyphicon')
							.removeClass('glyphicon-refresh glyphicon-refresh-animate')
							.addClass('glyphicon-ok');
					$('#form-group-code').fadeIn();
					$('#input-code').focus();
				});
		}
		else {
			// нет номера, кажем ошибку
			setInputState('#input-phone', '#button-getcode', false)
			// после ошибки надо на onkeypress проверять значение на верность
			inputEl.keyup(function(e){
				var inputEl = $('#input-phone');
				phone = extractPhone( inputEl.val() );
				setInputState('#input-phone', '#button-getcode', phone);
			});
			return false;
		}
	});

	$('#button-signin').click(function(e) {
		e.preventDefault();

		var inputEl = $('#input-code'),
			buttonEl = $(this);

		if( inputEl.val() ) {
			inputEl.parent('.input-group')
				.removeClass('has-error');

			$.getJSON('/api/sign-in', {
				phone: extractPhone($('#input-phone').val()),
				code: inputEl.val()
			})
				.done(function(data){
					if( data.code == 0 ) {
						window.location.href = "/mappa/";
					}
					else {
						//todo: Показать сообщение об том, что код херовый
					}
				});
		}
		else {
			setInputState('#input-code', '#button-signin', false)
			inputEl.keyup(function(e){
				var inputEl = $('#input-code');
				setInputState('#input-code', '#button-signin', inputEl.val());
			});
			return false;
		}
	});

	var extractPhone = function(s) {
		if( !s ) return false;
		phone = s.replace(/\D/g, '');
		if( phone.length == 11 ) {
			if( phone[0] == '8' ) phone = '7' + phone.substr(1, 300);
			return '+' + phone;
		}
		return false;
	}

	var setInputState = function(input, button, state) {
		var inputEl = $(input),
			buttonEl = $(button);

		if( state ) {
			inputEl.parent('.input-group')
				.removeClass('has-error')
				.addClass('has-success');
			buttonEl
				.removeClass('btn-danger')
				.addClass('btn-success');
		}
		else {
			inputEl.parent('.input-group')
				.removeClass('has-success')
				.addClass('has-error');
			buttonEl
				.removeClass('btn-success')
				.addClass('btn-danger');
		}
	}

});