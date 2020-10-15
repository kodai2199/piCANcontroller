
$(document).ready(function() {
$('.reset_button').click(function(){
    $(this).parent().hide();
    $(this).parent().siblings().show();
});
});