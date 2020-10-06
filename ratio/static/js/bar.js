// finished checkbox
$(function() {
  $('input#finished').bind('change', function() {
    var finished = $(this).is(':checked');

    if (finished) {
      $("label[for='finished']").children('i').removeClass().addClass('fa fa-check-square');
    } else {
      $("label[for='finished']").children('i').removeClass().addClass('fa fa-square');
    }

    $.getJSON($SCRIPT_ROOT + '_set_finished', {subgraph_id: $SUBGRAPH_ID, finished: finished})
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });
});