// add knowledge
$(function() {
  $('form#new-knowledge-form').submit(function() {
    var data = $(this).serialize();

    $.getJSON($SCRIPT_ROOT + '_add_knowledge', data, function(data) {
      if (data.error) {
        alert(data.error); //todo add element to page to display error
      } else {
        // add row to table above the form
        //alert(data.knowledge_id) // todo i will need this for the edit button
        $('form#new-knowledge-form').parent().before(`
          <tr class="w3-animate-opacity">
            <td>${ data.subject }</td>
            <td>${ data.predicate }</td>
            <td>${ data.object }</td>
            <td>
              <a href="#" class="w3-button" title="Edit knowledge">
                <i class="fas fa-pen fa-lg"></i>
              </a>
            </td>
          </tr>
        `);

        $('form#new-knowledge-form')[0].reset();
      }
    })
    .fail(function() { alert('getJSON request failed!'); });

    return false;
  });
});