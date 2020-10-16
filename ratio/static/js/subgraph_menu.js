// Filter
$(function() {
  $('input#subgraph-filter').bind('keyup', function() {
    var input, filter, div, entries, i, a, txtValue;
    input = document.getElementById('subgraph-filter');
    filter = input.value.toUpperCase();
    div = document.getElementById('subgraph-list');
    entries = div.children;
    for (i = 0; i < entries.length; i++) {
      a = entries[i].getElementsByTagName('a')[0];
      txtValue = a.textContent || a.innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        entries[i].style.display = '';
      } else {
        entries[i].style.display = 'none';
      }
    }
  });
});

// toggle add subgraph
$(function() {
  $('button#new-subgraph').bind('click', function() {
    $('button#new-subgraph').css('display', 'none');
    $('form#new-subgraph-form').css('display', 'block');
    $('input#new-subgraph-name').focus();
    return false;
  });

  $('a#new-subgraph-cancel').bind('click', function() {
    $('button#new-subgraph').css('display', 'block');
    $('form#new-subgraph-form').css('display', 'none');
    $('div#subgraph-menu-error').css('display', 'none');
    return false;
  });
});

// add subgraph
$(function() {
  $('form#new-subgraph-form').submit(function() {
    var data = $(this).serialize();

    $.getJSON($SCRIPT_ROOT + '/_add_subgraph', data, function(data) {
      if (data.error) {
        $('div#subgraph-menu-error').text(data.error);
        $('div#subgraph-menu-error').css('display', 'block');
      } else {
        window.location = data.redirect;
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });
});