window.A = {

    defaultStatPeriod : 'today',

    switchDatepicker : function() {
        $('[data-period="today"]').on('click', function() {
            $('#id_date_start').val(moment().startOf('day').format('YYYY-MM-DD 00:00'));
            $('#id_date_end').val(moment().startOf('day').format('YYYY-MM-DD 23:59'));
        });
        $('[data-period="yesterday"]').on('click', function() {
            $('#id_date_start').val(moment().add(-1, 'days').format('YYYY-MM-DD 00:00'));
            $('#id_date_end').val(moment().add(-1, 'days').format('YYYY-MM-DD 23:59'));
        });
        $('[data-period="week"]').on('click', function() {
            $('#id_date_start').val(moment().weekday(0).format('YYYY-MM-DD 00:00'));
            $('#id_date_end').val(moment().weekday(6).format('YYYY-MM-DD 23:59'));
        });
        $('[data-period="month"]').on('click', function() {
            $('#id_date_start').val(moment().startOf('month').format('YYYY-MM-DD 00:00'));
            $('#id_date_end').val(moment().endOf('month').format('YYYY-MM-DD 23:59'));
        });
    },

    changeCallStatus : function() {
        $('.buttonStatusChange').on('click', function(e) {
            var btn = $(this);
            var currentStatus = btn.data('current-status'), callId = btn.data('call-id');
            e.preventDefault();
            btn.prop('disabled', true);
            $.post(A.updateCallStatusUrl, {'call_id': callId, 'is_new': currentStatus})
                .done(function(response) {
                    if (response.is_new == true) {
                        btn.removeClass('btn-default').addClass('btn-info');
                    } else {
                        btn.removeClass('btn-info').addClass('btn-default');
                    }
                    $(".buttonStatusChange").popover('destroy');
                })
                .fail(function (xhr, status, error) {
                    console.log(xhr.responseJSON.error_text);
                    $(".buttonStatusChange").popover('destroy');
                    btn.popover({
                        html: true,
                        content: xhr.responseJSON.error_text,
                        placement: 'left'
                    }).popover('show');
                })
                .always(function (response) {
                    var new_status = response.is_new == true ? 'True' : 'False';
                    var button_value = response.is_new == true ? 'Да' : 'Нет';
                    btn.data('current-status', new_status);
                    btn.prop('disabled', false);
                    btn.html(button_value);
                });
        });
    },

    drawStatCharts : function() {
        var generalElem = $('#general_stat_table');
        if (A.generalStatData.length < 1) {
            generalElem.empty().append('<p class="text-danger">Нет данных.</p>');
            $('#general_stat_chart').empty().append('<p class="text-danger">Нет данных.</p>');
        } else {
            var generalStatData = google.visualization.arrayToDataTable(A.generalStatData);
            var generalOptions = {
              title: 'Количество звонков',
              curveType: 'function',
              legend: { position: 'start' }
            };
            var generalChart = new google.visualization.LineChart(document.getElementById('general_stat_chart'));
            generalChart.draw(generalStatData, generalOptions);
            generalElem.empty();
            generalElem.append(buildHtml(A.generalStatData));
        }

        var employeeElem = $('#employees_stat_table');
        if (A.employeeStatData.length < 1) {
            $('#employees_stat_chart').empty().append('<p class="text-danger">Нет данных.</p>');
            employeeElem.empty().append('<p class="text-danger">Нет данных.</p>');
        } else {
            var employeeStatData = google.visualization.arrayToDataTable(A.employeeStatData),
            employeeOptions = {
              title: 'Распределение звонков',
              is3D: true
            };
            var employeeChart = new google.visualization.PieChart(document.getElementById('employees_stat_chart'));
            employeeChart.draw(employeeStatData, employeeOptions);

            employeeElem.empty();
            employeeElem.append(buildHtml(A.employeeStatData));
        }

        var employeeDailyElem = $('#employees_stat_daily_table');
        if (A.employeeStatDataDaily.length < 1) {
            $('#employees_stat_daily_chart').empty().append('<p class="text-danger">Нет данных.</p>');
            employeeDailyElem.empty().append('<p class="text-danger">Нет данных.</p>');
        } else {
            var employeeStatDataDaily = google.visualization.arrayToDataTable(A.employeeStatDataDaily),
            employeeDailyOptions = {
                title: 'Распределение звонков (по сотрудникам)',
                //curveType: 'function',
                legend: { position: 'bottom' }
            };
            var employeeDailyChart = new google.visualization.LineChart(document.getElementById('employees_stat_daily_chart'));
            employeeDailyChart.draw(employeeStatDataDaily, employeeDailyOptions);

            employeeDailyElem.empty();
            var employeeDailyTable = '<table class="table table-bordered table-hover table-striped"><thead>',
            employeeDailyRows = 0;
            $.each(A.employeeStatDataDaily, function(k, v) {
                employeeDailyRows += 1;
                if (employeeDailyRows == 1) {
                    employeeDailyTable += '<tr><th>' + v[0] + '</th><th>' + v[1] + '</th></tr></thead><tbody>';
                } else {
                    employeeDailyTable += '<tr><td>' + v[0] + '</td><td>' + v[1] + '</td></tr>';
                }
            });
            employeeDailyTable += "</tbody></table>";
            employeeDailyElem.append(employeeDailyTable);
        }

        if (A.regionalAll.length < 1) {
            $('#regional_all_chart').empty().append('<p class="text-danger">Нет данных.</p>');
        } else {
            var regionalAllData = google.visualization.arrayToDataTable(A.regionalAll);
            var regionalAllOptions = {
              title: 'Распределение звонков по регионам (все)',
              is3D: true
            };
            var regionalAllChart = new google.visualization.PieChart(document.getElementById('regional_all_chart'));
            regionalAllChart.draw(regionalAllData, regionalAllOptions);
        }

        if (A.regionalNew.length < 1) {
            $('#regional_new_chart').empty().append('<p class="text-danger">Нет данных.</p>');
        } else {
            var regionalNewData = google.visualization.arrayToDataTable(A.regionalNew);
            var regionalNewOptions = {
              title: 'Распределение звонков по регионам (новые)',
              is3D: true
            };
            var regionalNewChart = new google.visualization.PieChart(document.getElementById('regional_new_chart'));
            regionalNewChart.draw(regionalNewData, regionalNewOptions);
        }

        var ununsweredElem = $('#status_table');
        if (A.statusDaily.length < 1) {
            $('#status_chart').empty().append('<p class="text-danger">Нет данных.</p>');
        } else {
            var statusData = google.visualization.arrayToDataTable(A.statusDaily),
            ununsweredOptions = {
                title: 'Распределение по статусам',
                //curveType: 'function',
                legend: { position: 'bottom' }
            };
            var ununsweredChart = new google.visualization.LineChart(document.getElementById('status_chart'));
            ununsweredChart.draw(statusData, ununsweredOptions);

            ununsweredElem.empty();
            ununsweredElem.append(buildHtml(A.statusDaily));
        }

        if (A.siteCallsAll.length < 1) {
            $('#site_calls_all_chart').empty().append('<p class="text-danger">Нет данных.</p>');
        } else {
            var siteCallsAllData = google.visualization.arrayToDataTable(A.siteCallsAll);
            var siteCallsAllOptions = {
              title: 'Распределение звонков по сайтам (все)',
              is3D: true
            };
            var siteCallsAllChart = new google.visualization.PieChart(document.getElementById('site_calls_all_chart'));
            siteCallsAllChart.draw(siteCallsAllData, siteCallsAllOptions);
        }

        if (A.siteCallsNew.length < 1) {
            $('#site_calls_new_chart').empty().append('<p class="text-danger">Нет данных.</p>');
        } else {
            var siteCallsNewData = google.visualization.arrayToDataTable(A.siteCallsNew);
            var siteCallsNewOptions = {
              title: 'Распределение звонков по сайтам (новые)',
              is3D: true
            };
            var siteCallsNewChart = new google.visualization.PieChart(document.getElementById('site_calls_new_chart'));
            siteCallsNewChart.draw(siteCallsNewData, siteCallsNewOptions);
        }


        function buildHtml(arr) {
            var rows = 1;
            var table = '<table class="table table-bordered table-hover table-striped"><thead>';

            arr.forEach(function (line) {
                if (rows == 1) {
                    table += '<tr>';
                    for (var i=0; i<line.length; i++) {
                        table += '<th>' + line[i] + '</th >'
                    }
                    table += '</tr></thead><tbody>';
                } else {
                    table += '<tr>';
                    for (var j=0; j<line.length; j++) {
                        table += '<td>' + line[j] + '</td>';
                    }
                    table += '</tr>';
                }
                rows++;
            });

            table += '</tbody></table>';
            return table;
        }
    },

    callListInit : function() {
        A.updateNumCallComments();
        $('button[data-call-uid]').on('click', function(e) {
            var callUid = $(this).data('call-uid'),
            callDate = $(this).data('call-date');
            A.listenCall(callUid, callDate, this);
        });
        $('.addComment, .commentBadge').on('click', function(e) {
            A.openCommentsModal($(this).data('call-id'));
        });
    },

    listenCall : function(callUid, callDate, e) {
        $.post(A.checkWavUrl, {'call_uid': callUid, 'call_date': callDate}, function(response) {
            if (response.result == 'none') {
                $(e).removeClass('btn-default').addClass('btn-danger').prop('disabled', true);
            } else {
                $(e).removeClass('btn-default').addClass('btn-success');
                $('#playWavModal').modal('show');
                $('#playWavModal').on('hidden.bs.modal', function () {$('#playWavModalContents').empty();});
                var url = A.getWavUrl + '?call_date=' + callDate + '&call_uid=' + callUid;
                var contents = '<audio controls preload="auto"><source src="' + url  + '" type="audio/wav"></audio>';
                $('#playWavModalContents').empty().html(contents);
            }
        });
        //console.log(callUid);
    },

    openCommentsModal: function(callId) {
        $('#addCommentModal').modal('show');
        A.getCallComments(callId);
        $('#addCommentButton').prop('disabled', false);
        $('#commentModalCallId').val(callId);
        $('#commentsContentsField').val('');
    },

    getCallComments : function(callId) {
        $.post(A.callCommentsUrl, {'call_id': callId}, function(response) {
            $('#addCommentModalContents').empty()
                .append('<table class="table><thead><th>Автор</th>' +
                    '<th>Комментарий</th></thead><tbody>');
            $.each(response, function(k, v) {
                $('#addCommentModalContents').append(
                    '<tr><td><b>' + v.u +
                    '</b><br/><span style="font-size: 9px">' + v.ts + '</span></td><td>' + v.contents +
                    '</td></tr>');
            });
            $('#addCommentModalContents').append('</tbody></table>');
        });
    },

    updateNumCallComments : function() {
        $.post(A.numCommentsUrl, {'ids': A.callIds}, function(response) {
           $.each(response, function(k, v) {
               var call_id = v.cid;
               var num_comments = v.num;
               console.log(call_id);
               $('.commentBadge[data-call-id="' + call_id + '"]')
                   .text(num_comments).addClass('badge-success')
                   .addClass('label-as-badge');
           });
        });
    }
}