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

  var userList = new List('subscriptions', {
    page: 10000,
    valueNames: ['feed', 'entries', 'newest', 'oldest']
  });
  userList.on('updated', function() {
    localizeTimes();
  });
}(moment));

(function() {
  "use strict";

  function subscribe() {
    var subscribeInput = document.getElementById('subscribe'),
        feedUrl = subscribeInput.value.trim(),
        xhr;
    if (!feedUrl) {
      return;
    }

    subscribeInput.setAttribute('disabled', 'disabled');
    xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
      if (xhr.readyState < 4) { return; }
      if (xhr.status >= 400) {
        console.warn('TODO: handle error', xhr);
      } else {
        subscribeInput.value = '';
      }
      subscribeInput.removeAttribute('disabled');
    }
    xhr.open('POST', '/subscriptions', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify({
      'url': feedUrl
    }));
  }
  function bindSubscribe() {
    var subscribeInput = document.getElementById('subscribe');
    if (!subscribeInput) {
      return;
    }
    subscribeInput.addEventListener('keyup', function(evt) {
      if (evt.keyCode === 13) {
        subscribe();
      }
    });
  }
  document.addEventListener('DOMContentLoaded', bindSubscribe);
}());
