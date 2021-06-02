$(document).ready( function () {
    //const csrftoken = Cookies.get('csrftoken');

    /* Change Bulma tabs */
    let $tabs = $('.tabs li');
    let $tabsContent = $('.tab-content');
    let sessionStorage = window.sessionStorage;

    $tabs.click(function () {
            $tab = $(this);
            $tabContent = $($tabsContent.get($tab.index()));
            sessionStorage.setItem('selectedTab', $tab.index());
            $tabs.removeClass('is-active');
            $tabsContent.removeClass('is-active');
            $tab.addClass('is-active');
            $tabContent.addClass('is-active');
    });

    let selectedTab = sessionStorage.getItem('selectedTab');
    if (!$tabs.hasClass('is-active')) {
        if (selectedTab) {
            $tabs.get(selectedTab).click();
        } else {
            $tabs.get(0).click();
        }
    }

    /* Render Templates */
    var ac_tmpl = $.templates("#addCar");
    var ct_tmpl = $.templates("#carTbl");
    $("#addCar_tmpl").html(ac_tmpl.render());
    $("#carTbl_cars_tmpl").html(ct_tmpl.render({name: "cars"}));
    $("#carTbl_runs_tmpl").html(ct_tmpl.render({name: "runs"}));

    /* Create and format jQuery DataTables */
    let cars_optDef = function(pageLength=0) {
        let optDef = {
            lengthMenu: [ [5, 8, 10, 14, 25, 50, -1], [5, 8, 10, 14, 25, 50, "All"] ],
            columns: [
                { name: 'number' },
                { name: 'name' }
            ]
        }
        if (pageLength) { optDef.pageLength = pageLength}
        return optDef;
    };
    let cars = $('#cars_cars').DataTable(cars_optDef(14));
    let cars_runs = $('#cars_runs').DataTable(cars_optDef(8));
    let cars_num = cars.column('number:name').data();
    let cars_name = cars.column('name:name').data();

    swapElements($('#cars_cars_wrapper .columns .column.is-one-half'), 0, 1);
    swapElements($('#cars_runs_wrapper .columns .column.is-one-half'), 0, 1);
    $('.dataTables_length,.dataTables_filter').css('margin-bottom','7px');
    $('.dataTables_length').css("text-align","right").css("float","right");
    $('.dataTables_filter').css("text-align","left").css("float","left").css("width","50%");
    $('.dataTables_filter input').css("width","100%");

    /* enable select on tables */
    $('#cars_runs tbody').delegate("tr", "click", function() {
        if (!$(this).hasClass("selected")) {
            cars_runs.rows().nodes().to$().removeClass('selected');
            $(this).addClass('selected');
        } else {
            $(this).removeClass('selected');
        }
    });
    $('#cars_cars tbody').delegate("tr", "click", function() {
        if (!$(this).hasClass("selected")) {
            cars.rows().nodes().to$().removeClass('selected');
            $(this).addClass('selected');
        } else {
            $(this).removeClass('selected');
        }
    });




    /* Runs tab functions */

    //Set track car
    let sTracksData = {};
    $('.addToTrack').click(function () {
        let $btn = $(this);
        const track_id = $btn.attr('id');
        let selectedRows = cars_runs.rows('.selected').data().toArray();
        if (selectedRows.length == 1) {
            let sCar = selectedRows[0];
            let newTrackData = {
                car_id: sCar[0],
                car_name: sCar[1]
            }

            /* If car was already selected, and not for the current track, remove it on the old track */
            let exists_id
            let exists = Object.keys(sTracksData).some(function(k) {
                exists_id = k;
                return _.isEqual(sTracksData[k], newTrackData);
            });
            if (exists && exists_id !== track_id) {
                delete sTracksData[exists_id];
                let $oldTrack = $("#addToTrack_" + exists_id);
                $oldTrack.find(".track_car_id").html("-");
                $oldTrack.find(".track_car_name").addClass("invisible").html("-");
                //console.log("Car already selected");
            }

            /* If car was already selected for current track, do nothing */
            let oldTrackData = sTracksData[track_id];
            if (!_.isEqual(newTrackData, oldTrackData)) {
                /* If another car was already selected for this track, remove the .selected_track class  for that car in the table */
                if (oldTrackData) {
                    let oldTrackCar = cars_runs.rows(":contains('"+ oldTrackData.car_id + "'):contains('"+ oldTrackData.car_name + "')").nodes().to$();
                    oldTrackCar.removeClass("selected_track");
                    //console.log("Another car previously selected");
                }
                //console.log("Adding New Track");
                sTracksData[track_id] = newTrackData;
                let $newTrack = $("#addToTrack_" + track_id);
                $newTrack.find(".track_car_id").html(newTrackData.car_id);
                $newTrack.find(".track_car_name").removeClass("invisible").html(newTrackData.car_name);
                cars_runs.rows('.selected').nodes().to$().addClass("selected_track");
            }

            /* Check if at least one track has been filled */
            if (sTracksData.length) {
                $("#post_run").attr("disabled", "True");
            } else {
                $("#post_run").removeAttr("disabled");
            }
        }
    });



    function runToggles() {
        $('.addToTrack_field').slideToggle();
        $('#new_run,#post_run').toggle();
    }
    function addRunToggles() {
        runToggles();
        $('#carTbl_runs_tmpl').fadeToggle(()=> {
            $('#results_card').fadeToggle();
        });
    }
    function newRunToggles() {
        runToggles();
        $('#results_card').fadeToggle(()=> {
            $('#carTbl_runs_tmpl').fadeToggle();
        });
    }

    //Start run -> POST add_run
    $("#post_run").click(function () {
        addRunToggles();
        RACETRACK.RACE_UPDATES_SOCKET.send(JSON.stringify({
            'type': 'start_run',
            'data': sTracksData
        }));
    });

    //New run -> reset variables
    $("#new_run").click(function () {
        newRunToggles();
        $("#post_run").attr("disabled", "True");

        /* Bump run number in title */
        $run_title = $("#run_title");
        $run_title.html("Run #" + (RACETRACK.CURRENT_RUN + 1));

        /* Clear track data */
        sTracksData = {};
        $tracks = $(".run_track");
        $tracks.find(".track_car_id").html("-");
        $tracks.find(".track_car_name").addClass("invisible").html("-");

        /* Remove table selection classes */
        cars_runs.rows().nodes().to$().removeClass(["selected_track","selected"]);
        cars_runs.search( '' ).columns().search( '' ).draw();
    });

    /* AddCar Validation */
    $('#car_number').on('input', function() {
        let value = $(this).val();
        let help = $('#car_number_help');
        let integer = /^-?\d+$/.test(value);
        let inArray = $.inArray(value, cars_num.toArray()) !== -1;
        if (!value) {
            help.html("-");
            help.removeClass('is-danger').addClass('invisible');
        } else if (!integer) {
            help.html("Invalid number");
            help.removeClass('invisible').addClass('is-danger');
        } else if (inArray) {
            help.html("#" + value + " is taken");
            help.removeClass('invisible').addClass('is-danger');
        } else {
            help.html("-");
            help.removeClass('is-danger').addClass('invisible');
        }
    });


});

/**
 * @param subjectIndex {int} Index of the item to be moved
 * @param objectIndex {int} Index of the item to move subject after
 * @param siblings {jQuery} List of sibling elements to act upon
 */
var swapElements = function(siblings, subjectIndex, objectIndex) {
    // Get subject jQuery
    var subject = $(siblings.get(subjectIndex));
    // Get object element
    var object = siblings.get(objectIndex);
    // Insert subject after object
    subject.insertAfter(object);
}


/*
$.ajax({
    url: url,
    type: "POST",
    data: sTracksData,
    beforeSend: function (xhr) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
    },
    success: function (data) {
        console.log(data);
        $("#run_title").attr("data-current-run", data.run_num + 1);
        $("#race_runs").html(data.run_num);
    },
    error: function (error) {
        console.log(error);
    }
});*/
/*    let RACE_ID = $('#data_div').attr("data-race-id");
    let updateSocket;
    function connectSocket() {
        updateSocket = new WebSocket(
            'ws://' + window.location.host +
            '/ws/race/' + RACE_ID + '/detail');
        updateSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            console.log("Received a message from the socket:", data);
            if (data.run_num) {
                $("#run_title").attr("data-current-run", data.run_num + 1);
                $("#race_runs").html(data.run_num);
            }
            if (data.run_results) {
                for (const [track, trial] of Object.entries(data.run_results)) {
                  let $track = $('#track_'+ track);
                  for (const [k,v] of Object.entries(trial)) {
                    if (!v) { break; }
                    $track.find('.track_car_' + k).removeClass('invisible').html(v);
                  }
                }
            }
        };
        updateSocket.onclose = function(e) {
            console.error('Chat socket closed unexpectedly; reconnecting');
            setTimeout(connectSocket, 1000);
        };
        updateSocket.onopen = function(e) {
            console.log("Socket connected");
        }
    }
    connectSocket();*/