/**
 * Javascript code related to the header:
 * Toggling the overlay and nothing else currently.
 */


// toggle overlay
function toggle_overlay() {
  overlay = $('div#overlay');
  if (overlay.css('display') == 'none') {
    overlay.css('display', 'block');
  } else {
    overlay.css('display', 'none');
  }

  return false;
}

function overlay_escape_handler(e) {
  if (e.key === "Escape" && $('div#overlay').css('display') == 'block' && $SUBGRAPH_ID != 0) {
    toggle_overlay();
  }
}

$(function() {
  $('a#subgraph-name').on('click', toggle_overlay);
  $('a#close-overlay').on('click', toggle_overlay);
  $(document).on('keyup', overlay_escape_handler);
});