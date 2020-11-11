// Show more or less text
$(document).ready(function() {
  var showChar = 100;  // How many characters are shown by default
  var ellipsestext = "...";
  var moretext = "Vis mere";
  var lesstext = "Vis mindre";
  

  $('.more').each(function() {
      var content = $(this).html();

      if(content.length > showChar) {
          var c = content.substr(0, showChar);
          var h = content.substr(showChar, content.length - showChar);
          var text = c + '<span class="moreellipses">' + ellipsestext + '</span><span class="morecontent"><span>' + h + '</span><a href="" class="morelink">' + moretext + '</a></span>';

          $(this).html(text);
      }
  });

  $(".morelink").click(function () {
      if($(this).hasClass("less")) {
          $(this).removeClass("less");
          $(this).html(moretext);
      } else {
          $(this).addClass("less");
          $(this).html(lesstext);
      }
      $(this).parent().prev().toggle();
      $(this).prev().toggle();
      return false;
  });
});