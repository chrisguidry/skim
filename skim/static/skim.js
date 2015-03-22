(function() {
  "use strict";
  console.info('Welcome to skim.');

  function localizeTimes() {
    var times = document.querySelectorAll('time');
    Array.prototype.forEach.call(times, function(time) {
      var timestamp = moment(time.dataset.iso);
      time.innerText = timestamp.fromNow();
      time.setAttribute('title', timestamp.format('LLL'));
    });
  }
  function updateTimes() {
    var times = document.querySelectorAll('time');
    Array.prototype.forEach.call(times, function(time) {
      time.innerText = moment(time.dataset.iso).fromNow();
    });
  }
  setInterval(updateTimes, 60*1000);
  document.addEventListener('DOMContentLoaded', localizeTimes);
  localizeTimes();
}(moment));
