// preloader.js
(function() {
  document.addEventListener("DOMContentLoaded", function() {
    /* load JSON image list from URL: /images */
    var imageUrls = JSON.parse(
      $.ajax({
        url: "/images",
        async: true,
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
  });
})();