/**
 * Javascript code related to the subgraph list:
 * Toggling the finished-checkboxes,
 * editing subgraph names, adding new subgraphs, deleting subgraphs and undoing that delete.
 */

// finished checkboxes
$(function() {
  $('div#subgraph-list').on('change', ':checkbox', function() {
    var finished = $(this).prop('checked');
    var subgraph_id = parseInt(this.id.substring(9));

    // change checkbox in the subgraph menu
    var menu_box = $('label[for="finished-'+subgraph_id+'"]').children('i');
    if (finished) {
      menu_box.removeClass().addClass('fa fa-check-square fa-lg');
      menu_box.prop('title', 'Finished');
    } else {
      menu_box.removeClass().addClass('fa fa-square fa-lg');
      menu_box.prop('title', 'Not finished');
    }

    $.getJSON($SCRIPT_ROOT + '/_set_finished', {subgraph_id: subgraph_id, finished: finished}, function (data) {
      if (data.error) { alert(data.error); }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });
});

// edit subgraph name
$(function() {
  $('div#subgraph-list').on('submit', 'form', function() {
    var data = $(this).serializeArray();
    var list_item = $(this.parentNode.parentNode);
    var subgraph_id = list_item.attr('data-subgraph-id')
    var flipid = 'subgraph-list-' + subgraph_id;
    data.push({ name: 'subgraph_id', value: subgraph_id });

    $.getJSON($SCRIPT_ROOT + '/_edit_subgraph_name', data, function(data) {
      if (data.error) {
        $('div#subgraph-menu-edit-msg').text(data.error);
        $('div#subgraph-menu-edit-msg').attr('data-flipid', flipid)
        $('div#subgraph-menu-edit-msg').css('display', 'block');
        list_item.find('form > input').focus();
      } else {
        if (subgraph_id == $SUBGRAPH_ID) {
          $('a#subgraph-name').text(data.name);
        }
        list_item.children().eq(0).children().eq(0).text(data.name);
        flip_front(flipid);
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });
});

// delete subgraph
$(function() {
  $('div#subgraph-list').on('click', 'form > a.delete-subgraph-button', function() {
    var item = $(this.parentNode.parentNode.parentNode);
    var subgraph_id = item.attr('data-subgraph-id');
    $.getJSON($SCRIPT_ROOT + '/_delete_subgraph', {subgraph_id: subgraph_id}, function(data) {
      if (data.error) {
        $('div#subgraph-menu-edit-msg').text(data.error);
        $('div#subgraph-menu-edit-msg').attr('data-flipid', 'subgraph-list-' + subgraph_id)
        $('div#subgraph-menu-edit-msg').css('display', 'block');
      } else {
        if (subgraph_id == $SUBGRAPH_ID) {
          // prevent user from going back to editing the subgraph
          $('a#close-overlay').css('display', 'none');
          $(document).off('keyup', overlay_escape_handler);
        }
        item.css('display', 'none');
        $('div#subgraph-menu-delete-msg').attr('data-subgraph-id', subgraph_id);
        $('div#subgraph-menu-delete-msg > span').text('"' + data.name + '" has been deleted.');
        $('div#subgraph-menu-delete-msg').css('display', 'block');
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });
});

// undo delete Subgraph
$(function() {
  $('div#subgraph-menu-delete-msg > a').on('click', function() {
    var subgraph_id = this.parentNode.getAttribute('data-subgraph-id');
    var item = $('div#subgraph-list > div.item[data-subgraph-id="' + subgraph_id + '"]')
    $.getJSON($SCRIPT_ROOT + '/_undo_delete_subgraph', {subgraph_id: subgraph_id}, function(data) {
      if (data.error) {
        alert(data.error);  // if everything runs correctly this will never happen
      } else {
        if (subgraph_id == $SUBGRAPH_ID) {
          $('a#close-overlay').css('display', 'block');
          $(document).on('keyup', overlay_escape_handler);
        }
        item.css('display', 'block');
        $('div#subgraph-menu-delete-msg').css('display', 'none');
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });
});

// add subgraph
$(function() {
  $('form#new-subgraph-form').on('submit', function() {
    var data = $(this).serialize();

    $.getJSON($SCRIPT_ROOT + '/_add_subgraph', data, function(data) {
      if (data.error) {
        $('div#subgraph-menu-add-msg').text(data.error);
        $('div#subgraph-menu-add-msg').css('display', 'block');
        $('input#new-subgraph-name').focus();
      } else {
        window.location = data.redirect;
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });
});