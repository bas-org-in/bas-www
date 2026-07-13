(function () {
  'use strict';

  var lazyImages = Array.prototype.slice.call(document.querySelectorAll('img[data-src]'));

  function loadImage(image) {
    var source = image.getAttribute('data-src');

    if (!source) {
      return;
    }

    image.src = source;
    image.removeAttribute('data-src');
    image.classList.add('bas-lazy-media--loaded');
  }

  if (!('IntersectionObserver' in window)) {
    lazyImages.forEach(loadImage);
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) {
        return;
      }

      observer.unobserve(entry.target);
      loadImage(entry.target);
    });
  }, {
    rootMargin: '160px 0px',
    threshold: 0.01
  });

  lazyImages.forEach(function (image) {
    observer.observe(image);
  });
}());
