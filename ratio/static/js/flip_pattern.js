function flip_front() {
var id = this.getAttribute('data-for');
  $('.flip-frontside-' + id).css('display', 'block');
  $('.flip-flipside-' + id).css('display', 'none');
  $('.flip-flipside-msg-' + id).css('display', 'none');
  return false;
}

function flip_flip() {
  var id = this.getAttribute('data-for');
  $('.flip-frontside-' + id).css('display', 'none');
  $('.flip-flipside-' + id).css('display', 'block');
  $('.flip-flipside-' + id).find('input').first().focus();
  return false;
}

$(function() {
  var buttons, i;
  buttons = $('.flip-frontbutton');
  for (i = 0; i < buttons.length; i++) {
    $(buttons[i]).bind('click', flip_front);
  }
  buttons = $('.flip-flipbutton');
  for (i = 0; i < buttons.length; i++) {
    $(buttons[i]).bind('click', flip_flip);
  }
});