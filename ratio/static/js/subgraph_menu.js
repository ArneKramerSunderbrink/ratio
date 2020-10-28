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

// edit subgraph
$(function() {
  $('div#subgraph-list form').submit(function() {
    var data = $(this).serializeArray();
    var list_item = $(this.parentNode.parentNode);
    var flipid = 'subgraph-list-' + list_item.attr('data-subgraph-id');
    data.push({ name: "subgraph_id", value: list_item.attr('data-subgraph-id') });

    $.getJSON($SCRIPT_ROOT + '/_edit_subgraph_name', data, function(data) {
      if (data.error) {
        $('div#subgraph-menu-edit-msg').text(data.error);
        $('div#subgraph-menu-edit-msg').attr('data-flipid', flipid)
        $('div#subgraph-menu-edit-msg').css('display', 'block');
        list_item.find('form > input').focus();
      } else {
        list_item.children().eq(0).children().eq(0).text(data.name);
        flip_front(flipid);
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });
});

// add subgraph
$(function() {
  $('form#new-subgraph-form').submit(function() {
    var data = $(this).serialize();

    $.getJSON($SCRIPT_ROOT + '/_add_subgraph', data, function(data) {
      if (data.error) {
        $('div#subgraph-menu-add-msg').text(data.error);
        $('div#subgraph-menu-add-msg').css('display', 'block');
        $('input#new-subgraph-name').focus();
      } else {
        window.location = data.redirect;
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });
});