$('.summary').on('click', function(e) {
  e.preventDefault();
  $(".summary").attr("disabled", "disabled");
  var length = $('.length')[0].value;
  var progressBar = $('.progress');
  var messageBox = $('.messages');

  if (length < 6) {
    $("#alert-text").html('<strong>Please submit a time greater than 10 seconds.</strong>');
    $(".alert").addClass("in");
    messageBox.html('');
    resetExceptFile();
  }

  else {
    var form_data = new FormData($('#upload-file')[0]);

    form_data.append('file', $('#file').prop("files")[0]);

    progressBar.removeClass('hide');
    $.ajax({
      type: 'POST',
      url: '/process',
      data: form_data,
      contentType: false,
      processData: false,
      success: function(result) {
        $(".summary").removeAttr("disabled");
        r = JSON.parse(result);

        // handle failure cases
        if (r.data == '') {
          $("#alert-text").html('<strong>Sorry, unable to process PDF.</strong>');
          $(".alert").addClass("in");
          messageBox.html('');
          resetEverything();
        }

        else if (r.data == 'empty') {
          $("#alert-text").html('<strong>Please upload a PDF with a name.</strong>');
          $(".alert").addClass("in");
          messageBox.html('');
          resetEverything();
        }

        else if (r.data == 'big') {
          $("#alert-text").html('<strong>Please upload a PDF less than 20 pages.</strong>');
          $(".alert").addClass("in");
          messageBox.html('');
          resetEverything();
        }

        // shouldn't happen
        else if (r.data == 'name') {
          $("#alert-text").html('<strong>Sorry, please submit a file with content.</strong>');
          $(".alert").addClass("in");
          messageBox.html('');
          resetEverything();
        }
        else {
          messageBox.html('<a href="' + r.unique_url + '" download>Download the file!</a>')
          done();
        }
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

function addTextBox() {
  var element = document.createElement("input");
  document.getElementById("uploadOptions").appendChild(element);
}

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