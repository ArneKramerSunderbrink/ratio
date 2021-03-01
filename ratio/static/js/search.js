/**
 * Javascript code related to the subgraph filter
 */

$(function(){
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
    //get_json_change_value(input, function () { return value; });
  });
});