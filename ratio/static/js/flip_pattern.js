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

  return false;
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

  return false;
}

$(function() {
  var elements, i;
  $('.flip-frontbutton').bind('click', function() {
    flip_front(this.getAttribute('data-flipid'));
  });
  $('.flip-flipbutton').bind('click', function() {
    flip_flip(this.getAttribute('data-flipid'));
  });
  $('.flip-flipside').keyup(function(e) {
    if (e.key === "Escape") {
      flip_front(this.getAttribute('data-flipid'));
      e.stopPropagation();
    }
  });
});