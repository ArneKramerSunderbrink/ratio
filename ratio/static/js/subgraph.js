// toggle edit knowledge
function display_edit_knowledge() {
  var knowledge_id = parseInt(this.id.substring(5));  // 'edit-123' without 'edit-'
  $('tr#tr-' + knowledge_id).css('display', 'none');
  $('tr#tr-edit-' + knowledge_id).css('display', 'table-row');
  return false;
}

function hide_edit_knowledge() {
  var knowledge_id = parseInt(this.id.substring(12));  // 'cancel-edit-123' without 'cancel-edit-'
  $('tr#tr-' + knowledge_id).css('display', 'table-row');
  $('tr#tr-edit-' + knowledge_id).css('display', 'none');
  return false;
}

$(function() {
  var as, i;
  as = $('a[id^="edit-"]'); // todo more efficient with $(subgraph).on('click', 'a[id^="edit-"]', display_edit_knowledge)
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
  var data = $(this).serializeArray();
  var knowledge_id = parseInt(this.id.substring(20));  // 'edit-knowledge-form-123' without 'edit-knowledge-form-'
  data.push({ name: "knowledge_id", value: knowledge_id });
  data.push({ name: "subgraph_id", value: $SUBGRAPH_ID });

  $.getJSON($SCRIPT_ROOT + '/_edit_knowledge', data, function(data) {
    if (data.error) {
      alert(data.error); //todo add element to page to display error
    } else {
      $('tr#tr-' + knowledge_id).children().eq(0).text(data.subject);
      $('tr#tr-' + knowledge_id).children().eq(1).text(data.predicate);
      $('tr#tr-' + knowledge_id).children().eq(2).text(data.object);
      $('tr#tr-' + knowledge_id).css('display', 'table-row');
      $('tr#tr-edit-' + knowledge_id).css('display', 'none');
    }
  })
  .fail(function() { alert('getJSON request failed!'); });

  return false;
}

$(function() {
  var forms, i;
  forms = $('form[id^="edit-knowledge-form-"]');
  for (i = 0; i < forms.length; i++) {
    $(forms[i]).submit(edit_knowledge);
  }
});

// delete knowledge
function delete_knowledge() {
  var knowledge_id = parseInt(this.id.substring(7));  // 'delete-123' without 'delete-'

  // todo: add a "are you sure?" - dialog?

  $.getJSON($SCRIPT_ROOT + '/_delete_knowledge', {knowledge_id: knowledge_id, subgraph_id: $SUBGRAPH_ID}, function(data) {
      if (data.error) {
        alert(data.error); //todo add element to page to display error
      } else {
        // remove the corresponding rows
        $('tr#tr-' + knowledge_id).remove();
        $('tr#tr-edit-' + knowledge_id).remove();
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

  return false;
}

$(function() {
  var as, i;
  as = $('table a[id^="delete-"]');
  for (i = 0; i < as.length; i++) {
    $(as[i]).bind('click', delete_knowledge);
  }
});

// add knowledge
$(function() {
  $('form#new-knowledge-form').submit(function() {
    var data = $(this).serializeArray();
    data.push({ name: "subgraph_id", value: $SUBGRAPH_ID });

    $.getJSON($SCRIPT_ROOT + '/_add_knowledge', data, function(data) {
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