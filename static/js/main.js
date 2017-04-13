// var pusher_key = {{pusher_key}}

// var pusher = new Pusher(pusher_key, {
//   encrypted: true
// });

$('.btn').click(function(e) {
  e.preventDefault();
  var form_data = new FormData($('#upload-file')[0]);
  $.ajax({
    type: 'POST',
    url: '/process',
    data: form_data,
    contentType: false,
    processData: false,
    success: function(result) {
      console.log(JSON.parse(result).data);
      console.log(JSON.parse(result).url)
    },
    error: function(result) {
      console.log('error');
    }
    });
});

// var channel = pusher.subscribe('my-channel');
// channel.bind('my-event', function(data) {
//   console.log(data.message);
// });