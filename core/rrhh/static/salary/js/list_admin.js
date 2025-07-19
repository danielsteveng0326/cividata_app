var input_year;
var select_month, select_employee;
var tblSalary;

var salary = {
    model: {},
    getEmployeesFromSelect: function () {
        return select_employee.select2('data').map(value => value.id);
    },
    countSalaryId: function () {
        var length = this.getSalaryIdSelected().length;
        $('.quantity').html(length);
    },
    getSalaryIdSelected: function () {
        var salaries = [];
        if (tblSalary) {
            salaries = tblSalary.rows().data().toArray().filter(value => value.selected === 1);
        }
        return salaries;
    },
    list: function () {
        var params = {
            'action': 'search',
            'year': input_year.datetimepicker('date').format("YYYY"),
            'month': select_month.val(),
            'employee_id': JSON.stringify(salary.getEmployeesFromSelect())
        };
        tblSalary = $('#data').DataTable({
            autoWidth: false,
            destroy: true,
            deferRender: false,
            ajax: {
                url: pathname,
                type: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                data: params,
                dataSrc: "",
                beforeSend: function () {
                    loading({'text': '...'});
                },
                complete: function () {
                    setTimeout(function () {
                        $.LoadingOverlay("hide");
                    }, 750);
                }
            },
            columns: [
                {data: "id"},
                {data: "employee.code"},
                {data: "employee.user.names"},
                {data: "employee.dni"},
                {data: "salary.year"},
                {data: "salary.month.name"},
                {data: "income"},
                {data: "expenses"},
                {data: "total_amount"},
                {data: "id"},
            ],
            columnDefs: [
                {
                    targets: [0],
                    class: 'text-center',
                    orderable: false,
                    render: function (data, type, row) {
                        return '<input type="checkbox" name="selected" class="form-control-checkbox">';
                    }
                },
                {
                    targets: [1, -5, -6],
                    class: 'text-center'
                },
                {
                    targets: [-2, -3, -4],
                    class: 'text-center',
                    render: function (data, type, row) {
                        return '$' + data;
                    }
                },
                {
                    targets: [-1],
                    class: 'text-center',
                    orderable: false,
                    render: function (data, type, row) {
                        var buttons = '<a class="btn btn-success btn-xs btn-flat" rel="detail" data-toggle="tooltip" title="Detalle"><i class="fas fa-folder-open"></i></a> ';
                        buttons += '<a href="' + pathname + 'print/' + row.id + '/" target="_blank" data-toggle="tooltip" title="Imprimir" class="btn btn-danger btn-xs btn-flat"><i class="fas fa-file-alt"></i></a>';
                        return buttons;
                    }
                },
            ],
            initComplete: function (settings, json) {
                $('[data-toggle="tooltip"]').tooltip();
                $(this).wrap('<div class="dataTables_scroll"><div/>');
                salary.countSalaryId();
            }
        });
    }
};

$(function () {
    input_year = $('input[name="year"]');
    select_month = $('select[name="month"]');
    select_employee = $('select[name="employee"]');

    input_year.datetimepicker({
        viewMode: 'years',
        format: 'YYYY',
        useCurrent: false,
        locale: 'es'
    });

    $('.select2').select2({
        theme: 'bootstrap4',
        language: "es"
    });

    $('.btnSearchSalaries').on('click', function () {
        salary.list();
    });

    $('input[name="select_all"]').on('change', function () {
        var checked = this.checked;
        if (tblSalary) {
            tblSalary.rows().every(function (rowIdx, tableLoop, rowLoop) {
                var data = this.data();
                data.selected = checked ? 1 : 0;
                var cell = this.cell(rowIdx, 0).node();
                $(cell).find('input[type="checkbox"][name="selected"]').prop('checked', checked);
            }).draw(false);
            salary.countSalaryId();
        }
    });

    $('#data tbody')
        .off()
        .on('change', 'input[name="selected"]', function () {
            var tr = tblSalary.cell($(this).closest('td, li')).index();
            var data = tblSalary.row(tr.row).data();
            data.selected = this.checked ? 1 : 0;
            salary.countSalaryId();
        })
        .on('click', 'a[rel="detail"]', function () {
            $('.tooltip').remove();
            var tr = tblSalary.cell($(this).closest('td, li')).index(),
                row = tblSalary.row(tr.row).data();
            salary.model = row;
            $('#tblHeadings').DataTable({
                autoWidth: false,
                destroy: true,
                ajax: {
                    url: pathname,
                    type: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken
                    },
                    data: {
                        'action': 'search_detail_heading',
                        'id': row.id
                    },
                    dataSrc: ""
                },
                ordering: false,
                lengthChange: false,
                searching: false,
                paginate: false,
                columnDefs: [
                    {
                        targets: [0],
                        class: 'text-left',
                        render: function (data, type, row) {
                            return data.toUpperCase();
                        }
                    },
                    {
                        targets: [1],
                        class: 'text-center'
                    },
                    {
                        targets: [-1, -2],
                        class: 'text-center',
                        render: function (data, type, row) {
                            if (data === '---') {
                                return data;
                            }
                            return '$' + data
                        }
                    },
                ],
                initComplete: function (settings, json) {
                    $(this).wrap('<div class="dataTables_scroll"><div/>');
                }
            });
            $('#myModalSalary').modal('show');
        });

    $('.SendSalariesByEmail').on('click', function () {
        var salaries = salary.getSalaryIdSelected();
        var params = new FormData();
        params.append('action', 'send_salary_email');
        params.append('salaries', JSON.stringify(salaries.map(value => value.id)));
        var args = {
            'params': params,
            'success': function (request) {
                alert_sweetalert({
                    'title': 'Notificación',
                    'message': 'Los roles de pago se han enviado exitosamente a los empleados',
                    'callback': function () {
                        salary.list();
                    }
                });
            }
        };
        submit_with_formdata(args);
    });

    $('.btnPrintReceiptEmployee').on('click', function () {
        var url = pathname + 'print/' + salary.model.id + '/';
        window.open(url, '_blank').focus();
    });

    $('.btnRemoveSalaries').on('click', function () {
        execute_ajax_request({
            'params': {
                'year': input_year.datetimepicker('date').format("YYYY"),
                'month': select_month.val(),
                'employee_id': JSON.stringify(salary.getEmployeesFromSelect()),
                'action': 'remove_salaries'
            },
            'success': function (request) {
                location.href = request.url;
            }
        });
    });

    $('.btnExportSalariesPdf').on('click', function () {
        execute_ajax_request({
            'params': {
                'year': input_year.datetimepicker('date').format("YYYY"),
                'month': select_month.val(),
                'employee_id': JSON.stringify(salary.getEmployeesFromSelect()),
                'action': 'export_salaries_pdf'
            },
            'dataType': 'blob',
            'success': function (data, status, request) {
                var a = document.createElement('a');
                document.body.appendChild(a);
                a.style = 'display: none';
                const blob = new Blob([data], {type: 'application/pdf'});
                const url = URL.createObjectURL(blob);
                a.href = url;
                a.download = request.getResponseHeader('X-Filename');
                a.click();
                window.URL.revokeObjectURL(url);
            }
        });
    });

    $('.btnGenerateTemplate').on('click', function () {
        var params = {
            'year': input_year.datetimepicker('date').format("YYYY"),
            'month': select_month.val(),
            'action': 'export_template_excel'
        };
        if (params.month === '') {
            message_error('Debe seleccionar un mes');
            return false;
        }
        execute_ajax_request({
            'params': params,
            'dataType': 'blob',
            'success': function (data, status, request) {
                var a = document.createElement('a');
                document.body.appendChild(a);
                a.style = 'display: none';
                const blob = new Blob([data], {type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
                const url = URL.createObjectURL(blob);
                a.href = url;
                a.download = request.getResponseHeader('X-Filename');
                a.click();
                window.URL.revokeObjectURL(url);
            }
        });
    });

    $('.btnExportSalariesExcel').on('click', function () {
        execute_ajax_request({
            'params': {
                'year': input_year.datetimepicker('date').format("YYYY"),
                'month': select_month.val(),
                'employee_id': JSON.stringify(salary.getEmployeesFromSelect()),
                'action': 'export_salaries_excel'
            },
            'dataType': 'blob',
            'success': function (data, status, request) {
                var a = document.createElement('a');
                document.body.appendChild(a);
                a.style = 'display: none';
                const blob = new Blob([data], {type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
                const url = URL.createObjectURL(blob);
                a.href = url;
                a.download = request.getResponseHeader('X-Filename');
                a.click();
                window.URL.revokeObjectURL(url);
            }
        });
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
});