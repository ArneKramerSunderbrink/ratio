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

    postJSON(window.SCRIPT_ROOT + '/admin/_edit_user', data, function(data) {
      if (data.error) {
        $('div.message:first > span').text(data.error);
        $('div.message:first').css('display', '');
        form.find('input').first().focus();
      } else {
        list_item.find('div.flip-frontside > div > div > span').text(data.user_name);
        if (data.user_is_admin) {
          list_item.find('div.flip-frontside > div > div > i').css('display', '');
        } else {
          list_item.find('div.flip-frontside > div > div > i').css('display', 'none');
        }
        flip_front(flipid);
      }
    });

    return false;
  });


  // delete user
  $('div#user-list').on('click', 'button.delete-user-button', function() {
    const item = $(this).closest('.item');
    const user_id = item.attr('data-user-id');
    postJSON(window.SCRIPT_ROOT + '/admin/_delete_user', {user_id: user_id}, function(data) {
      if (data.error) {
        $('div.message:first > span').text(data.error);
        $('div.message:first').css('display', '');
      } else {
        item.css('display', 'none');
        $('div#user-delete-msg').attr('data-user-id', user_id);
        $('div#user-delete-msg > span').text('"' + data.name + '" has been deleted.');
        $('div#user-delete-msg').css('display', '');
      }
    });

    return false;
  });

  // undo delete user
  $('div#user-delete-msg > button:first').on('click', function() {
    const user_id = this.parentNode.getAttribute('data-user-id');
    const item = $('div#user-list > div.item[data-user-id="' + user_id + '"]')
    postJSON(window.SCRIPT_ROOT + '/admin/_undo_delete_user', {user_id: user_id}, function(data) {
      if (data.error) {
        $('div.message:first > span').text(data.error);
        $('div.message:first').css('display', '');
      } else {
        item.css('display', 'block');
        $('div#user-delete-msg').css('display', 'none');
      }
    });

    return false;
  });

  // add user
  $('form#new-user-form').on('submit', function() {
    const form = this;
    const data = form_to_object(form);

    postJSON(window.SCRIPT_ROOT + '/admin/_add_user', data, function(data) {
      if (data.error) {
        $('div.message:first > span').text(data.error);
        $('div.message:first').css('display', '');
        $(form).find('input').first().focus();
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