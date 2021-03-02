/**
 * Javascript code related to the subgraph filter
 */

$(function(){
  // filter options
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

    search();
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

  // Check validity of option input
  $('div#scroll-container').on('focusout', '.option-form', function() {
    // if value not in options, .setCustomValidity("Invalid option.")
    const input = $(this).find('.option-input')[0];
    let value = false;
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
      set_validity(input, 'This value cannot be found in the database.');
      input.removeAttribute('data-option-uri');
      return;
    } else {
      set_validity(input, '');
      search();
    }
  });

  function search() {
    // collect all values from the filter fields
    const data = [];
    $('div.entity[data-entity-uri="http://www.example.org/ratio-tool#Filter"] input.option-input').each(function() {
      if (this.value != '') {
        if ($(this).is('[data-option-uri]')) {
          data.push({ name: $(this).closest('div.field').attr('data-property-uri'), value: $(this).attr('data-option-uri') });
        } else {
          data.push({ name: $(this).closest('div.field').attr('data-property-uri'), value: this.value });
        }
      }
    });

    if (JSON.stringify(data) == window.filter_data) { return; }  // nothing changed

    window.filter_data = JSON.stringify(data);
    $.getJSON(window.SCRIPT_ROOT + '/_search', data, function(data) {
      if (data.error) {
        alert(data.error);
      } else {
        // todo: build result list
      }
    })
    .fail(function() { alert('getJSON request failed!'); });
  }

});