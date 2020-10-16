// toggle edit knowledge
function display_edit_knowledge() {
  var id = parseInt(this.id.substring(5));  // 'edit-123' without 'edit-'
  $(this).parent().parent().css('display', 'none');
  $('form#edit-knowledge-form-' + id).parent().css('display', 'table-row');
  return false;
}

function hide_edit_knowledge() {
  var id = parseInt(this.id.substring(12));  // 'cancel-edit-123' without 'cancel-edit-'
  $('form#edit-knowledge-form-' + id).parent().css('display', 'none');
  $('a#edit-' + id).parent().parent().css('display', 'table-row');
  return false;
}

$(function() {
  var as, i, id;
  as = $('a[id^="edit-"]');
  for (i = 0; i < as.length; i++) {
    $(as[i]).bind('click', display_edit_knowledge);
  }
  as = $('a[id^="cancel-edit-"]');
  for (i = 0; i < as.length; i++) {
    $(as[i]).bind('click', hide_edit_knowledge);
  }
});

// edit knowledge
function edit_knowledge() {
  alert('test');
  var data = $(this).serialize();
  alert(data);
  // todo
  return false;
}

$(function() {
  var forms, i, id;
  forms = $('form[id^="edit-knowledge-form-"]');
  for (i = 0; i < forms.length; i++) {
    $(forms[i]).submit(edit_knowledge);
  }
});

// delete knowledge
function delete_knowledge() {
  var id = parseInt(this.id.substring(7));  // 'delete-123' without 'delete-'
  alert(id);
  // todo
  return false;
}

$(function() {
  var as, i, id;
  as = $('a[id^="delete-"]');
  for (i = 0; i < as.length; i++) {
    $(as[i]).bind('click', delete_knowledge);
  }
});

// add knowledge
$(function() {
  $('form#new-knowledge-form').submit(function() {
    var data = $(this).serialize();

    $.getJSON($SCRIPT_ROOT + '_add_knowledge', data, function(data) {
      if (data.error) {
        alert(data.error); //todo add element to page to display error
      } else {
        // add row to table above the form
        $('form#new-knowledge-form').parent().before(data.knowledge_row);

        $('a#edit-' + data.knowledge_id).bind('click', display_edit_knowledge);
        $('form#edit-knowledge-form-' + data.knowledge_id).submit(edit_knowledge);
        $('a#delete-' + data.knowledge_id).bind('click', delete_knowledge);
        $('a#cancel-edit-' + data.knowledge_id).bind('click', hide_edit_knowledge);

        $('form#new-knowledge-form')[0].reset();
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });
});