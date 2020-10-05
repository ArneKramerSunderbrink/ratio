$(function() {
  $('a#finished').bind('click', function() {
    alert('TEST');
    // todo send change finished to backend
    // todo change icon
    // siehe https://flask.palletsprojects.com/en/1.1.x/patterns/jquery/
    return false;
  });
});