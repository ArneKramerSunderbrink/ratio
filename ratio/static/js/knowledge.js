/**
 * Javascript code related to the dynamic display and editing of knowledge:
 * todo
 */

$(function () {
  // Add value
  $('div#scroll-container').on('click', 'div.field > div > a', function() {
    var property_uri = $(this).closest('div.field').attr('data-property-uri');
    var entity_uri = $(this).closest('div.entity').attr('data-entity-uri');
    var data = [
      { name: "subgraph_id", value: window.SUBGRAPH_ID },
      { name: "property_uri", value: property_uri },
      { name: "entity_uri", value: entity_uri }
    ];

    $.getJSON(window.SCRIPT_ROOT + '/_add_value', data, function(data) {
      if (data.error) {
        alert(data.error); //todo add element to page to display error
      } else {
        var entity = $('div.entity[data-entity-uri="' + data.entity_uri + '"]');
        var field = entity.find('div.field[data-property-uri="' + data.property_uri + '"]');
        var list = field.find('div.field-value-list');
        list.append(data.value_div);
        list.children().last().find('.literal-input, .option-input').focus();
        if (data.remove_plus) {
          field.children('div').children('a').css('display', 'none');
        }
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;

  });

  // Delete Value
  $('div#scroll-container').on('click', '.delete-value-button', function() {
    var form = $(this).closest('form');
    form.css('display', 'none');
    // TODO communicate deletion to server
    // Display message
    $('div#knowledge-delete-msg > span').text('Value has been deleted.');
    $('div#knowledge-delete-msg > a:first').off('click');
    $('div#knowledge-delete-msg > a:first').on('click', function() {
      form.css('display', '');
      // TODO communicate undo to server
      $('div#knowledge-delete-msg').css('display', 'none');
      return false;
    });
    $('div#knowledge-delete-msg').css('display', 'flex');
    return false;
  });

  $('div#knowledge-delete-msg > a:last').on('click', function() {
    $('div#knowledge-delete-msg').css('display', 'none');
    return false;
  });

  // Special functionality for Options-Fields
  // Filter
  $('div#scroll-container').on('keyup', 'input.option-input', function() {
    var filter_string = this.value.toUpperCase();
    $(this).next('.options').find('.option').each(function() {
      if ($(this).text().toUpperCase().indexOf(filter_string) > -1) {
        $(this).css('display', '');
      } else {
        $(this).css('display', 'none');
      }
    });
  });
  $('div#scroll-container').on('focus', 'input.option-input', function() {
    $(this).next('.options').find('.option').each(function() {
      $(this).css('display', '');
    });
  });

  // Select option
  $('div#scroll-container').on('click', '.option', function() {
    var input = $(this).parent().parent('.options').prev('.option-input')
    input.val($(this).text());
    input.get(0).setCustomValidity('');
  });

  // Mark option invalid
  // I found no way to discriminate between focus switching within the form (to the custom option input)
  // or out of the form and only then check validity
  $('div#scroll-container').on('focusout', 'form.option-form', function() {
    // if value not in options, .setCustomValidity("Invalid option.")
    var input = $(this).find('.option-input')[0];
    if (input.value == '' || input.value && $(this).find('.option').text().includes(input.value)) {
      input.setCustomValidity('');
      // TODO communicate choice to server
    } else {
      input.setCustomValidity('Choose an option from the list.');
    }
  });

  // Add entity
  $('div#scroll-container').on('submit', 'form.add-entity-form', function() {
    var field = $(this).closest('div.entity-field');
    var property_uri = field.attr('data-property-uri');
    var entity_uri = $(this).closest('div.entity').attr('data-entity-uri');
    var data = $(this).serializeArray();
    data.push({ name: "subgraph_id", value: window.SUBGRAPH_ID });
    data.push({ name: "property_uri", value: property_uri });
    data.push({ name: "entity_uri", value: entity_uri });

    $.getJSON(window.SCRIPT_ROOT + '/_add_entity', data, function(data) {
      if (data.error) {
        alert(data.error);
      } else {
        // add entity
        var list = field.find('div.entity-field-value-list').first();
        list.append(data.entity_div);
        // expand entity body
        flip_flip(list.children().last().find('.entity-title > a:first').attr('data-flipid'));
        // reset add entity input
        field.find('form.add-entity-form').first()[0].reset();
        flip_front(field.find('div.add-entity-div > div.flip-flipside').first().attr('data-flipid'));
        if (data.remove_plus) {
          field.find('add-entity-div').css('display', 'none');
        }
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });

  // Delete entity
  $('div#scroll-container').on('click', 'a.delete-entity-button', function() {
    var entity = $(this).closest('div.entity');
    var entity_uri = entity.attr('data-entity-uri');
    var data = [
      { name: "subgraph_id", value: window.SUBGRAPH_ID },
      { name: "entity_uri", value: entity_uri }
    ];

    $.getJSON(window.SCRIPT_ROOT + '/_delete_entity', data, function(data_return) {
      if (data_return.error) {
        alert(data_return.error);
      } else {
        // Remove entity div
        entity.css('display', 'none')
        // Display message
        $('div#knowledge-delete-msg > span').text('Entity has been deleted.');
        $('div#knowledge-delete-msg > a:first').off('click');
        $('div#knowledge-delete-msg > a:first').on('click', function() {
          $.getJSON(window.SCRIPT_ROOT + '/_undo_delete_entity', data, function(data_return) {
            if (data_return.error) {
              alert(data_return.error);
            } else {
              entity.css('display', '');
              $('div#knowledge-delete-msg').css('display', 'none');
            }
          })
          .fail(function() { alert('getJSON request failed!'); });
          return false;
        });
        $('div#knowledge-delete-msg').css('display', 'flex');
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });

});


/*
// edit knowledge
function edit_knowledge() {
  var data = $(this).serializeArray();
  var knowledge_id = parseInt(this.id.substring(20));  // 'edit-knowledge-form-123' without 'edit-knowledge-form-'
  data.push({ name: "knowledge_id", value: knowledge_id });
  data.push({ name: "subgraph_id", value: window.SUBGRAPH_ID });

  $.getJSON(window.SCRIPT_ROOT + '/_edit_knowledge', data, function(data) {
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

  $.getJSON(window.SCRIPT_ROOT + '/_delete_knowledge', {knowledge_id: knowledge_id, subgraph_id: window.SUBGRAPH_ID}, function(data) {
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
*/