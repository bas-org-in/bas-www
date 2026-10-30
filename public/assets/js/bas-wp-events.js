/*
 * Shows the latest events on the home page (bas-site-ops
 * docs/style-system.md, ST-79 and ST-85).
 *
 * The section [data-bas-events] gets up to 3 cards in one request to
 * /wp-json/bas/v1/home-events, which the home page preloads. The server
 * puts the upcoming events first, soonest first (an event that has not
 * ended counts as upcoming), then the most recent past events. Without
 * an answer or without events, the section keeps only its heading and
 * the "All events" link.
 */
(function () {
  // The <link rel="preload"> of the home page names the same address, so
  // the browser uses its response.
  var defaultSource = "/wp-json/bas/v1/home-events";
  var maxCards = 3;

  function textFromHtml(html) {
    var template = document.createElement("template");
    template.innerHTML = html || "";
    return (template.content.textContent || "").replace(/\s+/g, " ").trim();
  }

  // "2026-10-31 09:00:00" is the event's local time. Format it as it is,
  // without a time zone change: "Sat, 31 Oct 2026, 9:00 am".
  function formatStart(value, allDay) {
    var parts = /^(\d{4})-(\d{2})-(\d{2})(?: (\d{2}):(\d{2}))?/.exec(value || "");
    if (!parts) {
      return "";
    }
    var date = new Date(Date.UTC(+parts[1], +parts[2] - 1, +parts[3], +(parts[4] || 0), +(parts[5] || 0)));
    var options = { weekday: "short", day: "numeric", month: "short", year: "numeric", timeZone: "UTC" };
    if (!allDay && parts[4] !== undefined) {
      options.hour = "numeric";
      options.minute = "2-digit";
      options.hour12 = true;
    }
    return date.toLocaleString("en-GB", options);
  }

  function imageUrl(event) {
    var image = event.image;
    if (!image) {
      return "";
    }
    var sizes = image.sizes || {};
    return (sizes.medium_large && sizes.medium_large.url) || image.url || "";
  }

  function fetchEntries(source) {
    return fetch(source, { credentials: "same-origin" }).then(function (response) {
      if (!response.ok) {
        throw new Error("home events " + response.status);
      }
      return response.json();
    });
  }

  function card(event, label) {
    var article = document.createElement("article");
    article.className = "bas-post-card bas-event-card";

    var src = imageUrl(event);
    if (src) {
      var imageLink = document.createElement("a");
      imageLink.className = "bas-post-card__image-link";
      imageLink.href = event.url;
      imageLink.tabIndex = -1;
      imageLink.setAttribute("aria-hidden", "true");
      var img = document.createElement("img");
      img.src = src;
      img.alt = "";
      img.loading = "lazy";
      img.decoding = "async";
      imageLink.appendChild(img);
      article.appendChild(imageLink);
    }

    var body = document.createElement("div");
    body.className = "bas-post-card__body";

    var tag = document.createElement("span");
    tag.className = "bas-event-card__label bas-event-card__label--" + label.toLowerCase();
    tag.textContent = label;
    body.appendChild(tag);

    var meta = document.createElement("div");
    meta.className = "bas-post-card__meta";
    meta.textContent = formatStart(event.start_date, event.all_day);
    body.appendChild(meta);

    var title = document.createElement("h3");
    title.className = "bas-post-card__title";
    var titleLink = document.createElement("a");
    titleLink.href = event.url;
    titleLink.textContent = textFromHtml(event.title);
    title.appendChild(titleLink);
    body.appendChild(title);

    var venue = event.venue && event.venue.venue ? textFromHtml(event.venue.venue) : "";
    if (venue) {
      var place = document.createElement("p");
      place.className = "bas-event-card__venue";
      place.textContent = venue;
      body.appendChild(place);
    }

    article.appendChild(body);
    return article;
  }

  function render(section) {
    var list = section.querySelector("[data-bas-events-list]");
    var source = section.getAttribute("data-bas-events-src") || defaultSource;
    if (!list || !window.fetch) {
      return;
    }
    fetchEntries(source).then(function (entries) {
      return (Array.isArray(entries) ? entries : []).slice(0, maxCards).map(function (entry) {
        return card(entry.event, entry.label);
      });
    }).then(function (cards) {
      cards.forEach(function (element) {
        list.appendChild(element);
      });
      list.hidden = cards.length === 0;
    }).catch(function () {
      // The heading and the "All events" link stay; nothing else shows.
      list.hidden = true;
    });
  }

  function start() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-bas-events]"), render);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
