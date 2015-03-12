(function() {
    "use strict";
    console.info('Welcome to skim.');

    function updateTimes() {
        var times = document.querySelectorAll('time');
        Array.prototype.forEach.call(times, function(time) {
            time.innerText = moment(time.dataset.iso).fromNow();
        });
    }
    setInterval(updateTimes, 60*1000);
    document.addEventListener('DOMContentLoaded', updateTimes);
    updateTimes();
}(moment));
