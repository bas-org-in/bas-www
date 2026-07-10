(function () {
  var storageKey = "bas-theme";
  var root = document.documentElement;
  var mediaQuery = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  function storedTheme() {
    try {
      var value = window.localStorage && window.localStorage.getItem(storageKey);
      return value === "dark" || value === "light" ? value : null;
    } catch (error) {
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
    } catch (error) {
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

  document.addEventListener("DOMContentLoaded", function () {
    var button = document.querySelector("[data-bas-theme-toggle]");
    if (!button) {
      return;
    }

    updateToggle(activeTheme());
    button.addEventListener("click", toggleTheme);
  });
})();
