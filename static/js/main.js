$('.btn').click(function(e) {
  e.preventDefault();
  var form_data = new FormData($('#upload-file')[0]);
  $.ajax({
    type: 'POST',
    url: '/process',
    data: form_data,
    contentType: false,
    cache: false,
    processData: false,
    success: function(result) {
      console.log(JSON.parse(result).data);
    },
    error: function(result) {
      console.log('error');
    }
    });
});