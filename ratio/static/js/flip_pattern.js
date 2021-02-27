/**
 * Javascript code for the flip pattern described in dev_ressources/pattern_flip.html.
 */

function flip_front(id) {
  // the swapping is done in order for the function to also work with elements that have
  // display: flex or table-row instead of simply display: block
  const frontside = $('.flip-frontside[data-flipid="' + id + '"]');
  const flipside = $('.flip-flipside[data-flipid="' + id + '"]');
  const msg = $('.flip-flipside-msg[data-flipid="' + id + '"]');

  if (flipside.css('display') != 'none') {
    frontside.css('display', flipside.css('display'));
    flipside.css('display', 'none');
    msg.css('display', 'none');
  }
}

function flip_flip(id) {
  const frontside = $('.flip-frontside[data-flipid="' + id + '"]');
  const flipside = $('.flip-flipside[data-flipid="' + id + '"]');
  const msg = $('.flip-flipside-msg[data-flipid="' + id + '"]');

  if (frontside.css('display') != 'none') {
    flipside.css('display', frontside.css('display'));
    frontside.css('display', 'none');
    flipside.find('input').first().focus();
  }
}

$(document).on('click', '.flip-frontbutton', function() {
  flip_front(this.getAttribute('data-flipid'));
  return false;
});
$(document).on('click', '.flip-flipbutton', function() {
  flip_flip(this.getAttribute('data-flipid'));
  return false;
});
$(document).on('keyup', '.flip-flipside', function(e) {
  if (e.key === 'Escape') {
    flip_front(this.getAttribute('data-flipid'));
    e.stopPropagation();
  }
});