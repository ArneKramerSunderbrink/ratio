$(function() {
  $('a#finished').bind('click', function() {
    alert('TEST');
    // todo send change finished to backend
    // todo change icon
    return false;
  });
});

$(function() {
  $('button#script_root_test').bind('click', function() {
    $.getJSON($SCRIPT_ROOT + '/_test', {
      arg: 'script root'
    }, function(data) {
      alert(data.result);
    });
    return false;
  });
});

$(function() {
  $('button#config_test').bind('click', function() {
    $.getJSON($CONFIG + '/_test', {
      arg: 'config'
    }, function(data) {
      alert(data.result);
    });
    return false;
  });
});

$(function() {
  $('button#url_for_test').bind('click', function() {
    $.getJSON($URL_FOR + '_test', {
      arg: 'url_for'
    }, function(data) {
      alert(data.result);
    });
    return false;
  });
});