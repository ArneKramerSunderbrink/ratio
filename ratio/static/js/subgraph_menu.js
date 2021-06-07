/**
 * Javascript code related to the subgraph list:
 * Toggling finished-checkboxes,
 * editing subgraph names, adding new subgraphs, deleting subgraphs and undoing that delete.
 */

$(function() {
  // finished checkboxes
  $('div#subgraph-list').on('change', ':checkbox', function() {
    const finished = $(this).prop('checked');
    const subgraph_id = parseInt(this.id.substring(9));

    const link = $(this).prev();
    const menu_box = $('label[for="finished-'+subgraph_id+'"]').children('i');
    if (finished) {
      menu_box.removeClass().addClass('fa fa-check-square fa-lg');
      menu_box.prop('title', 'Finished');
      link.addClass('text-green');
    } else {
      menu_box.removeClass().addClass('fa fa-square fa-lg');
      menu_box.prop('title', 'Not finished');
      link.removeClass('text-green');
    }

    postJSON(window.SCRIPT_ROOT + '/_set_finished', {subgraph_id: subgraph_id, finished: finished}, function (data) {
      if (data.error) { alert(data.error); }
    });

    return false;
  });

  // edit subgraph name
  $('div#subgraph-list').on('submit', 'form', function() {
    const list_item = $(this).closest('.item');
    const subgraph_id = list_item.attr('data-subgraph-id');
    const flipid = 'subgraph-list-' + subgraph_id;
    const data = form_to_object(this);
    data.subgraph_id = subgraph_id;

    postJSON(window.SCRIPT_ROOT + '/_edit_subgraph_name', data, function(data) {
      if (data.error) {
        $('div#subgraph-menu-edit-msg').text(data.error);
        $('div#subgraph-menu-edit-msg').attr('data-flipid', flipid)
        $('div#subgraph-menu-edit-msg').css('display', 'block');
        list_item.find('form > input').focus();
      } else {
        list_item.find('a:first').text(data.name);
        flip_front(flipid);
      }
    });

    return false;
  });

  // delete subgraph
  $('div#subgraph-list').on('click', 'button.delete-subgraph-button', function() {
    const item = $(this).closest('.item');
    const subgraph_id = item.attr('data-subgraph-id');
    postJSON(window.SCRIPT_ROOT + '/_delete_subgraph', {subgraph_id: subgraph_id}, function(data) {
      if (data.error) {
        $('div#subgraph-menu-edit-msg').text(data.error);
        $('div#subgraph-menu-edit-msg').attr('data-flipid', 'subgraph-list-' + subgraph_id)
        $('div#subgraph-menu-edit-msg').css('display', 'block');
      } else {
        item.css('display', 'none');
        $('div#subgraph-menu-delete-msg').attr('data-subgraph-id', subgraph_id);
        $('div#subgraph-menu-delete-msg > span').text('"' + data.name + '" has been deleted.');
        $('div#subgraph-menu-delete-msg').css('display', 'block');
      }
    });

    return false;
  });

  // undo delete Subgraph
  $('div#subgraph-menu-delete-msg > a').on('click', function() {
    const subgraph_id = this.parentNode.getAttribute('data-subgraph-id');
    const item = $('div#subgraph-list > div.item[data-subgraph-id="' + subgraph_id + '"]')
    postJSON(window.SCRIPT_ROOT + '/_undo_delete_subgraph', {subgraph_id: subgraph_id}, function(data) {
      if (data.error) {
        alert(data.error);  // if everything runs correctly this will never happen
      } else {
        item.css('display', 'block');
        $('div#subgraph-menu-delete-msg').css('display', 'none');
      }
    });

    return false;
  });

// add subgraph
  $('form#new-subgraph-form').on('submit', function() {
    const data = form_to_object(this);

    postJSON(window.SCRIPT_ROOT + '/_add_subgraph', data, function(data) {
      if (data.error) {
        $('div#subgraph-menu-add-msg').text(data.error);
        $('div#subgraph-menu-add-msg').css('display', 'block');
        $('input#new-subgraph-name').focus();
      } else {
        window.location = data.redirect;
      }
    });

    return false;
  });
});