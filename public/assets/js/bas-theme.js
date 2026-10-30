(function () {
  var storageKey = "bas-theme";
  var root = document.documentElement;
  var mediaQuery = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  function storedTheme() {
    try {
      var value = window.localStorage && window.localStorage.getItem(storageKey);
      return value === "dark" || value === "light" ? value : null;
    } catch (ignoredError) {
      return null;
    }
  }

  function systemTheme() {
    return mediaQuery && mediaQuery.matches ? "dark" : "light";
  }

  function activeTheme() {
    return storedTheme() || systemTheme();
  }

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    root.style.colorScheme = theme;
    updateToggle(theme);
  }

  function setStoredTheme(theme) {
    try {
      window.localStorage.setItem(storageKey, theme);
    } catch (ignoredError) {
      // Ignore private browsing or storage-denied environments.
    }
  }

  function updateToggle(theme) {
    var button = document.querySelector("[data-bas-theme-toggle]");
    if (!button) {
      return;
    }

    var nextTheme = theme === "dark" ? "light" : "dark";
    var label = "Switch to " + nextTheme + " mode";
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
    button.setAttribute("data-theme-current", theme);
    button.innerHTML = '<span class="bas-theme-toggle__icon" aria-hidden="true">' +
      (theme === "dark" ? "&#9728;" : "&#9790;") +
      "</span>";
  }

  function toggleTheme() {
    var nextTheme = activeTheme() === "dark" ? "light" : "dark";
    setStoredTheme(nextTheme);
    applyTheme(nextTheme);
  }

  applyTheme(activeTheme());

  if (mediaQuery) {
    var onSystemThemeChange = function () {
      if (!storedTheme()) {
        applyTheme(systemTheme());
      }
    };

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener("change", onSystemThemeChange);
    } else if (mediaQuery.addListener) {
      mediaQuery.addListener(onSystemThemeChange);
    }
  }

  // The "Menu" button of the nav bar (bas-site-ops docs/style-system.md,
  // ST-84). The bar gets the class bas-site-nav--menu when its links do not
  // fit in one row beside the brand and the toggle; the stylesheet then
  // hides the links behind the button. Without this script the links wrap.
  function setUpMenu() {
    var nav = document.querySelector(".bas-site-nav");
    var links = nav && nav.querySelector(".bas-site-nav__links");
    var brand = nav && nav.querySelector(".bas-site-nav__brand");
    var items = links ? links.querySelectorAll("a") : [];
    if (!links || !brand || !items.length) {
      return;
    }
    if (!links.id) {
      links.id = "bas-site-nav-links";
    }

    var button = document.createElement("button");
    button.type = "button";
    button.className = "bas-site-nav__menu-button";
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-controls", links.id);
    button.textContent = "Menu";
    links.parentNode.insertBefore(button, links);

    function setOpen(open) {
      nav.classList.toggle("bas-site-nav--open", open);
      button.setAttribute("aria-expanded", open ? "true" : "false");
    }

    function middle(element) {
      var box = element.getBoundingClientRect();
      return (box.top + box.bottom) / 2;
    }

    var pending = false;
    function measure() {
      pending = false;
      nav.classList.remove("bas-site-nav--menu");
      var first = items[0];
      var last = items[items.length - 1];
      var oneRow = Math.abs(first.getBoundingClientRect().top - last.getBoundingClientRect().top) < 2;
      var besideBrand = Math.abs(middle(first) - middle(brand)) < 8;
      var narrow = !(oneRow && besideBrand);
      nav.classList.toggle("bas-site-nav--menu", narrow);
      if (!narrow) {
        setOpen(false);
      }
    }
    function schedule() {
      if (!pending) {
        pending = true;
        window.requestAnimationFrame(measure);
      }
    }

    button.addEventListener("click", function () {
      setOpen(!nav.classList.contains("bas-site-nav--open"));
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("bas-site-nav--open")) {
        setOpen(false);
        button.focus();
      }
    });
    document.addEventListener("click", function (event) {
      if (nav.classList.contains("bas-site-nav--open") && !nav.contains(event.target)) {
        setOpen(false);
      }
    });
    measure();
    window.addEventListener("load", schedule);
    window.addEventListener("resize", schedule);
  }

  document.addEventListener("DOMContentLoaded", function () {
    setUpMenu();

    var button = document.querySelector("[data-bas-theme-toggle]");
    if (!button) {
      return;
    }

    updateToggle(activeTheme());
    button.addEventListener("click", toggleTheme);
  });
})();
