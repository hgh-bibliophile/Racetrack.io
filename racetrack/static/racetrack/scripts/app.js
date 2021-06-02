$(document).ready( function () {
    window.RACETRACK = {
        RACE_ID:  $("meta[name='race-id']").attr("content"),
        CURRENT_RUN: $("meta[name='current-run']").attr("content")

    }

    /* Render Templates */
    var rc_tmpl = $.templates("#resultsCard");
    $("#resultsCard_tmpl").html(rc_tmpl.render());

    function connectSocket() {
        RACETRACK.RACE_UPDATES_SOCKET = new WebSocket(
            'ws://' + window.location.host +
            '/ws/race/' + RACETRACK.RACE_ID);
        RACETRACK.RACE_UPDATES_SOCKET.onmessage = function(e) {
            const data = JSON.parse(e.data);
            console.log("Received a message from the socket:", data);
            //customize
            if (data.run_num) {
                RACETRACK.CURRENT_RUN = data.run_num;
                $(".run_title").html("Run #" + RACETRACK.CURRENT_RUN);
                $(".race_runs").html(RACETRACK.CURRENT_RUN);
                $tracks = $("#results_tracks");
                $tracks.find(".track_car").addClass("invisible").html("-");
                $tracks.find(".track_car_number").removeClass("invisible");
            }
            if (data.run_results) {
                for (const [track, trial] of Object.entries(data.run_results)) {
                  let $track = $('#track_'+ track);
                  for (const [key,val] of Object.entries(trial)) {
                    if (!val) { break; }
                    $track.find('.track_car_' + key).removeClass('invisible').html(val);
                  }
                }
            }
            //customize
        };
        RACETRACK.RACE_UPDATES_SOCKET.onclose = function(e) {
            console.error('Chat socket closed unexpectedly; reconnecting');
            setTimeout(connectSocket, 1000);
        };
        RACETRACK.RACE_UPDATES_SOCKET.onopen = function(e) {
            console.log("Socket connected");
        }
    };
    connectSocket();
});