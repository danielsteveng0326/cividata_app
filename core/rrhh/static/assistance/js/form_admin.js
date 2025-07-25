var fv;
var input_datejoined, input_assistance_for_all;
var tblAssistance = null;
var assistance = {
    generate: function () {
        tblAssistance = $('#tblAssistance').DataTable({
            autoWidth: false,
            destroy: true,
            ajax: {
                url: pathname,
                type: 'POST',
                data: {
                    'action': 'generate_assistance',
                    'date_joined': input_datejoined.val()
                },
                dataSrc: "",
                headers: {
                    'X-CSRFToken': csrftoken
                }
            },
            ordering: false,
            lengthChange: false,
            paging: false,
            columns: [
                {data: "user.names"},
                {data: "dni"},
                {data: "position.name"},
                {data: "area.name"},
                {data: "description"},
                {data: "id"},
            ],
            columnDefs: [
                {
                    targets: [-2],
                    data: null,
                    class: 'text-center',
                    render: function (data, type, row) {
                        return '<input type="text" name="description" style="width: 100%;" class="form-control form-control-sm" placeholder="Ingrese una descripción" value="' + data + '" autocomplete="off">';
                    }
                },
                {
                    targets: [-1],
                    data: null,
                    class: 'text-center',
                    render: function (data, type, row) {
                        var attr = row.active === 1 ? ' checked' : '';
                        return '<input type="checkbox" name="active" class="form-control-checkbox" ' + attr + '>';
                    }
                },
            ],
            rowCallback: function (row, data, index) {
                var tr = $(row).closest('tr');
                var background = data.active === 0 ? '#fff' : '#fff0d7';
                $(tr).css('background', background);
            },
            initComplete: function (settings, json) {
                $(this).wrap('<div class="dataTables_scroll"><div/>');
            }
        });
    }
};

document.addEventListener('DOMContentLoaded', function (e) {
    fv = FormValidation.formValidation(document.getElementById('frmForm'), {
            locale: 'es_ES',
            localization: FormValidation.locales.es_ES,
            plugins: {
                trigger: new FormValidation.plugins.Trigger(),
                submitButton: new FormValidation.plugins.SubmitButton(),
                bootstrap: new FormValidation.plugins.Bootstrap(),
                icon: new FormValidation.plugins.Icon({
                    valid: 'fa fa-check',
                    invalid: 'fa fa-times',
                    validating: 'fa fa-refresh',
                }),
            },
            fields: {
                date_joined: {
                    validators: {
                        notEmpty: {
                            message: 'La fecha es obligatoria'
                        },
                        date: {
                            format: 'YYYY-MM-DD',
                            message: 'La fecha no es válida'
                        },
                        remote: {
                            url: pathname,
                            data: function () {
                                return {
                                    date_joined: fv.form.querySelector('[name="date_joined"]').value,
                                    action: 'validate_data'
                                };
                            },
                            message: 'La fecha de asistencia ya esta registrada',
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': csrftoken
                            }
                        }
                    }
                },
            },
        }
    )
        .on('core.element.validated', function (e) {
            if (e.valid) {
                const groupEle = FormValidation.utils.closest(e.element, '.form-group');
                if (groupEle) {
                    FormValidation.utils.classSet(groupEle, {
                        'has-success': false,
                    });
                }
                FormValidation.utils.classSet(e.element, {
                    'is-valid': false,
                });
            }
            const iconPlugin = fv.getPlugin('icon');
            const iconElement = iconPlugin && iconPlugin.icons.has(e.element) ? iconPlugin.icons.get(e.element) : null;
            iconElement && (iconElement.style.display = 'none');
        })
        .on('core.validator.validated', function (e) {
            if (!e.result.valid) {
                const messages = [].slice.call(fv.form.querySelectorAll('[data-field="' + e.field + '"][data-validator]'));
                messages.forEach((messageEle) => {
                    const validator = messageEle.getAttribute('data-validator');
                    messageEle.style.display = validator === e.validator ? 'block' : 'none';
                });
            }
        })
        .on('core.form.valid', function () {
            var assistances = tblAssistance.rows().data().toArray();
            if (assistances.length === 0) {
                message_error('Debe tener al menos un empleado en el listado de asistencias');
                return false;
            }
            var params = new FormData(fv.form);
            params.append('assistances', JSON.stringify(assistances));
            var args = {
                'params': params,
                'form': fv.form
            };
            submit_with_formdata(args);
        });
});

$(function () {
    input_assistance_for_all = $('input[name="assistance_for_all"]');
    input_datejoined = $('input[name="date_joined"]');

    input_datejoined.datetimepicker({
        useCurrent: false,
        format: 'YYYY-MM-DD',
        locale: 'es',
        keepOpen: false,
    });

    input_datejoined.on('change.datetimepicker', function (e) {
        fv.validateField('date_joined').then(function (status) {
            console.log(status);
            if (status === 'Valid') {
                input_assistance_for_all.prop('disabled', false);
                assistance.generate();
            } else {
                if (tblAssistance !== null) {
                    tblAssistance.clear().draw();
                }
                input_assistance_for_all.prop('disabled', true);
            }
        });
    });

    input_datejoined.trigger('change');

    $('#tblAssistance tbody')
        .off()
        .on('change', 'input[name="active"]', function () {
            var active = this.checked;
            var tr = tblAssistance.cell($(this).closest('td, li')).index();
            var row = tblAssistance.row(tr.row).data();
            row.active = active ? 1 : 0;
            var background = !active ? '#fff' : '#fff0d7';
            $(tblAssistance.row(tr.row).node()).css('background', background);
        })
        .on('keyup', 'input[name="description"]', function () {
            var tr = tblAssistance.cell($(this).closest('td, li')).index();
            var row = tblAssistance.row(tr.row).data();
            row.description = $(this).val();
        });

    input_assistance_for_all.on('change', function () {
        var active = this.checked;
        if (tblAssistance !== null) {
            var cells = tblAssistance.cells().nodes();
            $(cells).find('input[type="checkbox"][name="active"]').prop('checked', active).change();
        }
    });
});