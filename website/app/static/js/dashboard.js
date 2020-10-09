
$(document).ready(function() {
$('.reset_button').click(function(){
    var id = $(this).attr('id');
    console.log(id);
    $(this).parent().hide();
    $(this).parent().siblings().show();
});
});