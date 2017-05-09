$('.summary').click(function(e) {
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
    $('.summary').disabled = true;
    e.preventDefault();
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
        $('summary').disabled = false;
        r = JSON.parse(result);

      // handle failure cases
      if (r.data == '') {
        $("#alert-text").html('<strong>Sorry, unable to process PDF.</strong>');
        $(".alert").addClass("in");
        messageBox.html('');
        resetEverything();
      }

      // shouldn't happen
      else if (r.data == 'name') {
        $("#alert-text").html('<strong>Sorry, please submit a file with a name.</strong>');
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
      $('summary').disabled = false;
      console.log('error');
    }
  });
  }
});

$('.modal').on('shown', function () {
    $('.modal').focus();
})

// $('.textBoxBtn').click(function(e) {
//   var modal = document.getElementById("modalText");
//   modal.style.display = "block";

//   $('.close')[0].onclick = function() {
//     modal.style.display = "none";
//   }

//   // $('.submitTextBtn').onclick = function() {
//   //   modal.style.display = "none";
//   // }

//   // When the user clicks anywhere outside of the modal, close it
//   window.onclick = function(event) {
//     if (event.target == modal) {
//         modal.style.display = "none";
//     }
//   }
// });

// $(".submitTextBtn").change(function() {
//   var modal = document.getElementById("modalText");
//   modal.style.display = "none";
// });

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

  console.log(name + size + type)
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