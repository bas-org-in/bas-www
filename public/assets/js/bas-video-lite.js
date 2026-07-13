(function () {
  function youtubeEmbedUrl(id) {
    return 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(id) + '?autoplay=1&rel=0';
  }

  document.addEventListener('click', function (event) {
    var trigger = event.target.closest && event.target.closest('.bas-video-lite');
    if (!trigger) return;

    var id = trigger.getAttribute('data-youtube-id');
    if (!id) return;

    var iframe = document.createElement('iframe');
    iframe.className = 'bas-video-embed';
    iframe.width = '336';
    iframe.height = '189';
    iframe.src = youtubeEmbedUrl(id);
    iframe.title = trigger.getAttribute('data-title') || 'BAS video';
    iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
    iframe.allowFullscreen = true;

    trigger.replaceWith(iframe);
    iframe.focus();
  });
})();
