document.addEventListener("DOMContentLoaded", function () {
  var username = document.getElementById("id_username");
  if (username) {
    username.focus();
  }
  var messages = document.querySelector(".messages");
  if (messages) {
    messages.setAttribute("role", "status");
  }
  var search = document.querySelector(".global-search");
  if (search) {
    setupGlobalSearch(search);
  }
});

function setupGlobalSearch(form) {
  var input = form.querySelector("#global-search-input");
  var panel = form.querySelector("#global-search-results");
  var status = form.querySelector("#global-search-status");
  var hint = form.querySelector(".search-hint");
  var endpoint = form.getAttribute("data-search-url");
  var timer = null;
  var controller = null;
  var requestId = 0;
  var options = [];
  var activeIndex = -1;

  document.addEventListener("keydown", function (event) {
    var key = event.key;
    if ((event.ctrlKey || event.metaKey) && key.toLowerCase() === "k" && !event.altKey) {
      event.preventDefault();
      input.focus();
      input.select();
      return;
    }
    if (document.activeElement !== input && !panel.contains(document.activeElement)) {
      return;
    }
    if (key === "Escape") {
      event.preventDefault();
      ignorePending();
      if (!panel.hidden) {
        closePanel();
      } else {
        input.value = "";
        status.textContent = "";
      }
      return;
    }
    if (panel.hidden) {
      return;
    }
    if (key === "ArrowDown") {
      event.preventDefault();
      moveActive(1);
    } else if (key === "ArrowUp") {
      event.preventDefault();
      moveActive(-1);
    } else if (key === "Enter") {
      event.preventDefault();
      openActive();
    }
  });

  input.addEventListener("input", function () {
    if (hint) {
      hint.hidden = input.value.length > 0;
    }
    window.clearTimeout(timer);
    var term = input.value.trim();
    if (term.length < 2) {
      ignorePending();
      renderMessage(term.length === 0 ? "" : "Digite ao menos 2 caracteres.");
      return;
    }
    timer = window.setTimeout(function () {
      runSearch(term);
    }, 300);
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (panel.hidden) {
      return;
    }
    openActive();
  });

  document.addEventListener("click", function (event) {
    if (!form.contains(event.target)) {
      ignorePending();
      closePanel();
    }
  });

  function runSearch(term) {
    cancelRequest();
    requestId += 1;
    var current = requestId;
    controller = new AbortController();
    renderMessage("Buscando...");
    panel.setAttribute("aria-busy", "true");
    fetch(endpoint + "?q=" + encodeURIComponent(term), {
      headers: { Accept: "application/json" },
      credentials: "same-origin",
      signal: controller.signal,
    })
      .then(function (response) {
        if (!response.ok) {
          return response.json().then(function (payload) {
            throw new Error(payload.error || "Não foi possível buscar.");
          });
        }
        return response.json();
      })
      .then(function (payload) {
        if (current !== requestId) {
          return;
        }
        renderResults(payload, term);
      })
      .catch(function (error) {
        if (error.name === "AbortError" || current !== requestId) {
          return;
        }
        renderMessage("Não foi possível buscar. Tente de novo.");
      })
      .finally(function () {
        if (current === requestId) {
          panel.removeAttribute("aria-busy");
        }
      });
  }

  function renderResults(payload, term) {
    clearPanel();
    var groups = payload.groups || [];
    var count = 0;
    groups.forEach(function (group) {
      count += (group.results || []).length;
    });
    if (!count) {
      renderMessage(payload.message || "Nenhum resultado.");
      return;
    }
    groups.forEach(function (group) {
      if (!group.results || !group.results.length) {
        return;
      }
      var heading = document.createElement("p");
      heading.className = "search-group-label";
      heading.textContent = group.label || "";
      panel.appendChild(heading);
      group.results.forEach(function (result) {
        var option = document.createElement("button");
        option.type = "button";
        option.className = "search-option";
        option.setAttribute("role", "option");
        option.id = "search-option-" + options.length;
        option.setAttribute("aria-selected", "false");
        if (!isSafeUrl(result.url)) {
          return;
        }
        option.setAttribute("data-url", result.url);
        appendLine(option, "strong", result.title, term);
        appendLine(option, "small", result.detail, term);
        appendLine(option, "small", (result.type || "") + " · " + (result.meta || ""), term);
        option.addEventListener("click", function () {
          go(result.url);
        });
        panel.appendChild(option);
        options.push(option);
      });
    });
    if (!options.length) {
      renderMessage("Nenhum resultado.");
      return;
    }
    openPanel();
    status.textContent = count + " sugestões.";
  }

  function renderMessage(text) {
    clearPanel();
    if (!text) {
      closePanel();
      status.textContent = "";
      return;
    }
    var message = document.createElement("p");
    message.className = "search-state";
    message.textContent = text;
    panel.appendChild(message);
    openPanel();
    status.textContent = text;
  }

  function appendLine(parent, tag, text, term) {
    var line = document.createElement(tag);
    appendHighlighted(line, text || "", term);
    parent.appendChild(line);
  }

  function appendHighlighted(parent, text, term) {
    var needle = term || "";
    var source = text || "";
    if (!needle) {
      parent.appendChild(document.createTextNode(source));
      return;
    }
    var lowerSource = source.toLocaleLowerCase("pt-BR");
    var lowerNeedle = needle.toLocaleLowerCase("pt-BR");
    var start = 0;
    var index = lowerSource.indexOf(lowerNeedle);
    if (index === -1) {
      parent.appendChild(document.createTextNode(source));
      return;
    }
    while (index !== -1) {
      parent.appendChild(document.createTextNode(source.slice(start, index)));
      var mark = document.createElement("mark");
      mark.textContent = source.slice(index, index + needle.length);
      parent.appendChild(mark);
      start = index + needle.length;
      index = lowerSource.indexOf(lowerNeedle, start);
    }
    parent.appendChild(document.createTextNode(source.slice(start)));
  }

  function moveActive(step) {
    if (!options.length) {
      return;
    }
    if (activeIndex >= 0) {
      options[activeIndex].setAttribute("aria-selected", "false");
    }
    var next = activeIndex + step;
    if (next < 0) {
      next = options.length - 1;
    }
    if (next >= options.length) {
      next = 0;
    }
    activeIndex = next;
    options[activeIndex].setAttribute("aria-selected", "true");
    input.setAttribute("aria-activedescendant", options[activeIndex].id);
    options[activeIndex].scrollIntoView({ block: "nearest" });
  }

  function openActive() {
    if (activeIndex >= 0 && options[activeIndex]) {
      go(options[activeIndex].getAttribute("data-url"));
      return;
    }
    if (options.length) {
      go(options[0].getAttribute("data-url"));
    }
  }

  function go(url) {
    if (!isSafeUrl(url)) {
      return;
    }
    window.location.assign(url);
  }

  function isSafeUrl(url) {
    return typeof url === "string" && url.charAt(0) === "/" && url.charAt(1) !== "/";
  }

  function openPanel() {
    panel.hidden = false;
    input.setAttribute("aria-expanded", "true");
  }

  function closePanel() {
    panel.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    panel.textContent = "";
    options = [];
    activeIndex = -1;
    status.textContent = "";
  }

  function clearPanel() {
    panel.textContent = "";
    options = [];
    activeIndex = -1;
    input.removeAttribute("aria-activedescendant");
  }

  function ignorePending() {
    requestId += 1;
    cancelRequest();
  }

  function cancelRequest() {
    if (controller) {
      controller.abort();
      controller = null;
    }
  }
}
