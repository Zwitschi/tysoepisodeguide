// preloader.js
(function() {
    /* load JSON image list from URL: /static/images/ */
    var imageUrls = JSON.parse(
        $.ajax({
            url: "/static/images/",
            async: false,
            dataType: 'json'
        }).responseText
    );
      
    function preloadImage(url) {
      var img = new Image();
      img.src = url;
      img.height = '150px';
      img.width = '200px';
      
    }
  
    for (var i = 0; i < imageUrls.length; i++) {
      preloadImage(imageUrls[i]);
    }
  })();