// Filter
$(function() {
  $('input#subgraph-filter').bind('keyup', function() {
    var input, filter, ul, li, a, i;
    input = document.getElementById('subgraph-filter');
    filter = input.value.toUpperCase();
    div = document.getElementById('subgraph-list');
    a = div.getElementsByTagName('a');
    for (i = 0; i < a.length; i++) {
      txtValue = a[i].textContent || a[i].innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        a[i].style.display = '';
      } else {
        a[i].style.display = 'none';
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
    return false
  });

  $('a#new-subgraph-cancel').bind('click', function() {
    $('button#new-subgraph').css('display', 'block');
    $('form#new-subgraph-form').css('display', 'none');
    return false
  });
});