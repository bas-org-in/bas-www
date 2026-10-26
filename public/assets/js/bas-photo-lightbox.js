/*
 * Makes the home page photos buttons that open the BAS lightbox
 * (docs/style-system.md ST-67 to ST-70 in bas-org-in/bas-site-ops).
 *
 * The page marks each photo with data-bas-lightbox-src and loads the
 * lightbox scripts of the bas-gallery-publisher plugin before this one.
 * Only when they loaded does a photo get the button role, the tab stop, the
 * label and the zoom-in pointer of the article images (ST-58). Without them
 * the photos stay plain images.
 */
(function () {
  'use strict';

  if (!window.BASLightbox) {
    return;
  }

  Array.prototype.slice.call(document.querySelectorAll('img[data-bas-lightbox-src]')).forEach(function (image) {
    var alt = (image.getAttribute('alt') || '').trim();

    image.setAttribute('role', 'button');
    image.setAttribute('tabindex', '0');
    image.setAttribute('aria-haspopup', 'dialog');
    image.setAttribute('aria-label', alt ? 'Open image viewer: ' + alt : 'Open image viewer');
    image.classList.add('bas-lightbox-trigger');
  });
}());
