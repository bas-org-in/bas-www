/* Contents list of a long page (bas-site-ops docs/style-system.md, ST-81
   and ST-82). The page marks its content with data-bas-toc-root; the
   attribute value selects the section headings (default "h2"). The list
   goes into the element with data-bas-toc-slot when the page has one,
   and otherwise into a rail beside the content. The class bas-has-toc on
   the body turns the list on; the stylesheet does the layout. */
(function () {
  var MIN_SECTIONS = 4;
  var MIN_SCREENS = 3;
  var LIST_ID = "bas-page-toc-list";

  function slug(text, used) {
    var base = "bas-toc-" + (text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "section");
    var id = base;
    for (var n = 2; used[id] || document.getElementById(id); n += 1) {
      id = base + "-" + n;
    }
    used[id] = true;
    return id;
  }

  function sectionHeadings(root) {
    var selector = root.getAttribute("data-bas-toc-root") || "h2";
    return Array.prototype.filter.call(root.querySelectorAll(selector), function (heading) {
      return heading.textContent.trim() && !heading.closest(".bas-home-events, .bas-post-card");
    });
  }

  function build(headings) {
    var nav = document.createElement("nav");
    nav.className = "bas-page-toc";
    nav.setAttribute("aria-label", "On this page");

    var title = document.createElement("p");
    title.className = "bas-page-toc__title";
    title.textContent = "On this page";

    var button = document.createElement("button");
    button.type = "button";
    button.className = "bas-page-toc__button";
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-controls", LIST_ID);
    button.textContent = "On this page";

    var list = document.createElement("ol");
    list.className = "bas-page-toc__list";
    list.id = LIST_ID;
    var used = {};
    headings.forEach(function (heading) {
      if (!heading.id) {
        heading.id = slug(heading.textContent.trim(), used);
      }
      var item = document.createElement("li");
      var link = document.createElement("a");
      link.href = "#" + heading.id;
      link.textContent = heading.textContent.trim().replace(/\s+/g, " ");
      item.appendChild(link);
      list.appendChild(item);
    });

    nav.appendChild(title);
    nav.appendChild(button);
    nav.appendChild(list);
    return nav;
  }

  function place(root, nav) {
    var slot = document.querySelector("[data-bas-toc-slot]");
    if (slot) {
      slot.appendChild(nav);
      return;
    }
    var wrap = document.createElement("div");
    wrap.className = "bas-page-toc-wrap";
    var rail = document.createElement("div");
    rail.className = "bas-page-toc-rail";
    root.parentNode.insertBefore(wrap, root);
    rail.appendChild(nav);
    wrap.appendChild(rail);
    wrap.appendChild(root);
  }

  function wire(nav) {
    var button = nav.querySelector(".bas-page-toc__button");

    function setOpen(open) {
      nav.classList.toggle("bas-page-toc--open", open);
      button.setAttribute("aria-expanded", open ? "true" : "false");
    }

    button.addEventListener("click", function () {
      setOpen(!nav.classList.contains("bas-page-toc--open"));
    });
    nav.addEventListener("click", function (event) {
      if (event.target.closest(".bas-page-toc__list a")) {
        setOpen(false);
      }
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("bas-page-toc--open")) {
        setOpen(false);
        button.focus();
      }
    });
    document.addEventListener("click", function (event) {
      if (nav.classList.contains("bas-page-toc--open") && !nav.contains(event.target)) {
        setOpen(false);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var root = document.querySelector("[data-bas-toc-root]");
    if (!root) {
      return;
    }
    var headings = sectionHeadings(root);
    if (headings.length < MIN_SECTIONS) {
      return;
    }
    var nav = build(headings);
    place(root, nav);
    wire(nav);

    // The rule is measured without the list, so that the narrower column
    // of the list does not change the result.
    var body = document.body;
    var pending = false;
    function apply() {
      pending = false;
      body.classList.remove("bas-has-toc");
      var tall = root.getBoundingClientRect().height >= MIN_SCREENS * window.innerHeight;
      body.classList.toggle("bas-has-toc", tall);
    }
    function schedule() {
      if (!pending) {
        pending = true;
        window.requestAnimationFrame(apply);
      }
    }
    apply();
    window.addEventListener("load", schedule);
    window.addEventListener("resize", schedule);
  });
})();
