/**
 * Javascript code related to the dynamic display and editing of knowledge:
 * Adding, deleting and changing Literal and Entity values, checking if inputs are valid,
 * filtering options, adding custom options,
 * displaying messages related to the above.
 */

$(function () {
  // Delete message X-button
  $('div#knowledge-delete-msg > button:last').on('click', function() {
    $('div#knowledge-delete-msg').css('display', 'none');
    return false;
  });

  // Add value
  $('div#scroll-container').on('click', 'div.field > div > button', function() {
    const button = this;
    button.disabled = true;
    const field = $(this).closest('div.field');
    const entity = $(this).closest('div.entity');
    const property_uri = field.attr('data-property-uri');
    const entity_uri = entity.attr('data-entity-uri');
    const data = [
      { name: "subgraph_id", value: window.SUBGRAPH_ID },
      { name: "property_uri", value: property_uri },
      { name: "entity_uri", value: entity_uri }
    ];

    $.getJSON(window.SCRIPT_ROOT + '/_add_value', data, function(data) {
      if (data.error) {
        alert(data.error);
      } else {
        const value_div = $(data.value_div)
        field.find('div.field-value-list').append(value_div);
        value_div.find('div.literal-input, input.option-input').focus();
      }
      button.disabled = false;
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });

  // Delete Value
  $('div#scroll-container').on('click', 'button.delete-value-button', function() {
    const button = this;
    button.disabled = true;
    const form = $(this).closest('.literal-form, .option-form');
    const input = form.find('.literal-input, .option-input');
    let old_value = '';
    if (input.is('.literal-input')) {
      old_value = input[0].innerText;
    } else {
      form.find('.option').each(function() {
        if (this.textContent == input[0].value) {
          if ($(this).is('[data-option-uri]')) {
            old_value = $(this).attr('data-option-uri');
          } else {
            old_value = this.textContent;
          }
          return false;
        }
      });
    }
    get_json_change_value(input[0], function() { return ''; }, button);
    form.addClass('deleted');
    // Display message
    $('div#knowledge-delete-msg > span').text('Value has been deleted.');
    $('div#knowledge-delete-msg > button:first').off('click');
    $('div#knowledge-delete-msg > button:first').on('click', function() {
      const button = this;
      button.disabled = true;
      if (old_value != '') {
        get_json_change_value(input[0], function() { return old_value; }, button);
      }
      form.removeClass('deleted');
      $('div#knowledge-delete-msg').css('display', 'none');
      return false;
    });
    $('div#knowledge-delete-msg').css('display', 'flex');
    return false;
  });

  // Mark invalid
  function set_validity(element, validity) {
    if (validity == '') {
      element.style.boxShadow = '';
      element.title = '';
    } else {
      element.style.boxShadow = '0 0 2px 1px red';
      element.title = validity;
    }
  }

  function get_json_change_value(input, get_value, button=null) {
    const index = $(input).attr('data-index');
    if (index == -1) {
      $(input).attr('data-index', -2);
    } else if (index == -2) {
      function wait_for_index() {
        if ($(input).attr('data-index') == -2) {
          setTimeout(wait_for_index, 100);
          return;
        }
        get_json_change_value(input, get_value, button);
        return;
      }
      wait_for_index();
      return;
    }
    const property = $(input).closest('div.field');
    const property_uri = property.attr('data-property-uri');
    const entity_uri = $(input).closest('div.entity').attr('data-entity-uri');

    const data = [
      { name: 'subgraph_id', value: window.SUBGRAPH_ID },
      { name: 'entity_uri', value: entity_uri },
      { name: 'property_uri', value: property_uri },
      { name: 'index', value: index},
      { name: 'value', value: get_value()}
    ];

    $.getJSON(window.SCRIPT_ROOT + '/_change_value', data, function(data) {
      if (data.error) {
        alert(data.error);
      } else if (data.validity) {
        set_validity(input, data.validity);
      } else {
        set_validity(input, '');
      }
      if (index == -1) {
        $(input).attr('data-index', String(data.index));
      }
      if (button != null) {
        button.disabled = false;
      }
    })
    .fail(function() { alert('getJSON request failed!'); });
  }

  // Special functionality for literal fields
  // Change value
  $('div#scroll-container').on('input', 'div.literal-input', function() {
    const input = this;
    get_json_change_value(input, function() { return input.innerText; });
  });

  // Special functionality for options Fields
  // Filter
  $('div#scroll-container').on('input', 'input.option-input', function() {
    const filter_string = this.value.toUpperCase();
    $(this).next('.options-dropdown').find('.option:not(.deleted)').each(function() {
      if ($(this).text().toUpperCase().indexOf(filter_string) > -1) {
        $(this).css('display', '');
      } else {
        $(this).css('display', 'none');
      }
    });
  });
  $('div#scroll-container').on('focus', 'input.option-input', function() {
    $(this).next('.options-dropdown').find('.option').each(function() {
      $(this).css('display', '');
    });
  });

  // Select option
  $('div#scroll-container').on('click', '.option', function() {
    const input = $(this).closest('.options-dropdown').prev('.option-input')[0];
    let value = '';
    input.value = this.textContent;
    if ($(this).is('[data-option-uri]')) {
      value = $(this).attr('data-option-uri');
      input.setAttribute('data-option-uri', value);
    } else {
      value = this.textContent;
    }
    get_json_change_value(input, function () { return value; });
  });

  // Check validity of option input
  // I found no way to discriminate between focus switching within the form (to the custom option input)
  // or out of the form and only then check validity
  $('div#scroll-container').on('focusout', '.option-form', function() {
    // if value not in options, .setCustomValidity("Invalid option.")
    const input = $(this).find('.option-input')[0];
    let value = '';
    if (input.value != '') {
      $(this).find('.option').each(function() {
        if (this.textContent == input.value) {
          if ($(this).is('[data-option-uri]')) {
            value = $(this).attr('data-option-uri');
            input.setAttribute('data-option-uri', value);
          } else {
            value = this.textContent;
          }
        }
      });
      if (value == '') {
        set_validity(input, 'Choose an option from the list.');
        input.removeAttribute('data-option-uri');
        return
      }
    }
    get_json_change_value(input, function () { return value; });
  });

  // Add option
  $('div#scroll-container').on('submit', '.add-option-form', function() {
    const form = $(this);
    const button = form.find('button')[0];
    button.disabled = true;
    const entity_uri = form.closest('div.entity').attr('data-entity-uri');
    const field = form.closest('div.field');
    const property_uri = field.attr('data-property-uri');
    const data = form.serializeArray();
    const input = $(this).closest('.options-dropdown').prev('.option-input')[0];
    const index = $(input).attr('data-index');
    data.push({ name: "subgraph_id", value: window.SUBGRAPH_ID });
    data.push({ name: "entity_uri", value: entity_uri });
    data.push({ name: "property_uri", value: property_uri });
    data.push({ name: "index", value: index });

    $.getJSON(window.SCRIPT_ROOT + '/_add_option', data, function(data) {
      if (data.error) {
        alert(data.error);
      } else {
        input.value = data.option_label;
        input.setAttribute('data-option-uri', data.option_uri);
        if (index == -1) {
          input.setAttribute('data-index', String(data.index));
        }
        // reset add entity input
        form.first()[0].reset();
        // add option to all corrsponding fields
        data.option_fields.forEach(function(uri) {
          $('div.field[data-property-uri="'+uri+'"] div.options').append(data.option_div);
        });
      }
      button.disabled = false;
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });

  // Special functionality for Entities
  // Change label
  $('div#scroll-container').on('input', 'div.entity-label', function() {
    const entity_uri = $(this).closest('div.entity').attr('data-entity-uri');
    const label = this.innerText.replace(/\r?\n|\r/g, "");

    const data = [
      { name: 'subgraph_id', value: window.SUBGRAPH_ID },
      { name: 'entity_uri', value: entity_uri },
      { name: 'label', value: label}
    ];

    // update option fields
    $('input.option-input[data-option-uri="'+entity_uri+'"]').val(label);
    $('div.option[data-option-uri="'+entity_uri+'"]').text(label);

    $.getJSON(window.SCRIPT_ROOT + '/_change_label', data, function(data) {
      if (data.error) {
        alert(data.error);
      }
    })
    .fail(function() { alert('getJSON request failed!'); });
  });

  // Add entity
  $('div#scroll-container').on('submit', 'form.add-entity-form', function() {
    const button = $(this).find('button')[0];
    button.disabled = true;
    const field = $(this).closest('div.entity-field');
    const property_uri = field.attr('data-property-uri');
    const entity_uri = $(this).closest('div.entity').attr('data-entity-uri');
    const data = $(this).serializeArray();
    data.push({ name: "subgraph_id", value: window.SUBGRAPH_ID });
    data.push({ name: "property_uri", value: property_uri });
    data.push({ name: "entity_uri", value: entity_uri });

    $.getJSON(window.SCRIPT_ROOT + '/_add_entity', data, function(data) {
      if (data.error) {
        alert(data.error);
      } else {
        // add entity
        const list = field.find('div.entity-field-value-list').first();
        list.append(data.entity_div);
        // expand entity body
        flip_flip(list.children().last().find('.entity-title > button:first').attr('data-flipid'));
        // reset add entity input
        field.find('form.add-entity-form').first()[0].reset();
        flip_front(field.find('div.add-entity-div > div.flip-flipside').first().attr('data-flipid'));
        if (data.remove_plus) {
          field.find('add-entity-div').css('display', 'none');
        }
        if (data.option_fields) {
          data.option_fields.forEach(function(uri) {
            $('div.field[data-property-uri="'+uri+'"] div.options').append(data.option_div);
          });
        }
      }
      button.disabled = false;
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });

  // Delete entity
  $('div#scroll-container').on('click', 'button.delete-entity-button', function() {
    const button = this;
    button.disabled = true;
    const entity = $(this).closest('div.entity');
    const entity_uri = entity.attr('data-entity-uri');
    const data = [
      { name: "subgraph_id", value: window.SUBGRAPH_ID },
      { name: "entity_uri", value: entity_uri }
    ];

    $.getJSON(window.SCRIPT_ROOT + '/_delete_entity', data, function(data_return) {
      if (data_return.error) {
        alert(data_return.error);
      } else {
        // Remove entity div
        entity.addClass('deleted');
        // update option fields
        const deleted_uris = data_return.deleted;
        deleted_uris.forEach(function(uri) {
          $('input.option-input[data-option-uri="'+uri+'"]').val('');
          $('div.option[data-option-uri="'+uri+'"]').addClass('deleted');
        });
        // Display message
        $('div#knowledge-delete-msg > span').text('Entity has been deleted.');
        $('div#knowledge-delete-msg > button:first').off('click');
        $('div#knowledge-delete-msg > button:first').on('click', function() {
          const button = this;
          button.disabled = true;
          $.getJSON(window.SCRIPT_ROOT + '/_undo_delete_entity', data, function(data_return) {
            if (data_return.error) {
              alert(data_return.error);
            } else {
              entity.removeClass('deleted');
              deleted_uris.forEach(function(uri) {
                $('div.option[data-option-uri="'+uri+'"]').removeClass('deleted');
              });
              $('div#knowledge-delete-msg').css('display', 'none');
            }
            button.disabled = false;
          })
          .fail(function() { alert('getJSON request failed!'); });
          return false;
        });
        $('div#knowledge-delete-msg').css('display', 'flex');
      }
      button.disabled = false;
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });

});
