function flip_front(id) {
  // the swapping is done in order for the function to also work with elements that have
  // display: flex or table-row instead of simply display: block
  var frontside, flipside, msg;
  frontside = $(".flip-frontside[data-flipid='" + id + "']");
  flipside = $(".flip-flipside[data-flipid='" + id + "']");
  msg = $(".flip-flipside-msg[data-flipid='" + id + "']");

  if (flipside.css('display') != 'none') {
    frontside.css('display', flipside.css('display'));
    flipside.css('display', 'none');
    msg.css('display', 'none');
  }
}

function flip_flip(id) {
  var frontside, flipside, msg;
  frontside = $(".flip-frontside[data-flipid='" + id + "']");
  flipside = $(".flip-flipside[data-flipid='" + id + "']");
  msg = $(".flip-flipside-msg[data-flipid='" + id + "']");

  if (frontside.css('display') != 'none') {
    flipside.css('display', frontside.css('display'));
    frontside.css('display', 'none');
    flipside.find('input').first().focus();
  }
}

$(function() {
  var elements, i;
  $(document).on('click', '.flip-frontbutton', function() {
    flip_front(this.getAttribute('data-flipid'));
    return false;
  });
  $(document).on('click', '.flip-flipbutton', function() {
    flip_flip(this.getAttribute('data-flipid'));
    return false;
  });
  $(document).on('keyup', '.flip-flipside', function(e) {
    if (e.key === "Escape") {
      flip_front(this.getAttribute('data-flipid'));
      e.stopPropagation();
    }
  });
});