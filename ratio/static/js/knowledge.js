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

    // if the field has a unregistered value, call get_json_change_value(unregistered_input, '') first
    // so it becomes a real value the backend actually knows about
    // otherwise the new value and the unregistered value would have the same index
    const unregistered_input = field.find('*[data-unregistered]');
    if (unregistered_input.length > 0) {
      get_json_change_value(unregistered_input[0], '', null, function() {
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
      });
    } else {
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
    }
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
    get_json_change_value(input[0], '', button);
    form.addClass('deleted');
    // Display message
    $('div#knowledge-delete-msg > span').text('Value has been deleted.');
    $('div#knowledge-delete-msg > button:first').off('click');
    $('div#knowledge-delete-msg > button:first').on('click', function() {
      const button = this;
      button.disabled = true;
      if (old_value != '') {
        get_json_change_value(input[0], old_value, button);
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

  // general change value call
  function get_json_change_value(input, value, button=null, callback_=null) {
    const index = $(input).attr('data-index');
    const property = $(input).closest('div.field');
    const property_uri = property.attr('data-property-uri');
    const entity_uri = $(input).closest('div.entity').attr('data-entity-uri');

    const data = [
      { name: 'subgraph_id', value: window.SUBGRAPH_ID },
      { name: 'entity_uri', value: entity_uri },
      { name: 'property_uri', value: property_uri },
      { name: 'index', value: index},
      { name: 'value', value: value}
    ];

    $.getJSON(window.SCRIPT_ROOT + '/_change_value', data, function(data) {
      if (data.error) {
        alert(data.error);
      } else if (data.validity) {
        set_validity(input, data.validity);
      } else {
        set_validity(input, '');
      }
      input.removeAttribute('data-unregistered');
      if (button != null) {
        button.disabled = false;
      }
      if (callback_ != null) {
        callback_();
      }
    })
    .fail(function() { alert('getJSON request failed!'); });
  }

  // Special functionality for literal fields
  // Change value
  $('div#scroll-container').on('input', 'div.literal-input', function() {
    const input = this;
    get_json_change_value(input, input.innerText);
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
    get_json_change_value(input, value);
  });

  // Check validity of option input
  // I found no way to discriminate between focus switching within the form (to the custom option input)
  // or out of the form and only then check validity
  $('div#scroll-container').on('focusout', '.option-form', function() {
    // if value not in options, .setCustomValidity("Invalid option.")
    const input = $(this).find('.option-input')[0];
    let value = false;
    if (input.value != '') {
      $(this).find('.option').each(function() {
        if (this.textContent == input.value) {
          if ($(this).is('[data-option-uri]')) {
            value = $(this).attr('data-option-uri');
            input.setAttribute('data-option-uri', value);
          } else {
            value = this.textContent;
          }
          return false;
        }
      });
      if (value === false) {
        console.log('false');
        set_validity(input, 'Choose an option from the list.');
        input.removeAttribute('data-option-uri');
        return;
      }
    } else {
      value = '';
    }
    get_json_change_value(input, value);
  });

  // Add custom option
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
        set_validity(input, '');
        // reset add entity input
        form.first()[0].reset();
        // add option to all corresponding fields
        data.option_fields.forEach(function(uri) {
          $('div.field[data-property-uri="'+uri+'"] div.options').append(data.option_div);
        });
        // remove focus from input to the dropdown disappears
        document.activeElement.blur()
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
        const entity_div = $(data.entity_div)
        list.append(entity_div);
        // reset add entity input
        field.find('form.add-entity-form').first()[0].reset();
        flip_front(field.find('div.add-entity-div > button').first().attr('data-flipid'));
        if (data.remove_plus) {
          field.find('.add-entity-div').css('display', 'none');
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
    const field = $(this).closest('div.entity-field');
    const property_uri = field.attr('data-property-uri');
    const entity = $(this).closest('div.entity');
    const entity_uri = entity.attr('data-entity-uri');
    const data = [
      { name: "subgraph_id", value: window.SUBGRAPH_ID },
      { name: "property_uri", value: property_uri },
      { name: "entity_uri", value: entity_uri }
    ];

    $.getJSON(window.SCRIPT_ROOT + '/_delete_entity', data, function(data_return) {
      if (data_return.error) {
        alert(data_return.error);
      } else {
        // Remove entity div
        entity.addClass('deleted');
        const functional = data_return.functional;
        if (functional) {
          field.find('.add-entity-div').css('display', '');
        }
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
              if (functional) {
                field.find('.add-entity-div').css('display', 'none');
              }
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
