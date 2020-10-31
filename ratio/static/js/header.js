// toggle overlay
function toggle_overlay() {
  overlay = $('div#overlay');
  if (overlay.css('display') == 'none') {
    overlay.css('display', 'block');
  } else {
    overlay.css('display', 'none');
  }

  return false;
}

$(function() {
  $('a#subgraph-name').on('click', toggle_overlay);
  $('a#close-overlay').on('click', toggle_overlay);
  $(document).on('keyup', function(e) {
    if (e.key === "Escape" && $('div#overlay').css('display') == 'block' && $SUBGRAPH_ID != 0) {
      toggle_overlay();
    }
  });
});

// finished checkboxes
function toggle_finished() {
  var id = this.id;
  var finished = $(this).is(':checked');

  if (id == 'finished') {
    subgraph_id = $SUBGRAPH_ID;
  } else {
    subgraph_id = parseInt(id.substring(9));
  }

  // change checkbox in the subgraph menu
  var menu_box = $("label[for='finished-"+subgraph_id+"']").children('i');
  if (finished) {
    menu_box.removeClass().addClass('fa fa-check-square fa-lg');
    menu_box.prop('title', 'Finished');
  } else {
    menu_box.removeClass().addClass('fa fa-square fa-lg');
    menu_box.prop('title', 'Not finished');
  }

  // change checkbox in the header
  if (subgraph_id == $SUBGRAPH_ID) {
    var header_box = $("label[for='finished']").children('i');
    if (finished) {
      header_box.removeClass().addClass('fa fa-check-square');
    } else {
      header_box.removeClass().addClass('fa fa-square');
    }
  }

  $.getJSON($SCRIPT_ROOT + '/_set_finished', {subgraph_id: subgraph_id, finished: finished})
  .fail(function() { alert('getJSON request failed!'); });

  return false;
}

$(function() {
  $('input#finished').on('change', toggle_finished);
  $('div#subgraph-list').on('change', ':checkbox', toggle_finished);
});