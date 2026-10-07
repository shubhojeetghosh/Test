(function () {
  const storageKey = "eps-topik-theme";
  let savedTheme = "light";
  try {
    savedTheme = localStorage.getItem(storageKey) || localStorage.getItem("eps_theme") || "light";
    if (savedTheme === "dark" || savedTheme === "light") {
      localStorage.setItem(storageKey, savedTheme);
    }
  } catch (error) {
    // Keep the page usable when browser storage is disabled.
  }
  const initialTheme = savedTheme === "dark" ? "dark" : "light";

  document.documentElement.dataset.theme = initialTheme;

  function colorParts(value) {
    const parts = value.match(/[\d.]+/g);
    if (!parts || parts.length < 3) return null;
    return {
      red: Number(parts[0]),
      green: Number(parts[1]),
      blue: Number(parts[2]),
      alpha: parts.length > 3 ? Number(parts[3]) : 1
    };
  }

  function brightness(color) {
    return (color.red * 299 + color.green * 587 + color.blue * 114) / 1000;
  }

  function refreshThemeContrast() {
    const body = document.body;
    if (!body) return;

    const marked = body.querySelectorAll("[data-theme-surface], [data-theme-text]");
    if (document.documentElement.dataset.theme !== "dark") {
      marked.forEach(function (element) {
        element.removeAttribute("data-theme-surface");
        element.removeAttribute("data-theme-text");
      });
      if (body.hasAttribute("data-theme-surface")) {
        body.removeAttribute("data-theme-surface");
      }
      body.removeAttribute("data-theme-text");
      return;
    }

    // Re-scan the current appearance so states such as selected answers keep
    // their own colors instead of inheriting a stale light-surface marker.
    marked.forEach(function (element) {
      element.removeAttribute("data-theme-surface");
      element.removeAttribute("data-theme-text");
    });
    body.removeAttribute("data-theme-surface");
    body.removeAttribute("data-theme-text");

    const elements = [body, ...body.querySelectorAll("*")].filter(function (element) {
      return !element.closest("svg") && !/^(SCRIPT|STYLE|NOSCRIPT|LINK|META|PATH|DEFS|LINEARGRADIENT|STOP|FILTER|CIRCLE|PATH|RECT|POLYLINE|TEXT)$/.test(element.tagName);
    });
    const appearances = elements.map(function (element) {
      const computed = window.getComputedStyle(element);
      return {
        element: element,
        background: colorParts(computed.backgroundColor),
        color: colorParts(computed.color)
      };
    });
    const backgroundByElement = new Map();

    appearances.forEach(function (appearance) {
      const color = appearance.background;
      const lightSurface = color && color.alpha >= .75 && brightness(color) >= 205;
      if (lightSurface) {
        appearance.element.setAttribute("data-theme-surface", "light");
      }
      if (color && color.alpha >= .75) {
        backgroundByElement.set(appearance.element, {
          color: color,
          light: brightness(color) >= 205
        });
      }
    });

    appearances.forEach(function (appearance) {
      const element = appearance.element;
      const textColor = appearance.color;
      if (!textColor || element.matches("input[type=hidden], script, style")) return;

      let ancestor = element;
      let surface = null;
      while (ancestor && ancestor !== body.parentElement) {
        surface = backgroundByElement.get(ancestor);
        if (surface) break;
        const background = colorParts(window.getComputedStyle(ancestor).backgroundColor);
        if (background && background.alpha >= .75) {
          surface = { color: background, light: brightness(background) >= 205 };
          break;
        }
        ancestor = ancestor.parentElement;
      }

      if (!surface) return;
      const textBrightness = brightness(textColor);
      if (surface.light) {
        element.setAttribute("data-theme-text", "light");
      } else if (!surface.light && textBrightness < 125) {
        element.setAttribute("data-theme-text", "light");
      }
    });
  }

  let refreshTimer;
  function scheduleContrastRefresh() {
    window.clearTimeout(refreshTimer);
    refreshTimer = window.setTimeout(refreshThemeContrast, 60);
  }

  function syncThemeButton(button) {
    const isDark = document.documentElement.dataset.theme === "dark";
    button.setAttribute("aria-pressed", String(isDark));
    button.setAttribute(
      "aria-label",
      isDark ? "Turn off dark theme" : "Turn on dark theme"
    );

    const icon = button.querySelector(".theme-toggle-icon");
    const label = button.querySelector(".theme-toggle-label");
    if (icon) icon.textContent = isDark ? "☀" : "☾";
    if (label) label.textContent = isDark ? "Light" : "Dark";
  }

  // Keep already-open student and admin tabs in step with the index toggle.
  window.addEventListener("storage", function (event) {
    if (event.key !== storageKey && event.key !== "eps_theme") return;

    document.documentElement.dataset.theme =
      event.newValue === "dark" ? "dark" : "light";
    if (event.key === "eps_theme") {
      try { localStorage.setItem(storageKey, event.newValue === "dark" ? "dark" : "light"); } catch (error) {}
    }
    refreshThemeContrast();
    document.querySelectorAll("[data-theme-toggle]").forEach(syncThemeButton);
  });

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
      syncThemeButton(button);
      button.addEventListener("click", function () {
        const nextTheme =
          document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        document.documentElement.dataset.theme = nextTheme;
        refreshThemeContrast();
        try {
          localStorage.setItem(storageKey, nextTheme);
          localStorage.setItem("eps_theme", nextTheme);
        } catch (error) {
          // The current page still changes theme even if persistence is blocked.
        }
        syncThemeButton(button);
      });
    });

    refreshThemeContrast();
    const contentObserver = new MutationObserver(scheduleContrastRefresh);
    contentObserver.observe(document.body, {
      attributes: true,
      attributeFilter: ["class", "style"],
      childList: true,
      subtree: true
    });
  });
})();
