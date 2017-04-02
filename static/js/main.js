$('.btn').click(function(e) {
  e.preventDefault();
  $.ajax({
    type: 'POST',
    url: '/process',
    data: 'yo',
          success: function(result) {
            console.log(JSON.parse(result).data);
          },
          error: function(result) {
            console.log('error');
          }
        });
});