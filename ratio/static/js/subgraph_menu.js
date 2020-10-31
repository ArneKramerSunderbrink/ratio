// Filter
$(function() {
  $('input#subgraph-filter').on('keyup', function() {
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
  $('div#subgraph-list').on('submit', 'form', function() {
    var data = $(this).serializeArray();
    var list_item = $(this.parentNode.parentNode);
    var subgraph_id = list_item.attr('data-subgraph-id')
    var flipid = 'subgraph-list-' + subgraph_id;
    data.push({ name: "subgraph_id", value: subgraph_id });

    $.getJSON($SCRIPT_ROOT + '/_edit_subgraph_name', data, function(data) {
      if (data.error) {
        $('div#subgraph-menu-edit-msg').text(data.error);
        $('div#subgraph-menu-edit-msg').attr('data-flipid', flipid)
        $('div#subgraph-menu-edit-msg').css('display', 'block');
        list_item.find('form > input').focus();
      } else {
        if (subgraph_id == $SUBGRAPH_ID) {
          $('a#subgraph-name').text(data.name);
        }
        list_item.children().eq(0).children().eq(0).text(data.name);
        flip_front(flipid);
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });
});

// delete subgraph
$(function() {
  $('div#subgraph-list').on('click', 'form > a[id^="delete-"]', function() {
    var item = $(this.parentNode.parentNode.parentNode);
    var subgraph_id = item.attr('data-subgraph-id');
    $.getJSON($SCRIPT_ROOT + '/_delete_subgraph', {subgraph_id: subgraph_id}, function(data) {
        if (data.error) {
          $('div#subgraph-menu-edit-msg').text(data.error);
          $('div#subgraph-menu-edit-msg').attr('data-flipid', 'subgraph-list-' + subgraph_id)
          $('div#subgraph-menu-edit-msg').css('display', 'block');
        } else {
          if (subgraph_id == $SUBGRAPH_ID) {
            // prevent user from going back to editing the subgraph
            $('a#close-overlay').css('display', 'none');
            $(document).off('keyup', overlay_escape_handler);
          }
          item.css('display', 'none');
          $('div#subgraph-menu-edit-msg').attr('data-subgraph-id', subgraph_id);
          $('div#subgraph-menu-delete-msg > span').text('"' + data.name + '" has been deleted.');
          $('div#subgraph-menu-delete-msg').css('display', 'block');
        }
      })
      .fail(function() { alert('getJSON request failed!'); });
  });
});

// todo Undo delete Subgraph

// add subgraph
$(function() {
  $('form#new-subgraph-form').on('submit', function() {
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