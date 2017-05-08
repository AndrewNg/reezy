$('.summary').click(function(e) {
  e.preventDefault();
  var form_data = new FormData($('#upload-file')[0]);

  form_data.append('file', $('#file').prop("files")[0]);

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
      r = JSON.parse(result);

      if (r.data == '') {
        $("#alert-text").html('<strong>Sorry, unable to process PDF.</strong>');
        $(".alert").addClass("in");
        progressBar.addClass('hide');
      }
      else {
        messageBox.html('<a href="' + r.unique_url + '" download>Download the file!</a>')
      }
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

$(".upload").change(function(){
  var name = $('#file').prop("files")[0].name
  var size = $('#file').prop("files")[0].size
  var type = $('#file').prop("files")[0].type

  if (name.substr(name.length - 4) != '.pdf') {
    $("#alert-text").html('<strong>Wrong file extension.</strong> Please upload a PDF.');
    $(".alert").addClass("in");
  }

  else if (size > 5000000) {
    $("#alert-text").html('<strong>File too large.</strong> Please upload a file smaller than 5 mb.');
    $(".alert").addClass("in");
  }

  // we good
  else {
    if ($(".alert").hasClass("in")) {
      $(".alert").removeClass("in");
    }

    $(".fileUpload").addClass("hide");

    $(".filename").html(name);
    $(".filename").removeClass("hide");
    $(".summary").removeClass("hide");
  }

  console.log(name + size + type)
});