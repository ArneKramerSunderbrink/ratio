/**
 * Javascript code related to the admin interface.
 */

$(function() {
  // edit user
  $('div#user-list').on('submit', 'form', function() {
    const form = $(this);
    const list_item = form.closest('.item');
    const user_id = list_item.attr('data-user-id');
    const flipid = 'user-list-' + user_id;
    const data = form_to_object(this);
    data.user_id = user_id;

    postJSON(window.SCRIPT_ROOT + 'admin/_edit_user', data, function(data) {
      if (data.error) {
        $('div.message > span').text(data.error);
        $('div.message').css('display', '');
        form.find('input').first().focus();
      } else {
        //list_item.find('a:first').text(data.user_name);
        //data.user_is_admin  // todo admin button to all but only on admins display
        //todo edits to frontend
        flip_front(flipid);
      }
    });

    return false;
  });

  /*
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
  */
  // add user
  $('form#new-user-form').on('submit', function() {
    const form = $(this);
    const data = form_to_object(this);

    postJSON(window.SCRIPT_ROOT + 'admin/_add_user', data, function(data) {
      if (data.error) {
        $('div.message > span').text(data.error);
        $('div.message').css('display', '');
        form.find('input').first().focus();
      } else {
        // add user
        $('div#user-list').first().append($(data.user_row));
        // reset add user input
        form.reset();
        flip_front('new-user');
      }
    });

    return false;
  });
});