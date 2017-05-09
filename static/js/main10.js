$('.summary').on('click', function(e) {
  e.preventDefault();
  $(".summary").attr("disabled", "disabled");
  var length = $('.length')[0].value;
  var progressBarDiv = $('.progress');
  var progressBar = $('#realtime-progress-bar');
  var messageBox = $('.messages');
  messageBox.html('initializing...');
  progressBar.width('0%');


  if (length < 6 || length > 600) {
    $("#alert-text").html('<strong>Please submit a time between 10 seconds and 10 minutes.</strong>');
    $(".alert").addClass("in");
    messageBox.html('');
    resetExceptFile();
    $(".summary").removeAttr("disabled");
  }

  else {
    if ($(".alert").hasClass("in")) {
      $(".alert").removeClass("in");
    }

    var form_data = new FormData($('#upload-file')[0]);

    form_data.append('file', $('#file').prop("files")[0]);

    progressBarDiv.removeClass('hide');
    $.ajax({
      type: 'POST',
      url: '/process',
      data: form_data,
      contentType: false,
      processData: false,
      success: function(result) {

      },
    error: function(result) {
      $(".summary").removeAttr("disabled");
      $("#alert-text").html('<strong>Sorry, there was a problem processing the PDF.</strong>');
      $(".alert").addClass("in");
      messageBox.html('');
      resetEverything();
    }
  });
  }
});

$('.textBoxBtn').click(function(e) {
  var modal = document.getElementById("modalText");
  modal.style.display = "block";

  // When the user clicks anywhere outside of the modal, close it
  window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}
});

$('.textSubmitBtn').click(function(e) {
  $(".summary").removeClass("hide");
})

$(".upload").change(function(){
  var name = $('#file').prop("files")[0].name
  var size = $('#file').prop("files")[0].size
  var type = $('#file').prop("files")[0].type
  var filename = $('.filename');

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

  resetExceptFile();
});

// reset everything to default state
function resetEverything() {
 var progressBar = $('.progress');
 var messageBox = $('.messages');
 var filename = $('.filename');
 var summary = $('.summary');
 var fileUpload = $('.fileUpload')

 progressBar.addClass('hide');
 summary.addClass('hide');
 filename.addClass('hide');
 filename.html('');
 fileUpload.removeClass('hide');
 messageBox.html('');
}

// reset everything but keep the file
function resetExceptFile() {
 var progressBar = $('.progress');
 var messageBox = $('.messages');
 var filename = $('.filename');
 var summary = $('.summary');
 var fileUpload = $('.fileUpload')

 progressBar.addClass('hide');
 messageBox.html('');
}

// at successful completion
function done() {
  var fileUpload = $('.fileUpload')
  var summary = $('.summary');
  var buttonText = $('#chooseText')

  fileUpload.removeClass('hide');
  summary.addClass('hide');
  buttonText.html('Choose another file');
}