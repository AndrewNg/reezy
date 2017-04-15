$('.summary').click(function(e) {
  e.preventDefault();
  var form_data = new FormData($('#upload-file')[0]);
  $.ajax({
    type: 'POST',
    url: '/process',
    data: form_data,
    contentType: false,
    processData: false,
    success: function(result) {
      console.log(JSON.parse(result).data + JSON.parse(result).unique_url);
    },
    error: function(result) {
      console.log('error');
    }
    });
});

function addTextBox() {
  var element = document.createElement("input");

  document.getElementById("uploadOptions").appendChild(element);
}