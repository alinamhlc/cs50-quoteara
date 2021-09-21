$(document).ready(function () {
  $("#search").click(function () {
    /*
    listener for button with id="search"
    Get book information from Google Books API
    */

    var outputList = document.getElementById("list-books"); // div with rows for search results
    var bookUrl = "https://www.googleapis.com/books/v1/volumes?q="; // Google books API
    var searchData; // search input

    //empty html output
    outputList.innerHTML = "";

    // get input from the user
    searchData = $("#search-input").val();
    if (!(searchData === "" || searchData === null)) {
      $.ajax({
        // contact API and process the results
        url: bookUrl + searchData,
        dataType: "json",
        success: function (response) {
          if (response.totalItems === 0) {
            alert("no result!.. try again");
          } else {
            // Generate list results
            $(".search-results").css("visibility", "visible");
            displayResults(response);
          }
        },
        error: function () {
          alert("Something went wrong.. <br>" + "Try again!");
        },
      });
    }
    //clear search input
    $("#search-input").val("");
  });

  function displayResults(response) {
    /*
      function to display results of Google Books API call
      https://github.com/zentech/Book-Finder
     */
    var outputList = document.getElementById("list-books"); // div with rows for search results
    var item, title, author, bookImg;
    var placeHldrImg =
      "https://bitsofco.de/content/images/2018/12/broken-1.png"; // Placeholder image for search results without an image

    for (var i = 0; i < response.items.length; i++) {
      item = response.items[i];
      // Ensure title exists
      if (item.volumeInfo.title) {
        title = item.volumeInfo.title;
      } else {
        title = "";
      }
      // Ensure author exists
      if (item.volumeInfo.authors) {
        author = item.volumeInfo.authors;
      } else {
        author = "";
      }
      // Ensure image exists
      bookImg = placeHldrImg;
      if (item.volumeInfo.imageLinks) {
        if (item.volumeInfo.imageLinks.thumbnail) {
          bookImg = item.volumeInfo.imageLinks.thumbnail;
        }
      }
      // Ensure id exists
      if (item.id) {
        book_id = item.id;
      } else {
        book_id = "";
      }
      // Add HTML output
      outputList.innerHTML +=
        '<div class="row mt-4"> ' +
        formatOutput(bookImg, title, author, book_id);
    }
  }

  function formatOutput(bookImg, title, author, book_id) {
    /*
     * Format card element
     */
    var htmlCard = `
         <div class="card mb-3" style="max-width: 540px;">
           <div class="row g-0">
             <div class="col-md-4">
               <img src="${bookImg}" class="card-img" alt="book cover">
             </div>
             <div class="col-md-8">
               <div class="card-body">
                 <h6 class="card-title">${title}</h6>
                 <p class="card-text">Author: ${author}</p>

                  <button class="btn btn-secondary book_idbtn" value="${book_id}">Add to your list</button>
               </div>
             </div>
           </div>
       </div>`;
    return htmlCard;
  }

  $(document).on("click", ".book_idbtn", function (item) {
    /*
    Send book id to be added to users's list
    */
    $.ajax({
      data: {
        book_id: this.value,
      },
      type: "POST",
      url: "/processbook",
      success: function () {
        alert("Book added to your list");
      },
      error: function () {
        alert("Something went wrong. Missing data.");
      },
    });
    item.preventDefault();
  });

  $("#addnewquote").submit(function (addquote) {
    /*
    Send quote to be added to users's quotes list
    */

    if ($("#selectbook option:selected").length == 0) {
      // no book was selected
      addquote.preventDefault();
      alert("Select a book");
      return false;
    }

    if ($("#quote").val().length > 2049) {
      // text is too long
      addquote.preventDefault();
      alert("Text too long");
      return false;
    }
    if ($("#quote").val().length == 0) {
      // text is too long
      addquote.preventDefault();
      alert("Quote can't be empty");
      return false;
    }

    // Send data to be added to db
    $.ajax({
      data: {
        book_id: $("#selectbook").val(),
        quote: $("#quote").val(),
      },
      type: "POST",
      url: "/processquote",
      success: function () {
        alert("Quote added to your list");
      },
      error: function () {
        alert("Something went wrong. Missing data.");
      },
    });

    // Empty the textarea
    $("#quote").val("");
    addquote.preventDefault();
  });

  $("#scanPhoto").submit(function (event) {
    /*
      Send photo to be converted to txt and add txt to textarea
      */

    // Check that file was uploaded
    if ($("#my_upload").prop("files").length == 0) {
      alert("no file was selected");
      return false;
    }

    // Check that only one file is uploaded
    if ($("#my_upload").prop("files").length > 1) {
      alert("Only one file can be selected");
      return false;
    }

    // Check file format
    if (!isImage($("#my_upload").val())) {
      alert("Format file not supported.");
      return false;
    }

    // Create object for submission
    var formData = new FormData($("#scanPhoto")[0]);

    // Create Ajax request
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/processPhoto", true);

    xhr.onload = function () {
      // Handle the event after completion of upload
      if (xhr.status === 200) {
        if (this.responseText == "-1") {
          alert("Failed to convert image to text");
        } else {
          document.getElementById("quote").innerHTML = this.responseText;
        }
      } else {
        alert("File upload failed!");
      }
    };
    xhr.send(formData);

    event.preventDefault();
  });

  function getExtension(filename) {
    /*
    Get extension from filename
    https://stackoverflow.com/questions/7977084/check-file-type-when-form-submit
    */
    var parts = filename.split(".");
    return parts[parts.length - 1];
  }

  function isImage(filename) {
    /*
    Chek if the input file is a supported image format
    https://stackoverflow.com/questions/7977084/check-file-type-when-form-submit
    */
    var ext = getExtension(filename);
    switch (ext.toLowerCase()) {
      case "jpg":
      case "jpeg":
      case "bmp":
      case "png":
      case "tiff":
      case "gif":
        return true;
    }
    return false;
  }
});
