// toggle overlay
$(function() {
  $('a#subgraph_name').bind('click', function() {
    overlay = $('div#overlay');
    if (overlay.css('display') == 'none') {
      overlay.css('display', 'block');
    } else {
      overlay.css('display', 'none');
    }

    return false
  })
})

// finished checkboxes
function toggle_finished() {
  var id = this.id;
  var finished = $(this).is(':checked');

  alert(id);

  if (id == 'finished') {
    subgraph_id = $SUBGRAPH_ID;
  } else {
    subgraph_id = parseInt(id.substring(9));
  }

  alert(subgraph_id);

  // change checkbox in the subgraph menu
  if (finished) {
    $("label[for='finished-"+subgraph_id+"']").children('i').removeClass().addClass('fa fa-check-square');
  } else {
    $("label[for='finished-"+subgraph_id+"']").children('i').removeClass().addClass('fa fa-square');
  }

  // change checkbox in the header
  if (subgraph_id == $SUBGRAPH_ID) {
    if (finished) {
      $("label[for='finished']").children('i').removeClass().addClass('fa fa-check-square');
    } else {
      $("label[for='finished']").children('i').removeClass().addClass('fa fa-square');
    }
  }

  $.getJSON($SCRIPT_ROOT + '_set_finished', {subgraph_id: subgraph_id, finished: finished})
  .fail(function() { alert('getJSON request failed!'); });

  return false;
}

$(function() {
  $('input#finished').bind('change', toggle_finished);
  $('div#subgraph-list').find(':checkbox').bind('change', toggle_finished);
});