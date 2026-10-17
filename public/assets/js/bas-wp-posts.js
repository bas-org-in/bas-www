/*
 * Lists BAS articles from the WordPress REST API on the static pages.
 *
 * An article is a published post in the Articles category that is not in
 * the Gallery category. The list asks the REST API for these posts only,
 * with the category IDs looked up by slug, and each card links to the
 * article address that WordPress gives in the post's "link" field
 * (/blogs/<post name>/).
 *
 * An old single-post link, /blogs/?post=<post name>, goes on to the
 * address of that post with location.replace().
 */
(function () {
  var defaultPostsApi = "/gallery/wp-json/wp/v2/posts";
  var defaultCategoriesApi = "/gallery/wp-json/wp/v2/categories";
  var defaultCategory = "articles";
  var defaultExcludeCategory = "gallery";
  var emptyMessage = "No articles are published yet.";
  var errorMessage = "Articles are not available at the moment.";
  var notFoundMessage = "This post was not found.";

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

  // The address of a post: the "link" field of the REST API. Only http and
  // https addresses are used.
  function postHref(post) {
    try {
      var url = new URL(post && post.link, window.location.origin);
      return url.protocol === "https:" || url.protocol === "http:" ? url.href : "";
    } catch (ignoredError) {
      return "";
    }
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

  function createPostCard(post, href, options) {
    var article = document.createElement("article");
    article.className = "bas-post-card";

    var image = postImage(post);
    if (image && options.showImage !== false) {
      var imageLink = document.createElement("a");
      imageLink.className = "bas-post-card__image-link";
      imageLink.href = href;

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
    titleLink.href = href;
    titleLink.textContent = textFromHtml(post.title && post.title.rendered) || "Untitled article";
    title.appendChild(titleLink);
    body.appendChild(title);

    var excerpt = document.createElement("p");
    excerpt.className = "bas-post-card__excerpt";
    excerpt.textContent = textFromHtml(post.excerpt && post.excerpt.rendered);
    body.appendChild(excerpt);

    var link = document.createElement("a");
    link.className = "bas-button bas-button--subtle";
    link.href = href;
    link.textContent = "Read article";
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

  // Looks up the IDs of the article category and the excluded category by
  // their slugs. The result has articles: null when the category is missing.
  function categoryIds(container) {
    var api = container.getAttribute("data-bas-wp-categories-api") || defaultCategoriesApi;
    var include = container.getAttribute("data-bas-wp-category") || defaultCategory;
    var exclude = container.getAttribute("data-bas-wp-exclude-category") || defaultExcludeCategory;

    return fetchJson(buildUrl(api, { slug: include + "," + exclude, _fields: "id,slug" })).then(function (terms) {
      var ids = { articles: null, excluded: null };
      (Array.isArray(terms) ? terms : []).forEach(function (term) {
        if (term && term.slug === include) {
          ids.articles = term.id;
        } else if (term && term.slug === exclude) {
          ids.excluded = term.id;
        }
      });
      return ids;
    });
  }

  function renderPostList(container) {
    var api = container.getAttribute("data-bas-wp-api") || defaultPostsApi;
    var count = container.getAttribute("data-bas-wp-count") || "6";
    var layout = container.getAttribute("data-bas-wp-layout") || "grid";
    var empty = container.getAttribute("data-bas-wp-empty") || emptyMessage;

    setStatus(container, "Loading articles...");

    categoryIds(container)
      .then(function (ids) {
        if (ids.articles === null) {
          return [];
        }
        return fetchJson(buildUrl(api, {
          per_page: count,
          categories: ids.articles,
          categories_exclude: ids.excluded,
          _embed: "1"
        }));
      })
      .then(function (posts) {
        var list = document.createElement("div");
        list.className = layout === "compact" ? "bas-post-list bas-post-list--compact" : "bas-post-list";
        (Array.isArray(posts) ? posts : []).forEach(function (post) {
          var href = postHref(post);
          if (href) {
            list.appendChild(createPostCard(post, href, { showImage: layout !== "compact" }));
          }
        });

        if (!list.children.length) {
          setStatus(container, empty);
          return;
        }
        container.innerHTML = "";
        container.appendChild(list);
      })
      .catch(function () {
        setStatus(container, errorMessage, "error");
      });
  }

  // An old single-post link: go on to the address of the post, without a
  // history entry for the old link.
  function redirectToPost(container, slug) {
    var api = container.getAttribute("data-bas-wp-api") || defaultPostsApi;

    setStatus(container, "Opening the post...");

    fetchJson(buildUrl(api, { slug: slug, _fields: "link" }))
      .then(function (posts) {
        var href = Array.isArray(posts) && posts[0] ? postHref(posts[0]) : "";
        if (!href) {
          setStatus(container, notFoundMessage, "error");
          return;
        }
        window.location.replace(href);
      })
      .catch(function () {
        setStatus(container, errorMessage, "error");
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    Array.prototype.slice.call(document.querySelectorAll("[data-bas-wp-posts]")).forEach(renderPostList);

    Array.prototype.slice.call(document.querySelectorAll("[data-bas-wp-post]")).forEach(function (container) {
      var params = new URLSearchParams(window.location.search);
      var slug = params.get("post");
      if (slug) {
        redirectToPost(container, slug);
      } else {
        renderPostList(container);
      }
    });
  });
})();
