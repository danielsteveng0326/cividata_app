function alert_sweetalert(args) {
    if (!args.hasOwnProperty('type')) {
        args.type = 'success';
    }
    if (!args.hasOwnProperty('title')) {
        args.title = 'Notificación';
    }
    if (args.hasOwnProperty('message')) {
        args.html = '';
    } else {
        args.message = '';
    }
    if (!args.hasOwnProperty('timer')) {
        args.timer = null;
    }
    Swal.fire({
        icon: args.type,
        title: args.title,
        text: args.message,
        html: args.html,
        grow: true,
        showCloseButton: true,
        allowOutsideClick: true,
        timer: args.timer
    }).then((result) => {
        args.callback();
    });
}

function message_error(message) {
    var content = message;
    if (typeof (message) === "object") {
        content = JSON.stringify(message);
    }
    alert_sweetalert({
        'type': 'error',
        'message': content,
        'timer': null,
        'callback': function () {

        }
    });
}

function submit_with_formdata(args) {
    if (!args.hasOwnProperty('type')) {
        args.type = '';
    }
    if (!args.hasOwnProperty('theme')) {
        args.theme = 'modern';
    }
    if (!args.hasOwnProperty('title')) {
        args.title = 'Notificación';
    }
    if (!args.hasOwnProperty('icon')) {
        args.icon = 'fas fa-info-circle';
    }
    if (!args.hasOwnProperty('content')) {
        args.content = '¿Estas seguro de realizar la siguiente acción?';
    }
    if (!args.hasOwnProperty('pathname')) {
        args.pathname = pathname;
    }

    $.confirm({
        type: args.type,
        theme: args.theme,
        title: args.title,
        icon: args.icon,
        content: args.content,
        columnClass: 'small',
        typeAnimated: true,
        cancelButtonClass: 'btn-primary',
        draggable: true,
        dragWindowBorder: false,
        buttons: {
            info: {
                text: "Si",
                btnClass: 'btn-primary',
                action: function () {
                    $.ajax({
                        url: args.pathname,
                        data: args.params,
                        type: 'POST',
                        dataType: 'json',
                        headers: {
                            'X-CSRFToken': csrftoken
                        },
                        processData: false,
                        contentType: false,
                        beforeSend: function () {
                            loading({'text': '...'});
                        },
                        success: function (request) {
                            if (!request.hasOwnProperty('error')) {
                                if (request.hasOwnProperty('resp') && request.resp === false) {
                                    return message_error(request.msg);
                                }
                                if (args.hasOwnProperty('success')) {
                                    args.success(request);
                                } else {
                                    location.href = $(args.form).attr('data-url');
                                }
                                return false;
                            }
                            return message_error(request.error);
                        },
                        error: function (jqXHR, textStatus, errorThrown) {
                            message_error(errorThrown + ' ' + textStatus);
                        },
                        complete: function () {
                            $.LoadingOverlay("hide");
                        }
                    });
                }
            },
            danger: {
                text: "No",
                btnClass: 'btn-red',
                action: function () {

                }
            },
        }
    });
}

function loading(args) {
    if (!args.hasOwnProperty('fontawesome')) {
        args.fontawesome = 'fa-solid fa-circle-notch fa-spin';
    }
    if (!args.hasOwnProperty('text')) {
        args.fontawesome = 'Cargando...';
    }
    $.LoadingOverlay("show", {
        image: "",
        fontawesome: args.fontawesome,
        custom: $("<div>", {
            "class": "loading",
            "text": args.text
        })
    });
}

function dialog_action(args) {
    if (!args.hasOwnProperty('type')) {
        args.type = '';
    }
    if (!args.hasOwnProperty('theme')) {
        args.theme = 'modern';
    }
    if (!args.hasOwnProperty('title')) {
        args.title = 'Confirmación';
    }
    if (!args.hasOwnProperty('icon')) {
        args.icon = 'fas fa-info-circle';
    }
    if (!args.hasOwnProperty('content')) {
        args.content = '¿Estas seguro de realizar la siguiente acción?';
    }
    $.confirm({
        type: args.type,
        theme: args.theme,
        title: args.title,
        icon: args.icon,
        content: args.content,
        columnClass: 'small',
        typeAnimated: true,
        cancelButtonClass: "btn-primary",
        draggable: true,
        dragWindowBorder: false,
        buttons: {
            info: {
                text: "Si",
                btnClass: 'btn-primary',
                action: function () {
                    args.success();
                }
            },
            danger: {
                text: "No",
                btnClass: 'btn-red',
                action: function () {
                    args.cancel();
                }
            },
        }
    });
}

function validate_text_box(args) {
    if (!args.hasOwnProperty('type')) {
        args.type = 'numbers';
    }
    var key = args.event.keyCode || args.event.which;
    var numbers = (key > 47 && key < 58) || key === 8;
    var numbers_spaceless = key > 47 && key < 58;
    var letters = !((key !== 32) && (key < 65) || (key > 90) && (key < 97) || (key > 122 && key !== 241 && key !== 209 && key !== 225 && key !== 233 && key !== 237 && key !== 243 && key !== 250 && key !== 193 && key !== 201 && key !== 205 && key !== 211 && key !== 218)) || key === 8;
    var letters_spaceless = !((key < 65) || (key > 90) && (key < 97) || (key > 122 && key !== 241 && key !== 209 && key !== 225 && key !== 233 && key !== 237 && key !== 243 && key !== 250 && key !== 193 && key !== 201 && key !== 205 && key !== 211 && key !== 218)) || key === 8;
    var decimals = ((key > 47 && key < 58) || key === 8 || key === 46);

    switch (args.type) {
        case "numbers":
            return numbers;
        case "numbers_spaceless":
            return numbers_spaceless;
        case "letters":
            return letters;
        case "numbers_letters":
            return numbers || letters;
        case "letters_spaceless":
            return letters_spaceless;
        case "decimals":
            return decimals;
    }
    return true;
}

function load_image(args) {
    if (!args.hasOwnProperty('alt')) {
        args.alt = '';
    }
    Swal.fire({
        imageUrl: args.url,
        imageWidth: '100%',
        imageHeight: 250,
        imageAlt: args.alt,
        animation: false
    })
}

function convert_to_formdata(data) {
    if (!(data instanceof FormData)) {
        let params = new FormData();
        for (const key in data) {
            if (data.hasOwnProperty(key)) {
                params.append(key, data[key]);
            }
        }
        return params;
    }
    return data;
}

function execute_ajax_request(args) {
    if (!args.hasOwnProperty('pathname')) {
        args.pathname = pathname;
    }
    if (!args.hasOwnProperty('loading')) {
        args.loading = true;
    }

    let ajaxConfig = {
        url: args.pathname,
        data: convert_to_formdata(args.params),
        type: 'POST',
        processData: false,
        contentType: false,
        headers: {
            'X-CSRFToken': csrftoken
        },
        beforeSend: function () {
            if (args.loading) {
                loading({'text': '...'});
            }
            if (args.hasOwnProperty('beforeSend')) {
                args.beforeSend();
            }
        },
        success: function (data, status, request) {
            if (!data.hasOwnProperty('error')) {
                args.success(data, status, request);
                return false;
            }
            message_error(data.error);
        },
        error: function (jqXHR, textStatus, errorThrown) {
            message_error(errorThrown + ' ' + textStatus);
        },
        complete: function () {
            $.LoadingOverlay("hide");
            if (args.hasOwnProperty('complete')) {
                args.complete();
            }
        }
    };

    if (!args.hasOwnProperty('dataType')) {
        args.dataType = 'json';
    }

    switch (args.dataType) {
        case "json":
            ajaxConfig.dataType = 'json';
            break;
        case "blob":
            ajaxConfig.xhrFields = {
                responseType: 'blob'
            };
            break;
    }

    $.ajax(ajaxConfig);
}