var tblHeadings = null;
var select_employee;
var input_year_month;
var fv;
var salary = {
    listEmployees: function () {
        var employees = select_employee.select2('data').map(value => parseInt(value.id));
        var params = {
            'action': 'search_employees',
            'employee_id': JSON.stringify(employees),
            'year': input_year_month.datetimepicker('date').format("YYYY"),
            'month': input_year_month.datetimepicker('date').format("MM"),
        };

        execute_ajax_request({
            'params': params,
            'success': function (request) {
                tblHeadings = $('#tblHeadings').DataTable({
                    autoWidth: false,
                    destroy: true,
                    data: request.detail,
                    columns: request.columns,
                    columnDefs: [
                        {
                            targets: '_all',
                            class: 'text-center',
                            render: function (data, type, row) {
                                if (typeof data === "object") {
                                    var disabled = ['total_assets', 'total_discounts', 'total_charge'].includes(data.code) ? 'disabled' : '';
                                    return '<input type="text" ' + disabled + ' rel="amount" class="form-control form-control-sm" autocomplete="off" value="' + parseFloat(data.amount).toFixed(2) + '" placeholder="Ingrese un valor" name="' + data.code + '">';
                                }
                                if (Number.isInteger(data)) {
                                    return '<input type="text" class="form-control form-control-sm" name="quantity" value="' + data + '" autocomplete="off">';
                                }
                                return '';
                            }
                        },
                        {
                            targets: [0],
                            class: 'text-center',
                            render: function (data, type, row) {
                                return row.employee.user.names;
                            }
                        },
                    ],
                    rowCallback: function (row, data, index) {
                        var tr = $(row).closest('tr');
                        var rmu = data.employee.remuneration;
                        $('td:eq(0)', row).html(data.employee.code + ' - ' + data.employee.user.names + ' (' + rmu + ')');
                        tr.find('input[type="text"]')
                            .on('keypress', function (e) {
                                return validate_text_box({'event': e, 'type': 'numbers'});
                            });
                    },
                    initComplete: function (settings, json) {
                        $(this).wrap('<div class="dataTables_scroll"><div/>');
                    }
                });
                $('#tblHeadings tbody')
                    .off()
                    .on('keyup', 'input[type="text"][rel="amount"]', function (e) {
                        let tr = tblHeadings.cell($(this).closest('td, li')).index();
                        let name = $(this)[0].name;
                        let text = $(this).val();
                        var row = tblHeadings.row(tr.row).data();
                        row[name]['amount'] = parseFloat(text);
                        salary.calculateRol(tr.row);
                        $(this).parents('tr').find('input[name="total_assets"]').val(parseFloat(row.total_assets.amount));
                        $(this).parents('tr').find('input[name="total_discounts"]').val(parseFloat(row.total_discounts.amount));
                        $(this).parents('tr').find('input[name="total_charge"]').val(parseFloat(row.total_charge.amount));
                    })
                    .on('keyup', 'input[type="text"][name="quantity"]', function (e) {
                        let tr = tblHeadings.cell($(this).closest('td, li')).index();
                        var element = $(this).parent().next().find('input[type="text"][rel="amount"]');
                        let name = $(element)[0].name;
                        var row = tblHeadings.row(tr.row).data();
                        row[name].quantity = parseInt($(this).val());
                    });
            },
        });
    },
    calculateRol: function (position) {
        let headings = tblHeadings.row(position).data();
        let total_assets = 0.00; //parseFloat(heading.employee.remuneration);
        let total_discounts = 0.00;
        let total_charge;
        $.each(headings, function (index, value) {
            if (!['employee', 'total_assets', 'total_discounts', 'total_charge'].includes(index)) {
                switch (value.item_type.id) {
                    case "haberes":
                        total_assets += parseFloat(value.amount);
                        break;
                    case "descuentos":
                        total_discounts += parseFloat(value.amount);
                        break;
                }
            }
        });
        headings.total_assets.amount = parseFloat(total_assets);
        headings.total_discounts.amount = parseFloat(total_discounts);
        total_charge = total_assets - total_discounts;
        headings.total_charge.amount = total_charge;
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
                excluded: new FormValidation.plugins.Excluded(),
                icon: new FormValidation.plugins.Icon({
                    valid: 'fa fa-check',
                    invalid: 'fa fa-times',
                    validating: 'fa fa-refresh',
                }),
            },
            fields: {
                year_month: {
                    validators: {
                        notEmpty: {},
                        regexp: {
                            regexp: /^([0-9]{1,2}([/][0-9]{2}))+$/i,
                            message: 'Debe ingresar el mes y el año en el siguiente formato 01/20'
                        },
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
            if (tblHeadings === null) {
                message_error('Debe tener al menos un registro en el detalle de salario');
                return false;
            }
            var params = new FormData(fv.form);
            params.append('year', input_year_month.datetimepicker('date').format("YYYY"));
            params.append('month', input_year_month.datetimepicker('date').format("MM"));
            params.append('headings', JSON.stringify(tblHeadings.rows().data().toArray()));
            var args = {
                'params': params,
                'form': fv.form,
            };
            submit_with_formdata(args);
        });
});

$(function () {
    select_employee = $('select[name="employee"]');
    input_year_month = $('input[name="year_month"]');

    input_year_month.datetimepicker({
        viewMode: 'years',
        format: 'MM/YY',
        useCurrent: false,
        locale: 'es',
        date: new Date(),
    });

    input_year_month.on('change.datetimepicker', function (e) {
        fv.revalidateField('year_month');
    });

    select_employee.select2({
        theme: 'bootstrap4',
        language: "es",
        placeholder: 'Buscar..',
        allowClear: true,
        ajax: {
            delay: 250,
            type: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            url: pathname,
            data: function (params) {
                return {
                    term: params.term,
                    action: 'search_employee'
                };
            },
            processResults: function (data) {
                return {
                    results: data
                };
            },
        },
        minimumInputLength: 1,
    })
        .on('select2:select', function (e) {

        })
        .on('select2:clear', function (e) {

        });

    $('.btnSearch').on('click', function () {
        fv.revalidateField('year_month');
        if (tblHeadings !== null) {
            tblHeadings.clear().draw();
        }
        fv.validateField('year_month').then(function (status) {
            if (status === 'Valid') {
                salary.listEmployees();
            }
        });
    });
});