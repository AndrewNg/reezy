$('.summary').click(function(e) {
  e.preventDefault();
  var form_data = new FormData($('#upload-file')[0]);
  var progressBar = $('.progress');
  var messageBox = $('.messages')
  progressBar.removeClass('hide');
  $.ajax({
    type: 'POST',
    url: '/process',
    data: form_data,
    contentType: false,
    processData: false,
    success: function(result) {
      console.log(JSON.parse(result).data);
      messageBox.html('<a href="' + JSON.parse(result).unique_url + '" download>Download the file!</a>')
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