/*
 * Lists BAS articles from the WordPress REST API on the static pages.
 *
 * An article is a published post in the Articles category (slug "blogs").
 * A post that is also in a category with the slug "gallery" is left out,
 * when that category exists. The list asks the REST API at /wp-json/ for
 * these posts only, with the category IDs looked up by slug, and each card
 * links to the article address that WordPress gives in the post's "link"
 * field (/blogs/<post name>/).
 *
 * An old single-post link, /blogs/?post=<post name>, goes on to the
 * address of that post with location.replace().
 *
 * /blogs/?topic=<tag slug> lists only the articles with that post tag, for the
 * known topics only (AA-30 to AA-32). The tag ID is looked up by its slug.
 * /blogs/?page=<n> shows the next articles, with links between pages (AA-33,
 * AA-34).
 */
(function () {
  var defaultPostsApi = "/wp-json/wp/v2/posts";
  var defaultCategoriesApi = "/wp-json/wp/v2/categories";
  var defaultCategory = "blogs";
  var defaultExcludeCategory = "gallery";
  var emptyMessage = "No articles are published yet.";
  var errorMessage = "Articles are not available at the moment.";
  var notFoundMessage = "This post was not found.";
  var noTopicMessage = "No articles on this topic yet.";
  var defaultTagsApi = "/wp-json/wp/v2/tags";
  var topics = ["awe", "star-party"];

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

  // The posts of one page, and the number of pages from the X-WP-TotalPages
  // header. A page past the last answers HTTP 400, which gives no posts.
  function fetchPage(url) {
    return fetch(url, { credentials: "same-origin" }).then(function (response) {
      if (response.status === 400) {
        return { posts: [], pages: 0 };
      }
      if (!response.ok) {
        throw new Error("WordPress returned HTTP " + response.status);
      }
      var pages = parseInt(response.headers.get("X-WP-TotalPages") || "1", 10);
      return response.json().then(function (posts) {
        return { posts: posts, pages: pages };
      });
    });
  }

  // The address of a page of the listing, with its topic.
  function listingHref(topic, page) {
    var params = [];
    if (topic) {
      params.push("topic=" + encodeURIComponent(topic));
    }
    if (page > 1) {
      params.push("page=" + page);
    }
    return "/blogs/" + (params.length ? "?" + params.join("&") : "");
  }

  function pageLinks(topic, page, pages) {
    var nav = document.createElement("nav");
    nav.className = "bas-wp-posts__pages";
    nav.setAttribute("aria-label", "Pages of articles");
    if (page > 1) {
      var newer = document.createElement("a");
      newer.href = listingHref(topic, page - 1);
      newer.textContent = "Newer articles";
      nav.appendChild(newer);
    }
    if (page < pages) {
      var older = document.createElement("a");
      older.href = listingHref(topic, page + 1);
      older.textContent = "Older articles";
      nav.appendChild(older);
    }
    return nav.children.length ? nav : null;
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

  // The ID of a topic's post tag, or null when the tag does not exist.
  function tagId(container, topic) {
    if (!topic) {
      return window.Promise.resolve(undefined);
    }
    var api = container.getAttribute("data-bas-wp-tags-api") || defaultTagsApi;
    return fetchJson(buildUrl(api, { slug: topic, _fields: "id,slug" })).then(function (terms) {
      var term = (Array.isArray(terms) ? terms : []).filter(function (item) {
        return item && item.slug === topic;
      })[0];
      return term ? term.id : null;
    });
  }

  function renderPostList(container, topic, page) {
    page = page || 1;
    var paged = container.hasAttribute("data-bas-wp-post");
    var api = container.getAttribute("data-bas-wp-api") || defaultPostsApi;
    var count = container.getAttribute("data-bas-wp-count") || "6";
    var layout = container.getAttribute("data-bas-wp-layout") || "grid";
    var empty = topic ? noTopicMessage : (container.getAttribute("data-bas-wp-empty") || emptyMessage);

    setStatus(container, "Loading articles...");

    window.Promise.all([categoryIds(container), tagId(container, topic)])
      .then(function (found) {
        var ids = found[0];
        var tag = found[1];
        if (ids.articles === null || tag === null) {
          return { posts: [], pages: 0 };
        }
        return fetchPage(buildUrl(api, {
          per_page: count,
          page: page > 1 ? page : "",
          categories: ids.articles,
          categories_exclude: ids.excluded,
          tags: tag,
          _embed: "1"
        }));
      })
      .then(function (result) {
        var posts = result.posts;
        var links = paged ? pageLinks(topic, page, result.pages) : null;
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
        } else {
          container.innerHTML = "";
          container.appendChild(list);
        }
        if (links) {
          container.appendChild(links);
        }
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

  // Marks the link of the current topic (AA-30).
  function markTopic(topic) {
    var want = topic ? "/blogs/?topic=" + topic : "/blogs/";
    Array.prototype.slice.call(document.querySelectorAll(".bas-topic-links a")).forEach(function (link) {
      if (link.getAttribute("href") === want) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    Array.prototype.slice.call(document.querySelectorAll("[data-bas-wp-posts]")).forEach(function (container) {
      renderPostList(container, "");
    });

    var params = new URLSearchParams(window.location.search);
    var topic = topics.indexOf(params.get("topic")) >= 0 ? params.get("topic") : "";
    var page = /^[1-9][0-9]*$/.test(params.get("page") || "") ? parseInt(params.get("page"), 10) : 1;
    markTopic(topic);

    Array.prototype.slice.call(document.querySelectorAll("[data-bas-wp-post]")).forEach(function (container) {
      var slug = params.get("post");
      if (slug) {
        redirectToPost(container, slug);
      } else {
        renderPostList(container, topic, page);
      }
    });
  });
})();
