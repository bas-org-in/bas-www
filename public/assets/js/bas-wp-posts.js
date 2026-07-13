(function () {
  var defaultPostsApi = "/gallery/wp-json/wp/v2/posts";
  var defaultMediaApi = "/gallery/wp-json/wp/v2/media";

  function textFromHtml(html) {
    var template = document.createElement("template");
    template.innerHTML = html || "";
    return (template.content.textContent || "").replace(/\s+/g, " ").trim();
  }

  function formatDate(value) {
    if (!value) {
      return "";
    }

    var date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return "";
    }

    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric"
    });
  }

  function postImage(post) {
    var media = post && post._embedded && post._embedded["wp:featuredmedia"];
    var image = media && media[0];
    if (!image || !image.source_url) {
      return null;
    }

    return {
      src: image.source_url,
      alt: image.alt_text || textFromHtml(post.title && post.title.rendered)
    };
  }

  function localPostHref(post) {
    var slug = post && post.slug ? post.slug : "";
    return "/blogs/" + (slug ? "?post=" + encodeURIComponent(slug) : "");
  }

  function buildUrl(base, params) {
    var url = new URL(base, window.location.origin);
    Object.keys(params).forEach(function (key) {
      if (params[key] !== undefined && params[key] !== null && params[key] !== "") {
        url.searchParams.set(key, params[key]);
      }
    });
    return url.toString();
  }

  function createPostCard(post, options) {
    var article = document.createElement("article");
    article.className = "bas-post-card";

    var image = postImage(post);
    if (image && options.showImage !== false) {
      var imageLink = document.createElement("a");
      imageLink.className = "bas-post-card__image-link";
      imageLink.href = localPostHref(post);

      var img = document.createElement("img");
      img.src = image.src;
      img.alt = image.alt;
      img.loading = "lazy";
      img.decoding = "async";
      imageLink.appendChild(img);
      article.appendChild(imageLink);
    }

    var body = document.createElement("div");
    body.className = "bas-post-card__body";

    var meta = document.createElement("div");
    meta.className = "bas-post-card__meta";
    meta.textContent = formatDate(post.date);
    body.appendChild(meta);

    var title = document.createElement("h3");
    title.className = "bas-post-card__title";
    var titleLink = document.createElement("a");
    titleLink.href = localPostHref(post);
    titleLink.textContent = textFromHtml(post.title && post.title.rendered) || "Untitled post";
    title.appendChild(titleLink);
    body.appendChild(title);

    var excerpt = document.createElement("p");
    excerpt.className = "bas-post-card__excerpt";
    excerpt.textContent = textFromHtml(post.excerpt && post.excerpt.rendered);
    body.appendChild(excerpt);

    var link = document.createElement("a");
    link.className = "bas-button bas-button--subtle";
    link.href = localPostHref(post);
    link.textContent = "Read post";
    body.appendChild(link);

    article.appendChild(body);
    return article;
  }

  function setStatus(container, message, tone) {
    container.innerHTML = "";
    var status = document.createElement("p");
    status.className = "bas-wp-posts__status" + (tone ? " bas-wp-posts__status--" + tone : "");
    status.textContent = message;
    container.appendChild(status);
  }

  function fetchJson(url) {
    return fetch(url, { credentials: "same-origin" }).then(function (response) {
      if (!response.ok) {
        throw new Error("WordPress returned HTTP " + response.status);
      }
      return response.json();
    });
  }

  function renderPostList(container) {
    var api = container.getAttribute("data-bas-wp-api") || defaultPostsApi;
    var count = container.getAttribute("data-bas-wp-count") || "6";
    var layout = container.getAttribute("data-bas-wp-layout") || "grid";

    setStatus(container, "Loading BAS posts...");

    fetchJson(buildUrl(api, { per_page: count, _embed: "1" }))
      .then(function (posts) {
        container.innerHTML = "";
        if (!posts.length) {
          setStatus(container, container.getAttribute("data-bas-wp-empty") || "No posts are available yet.");
          return;
        }

        var list = document.createElement("div");
        list.className = layout === "compact" ? "bas-post-list bas-post-list--compact" : "bas-post-list";
        posts.forEach(function (post) {
          list.appendChild(createPostCard(post, { showImage: layout !== "compact" }));
        });
        container.appendChild(list);
      })
      .catch(function () {
        setStatus(container, "BAS posts are temporarily unavailable.", "error");
      });
  }

  function enhanceImages(article, mediaApi) {
    var images = Array.prototype.slice.call(article.querySelectorAll("img[data-attachment-id]"));
    if (!images.length) {
      return;
    }

    images.forEach(function (img) {
      var id = img.getAttribute("data-attachment-id");
      fetchJson(buildUrl(mediaApi + "/" + encodeURIComponent(id), {}))
        .then(function (media) {
          if (media && media.source_url) {
            img.src = media.source_url;
          }
        })
        .catch(function () {
          return null;
        });
    });
  }

  function renderSinglePost(container, slug) {
    var api = container.getAttribute("data-bas-wp-api") || defaultPostsApi;
    var mediaApi = container.getAttribute("data-bas-wp-media-api") || defaultMediaApi;

    setStatus(container, "Loading BAS post...");

    fetchJson(buildUrl(api, { slug: slug, _embed: "1" }))
      .then(function (posts) {
        container.innerHTML = "";
        var post = posts[0];
        if (!post) {
          setStatus(container, "This BAS post was not found.", "error");
          return;
        }

        var article = document.createElement("article");
        article.className = "bas-post";

        var back = document.createElement("a");
        back.className = "bas-post__back";
        back.href = "/blogs/";
        back.textContent = "All posts";
        article.appendChild(back);

        var title = document.createElement("h1");
        title.textContent = textFromHtml(post.title && post.title.rendered) || "Untitled post";
        article.appendChild(title);

        var meta = document.createElement("p");
        meta.className = "bas-post__meta";
        meta.textContent = formatDate(post.date);
        article.appendChild(meta);

        var image = postImage(post);
        if (image) {
          var img = document.createElement("img");
          img.className = "bas-post__featured-image";
          img.src = image.src;
          img.alt = image.alt;
          img.decoding = "async";
          article.appendChild(img);
        }

        var content = document.createElement("div");
        content.className = "bas-post__content";
        content.innerHTML = post.content && post.content.rendered ? post.content.rendered : "";
        article.appendChild(content);
        enhanceImages(article, mediaApi);

        container.appendChild(article);
        document.title = title.textContent + " · BAS Blogs";
      })
      .catch(function () {
        setStatus(container, "This BAS post is temporarily unavailable.", "error");
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    Array.prototype.slice.call(document.querySelectorAll("[data-bas-wp-posts]")).forEach(renderPostList);

    Array.prototype.slice.call(document.querySelectorAll("[data-bas-wp-post]")).forEach(function (container) {
      var params = new URLSearchParams(window.location.search);
      var slug = params.get("post");
      if (slug) {
        renderSinglePost(container, slug);
      } else {
        renderPostList(container);
      }
    });
  });
})();
