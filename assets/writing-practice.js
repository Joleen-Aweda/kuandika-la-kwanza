(function () {
  "use strict";

  var STORE_PREFIX = "kuandika-practice-v1:";
  var MAX_CARDS = 32;

  function storageKey(id) {
    return STORE_PREFIX + location.pathname + ":" + id;
  }

  function readStored(id) {
    try {
      return window.localStorage.getItem(storageKey(id));
    } catch (_error) {
      return null;
    }
  }

  function writeStored(id, value) {
    try {
      window.localStorage.setItem(storageKey(id), value);
    } catch (_error) {
      // The activity remains usable if private browsing blocks storage.
    }
  }

  function removeStored(id) {
    try {
      window.localStorage.removeItem(storageKey(id));
    } catch (_error) {
      // The visible canvas can still be cleared without persistent storage.
    }
  }

  function cleanText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function visibleLabel(control) {
    return cleanText(
      control.getAttribute("aria-label") ||
      control.getAttribute("placeholder") ||
      "Andika jibu lako."
    );
  }

  function isDrawingPrompt(text) {
    return /\b(chora|mchoro|picha|trace|fanya mchoro)\b/i.test(text);
  }

  function uniquePush(items, seen, item) {
    var signature = cleanText(item.prompt).toLowerCase() + "|" + item.kind;
    if (!signature || seen.has(signature)) return;
    seen.add(signature);
    items.push(item);
  }

  function collectTasks(section) {
    var items = [];
    var seen = new Set();
    var controls = section.querySelectorAll(
      'input[type="text"][data-activity-item], input[type="search"][data-activity-item], textarea[data-activity-item]'
    );

    controls.forEach(function (control) {
      var prompt = visibleLabel(control);
      uniquePush(items, seen, {
        prompt: prompt,
        kind: isDrawingPrompt(prompt) ? "drawing" : "writing",
      });
    });

    if (!items.length) {
      var images = section.querySelectorAll("img[data-id]");
      if (images.length && /\bchora\b/i.test(section.textContent || "")) {
        images.forEach(function (image, index) {
          var name = cleanText(image.getAttribute("alt"));
          uniquePush(items, seen, {
            prompt: name ? "Chora: " + name : "Chora picha ya " + (index + 1) + ".",
            kind: "drawing",
          });
        });
      }
    }

    if (!items.length) {
      section.querySelectorAll("[data-id]").forEach(function (element) {
        var text = cleanText(element.textContent);
        if (!text || text.length > 180) return;
        if (/\b(Chora|Fuatisha|Andika|Nakili|Jaza|Tunga|Panga|Unganisha)\b/i.test(text)) {
          uniquePush(items, seen, {
            prompt: text,
            kind: isDrawingPrompt(text) ? "drawing" : "writing",
          });
        }
      });
    }

    return items.slice(0, MAX_CARDS);
  }

  function canvasPoint(canvas, event) {
    var rect = canvas.getBoundingClientRect();
    return {
      x: (event.clientX - rect.left) * (canvas.width / rect.width),
      y: (event.clientY - rect.top) * (canvas.height / rect.height),
    };
  }

  function initialiseCard(card) {
    var canvas = card.querySelector("canvas");
    var clear = card.querySelector(".practice-clear");
    var status = card.querySelector(".practice-status");
    var alternative = card.querySelector(".practice-alternative");
    var context = canvas.getContext("2d");
    var id = canvas.id;
    var drawing = false;
    var strokeMade = false;

    context.lineCap = "round";
    context.lineJoin = "round";
    context.lineWidth = 6;
    context.strokeStyle = "#172033";

    function updateStatus() {
      var complete = canvas.dataset.hasDrawing === "true" || alternative.value.trim() !== "";
      status.textContent = complete ? "Jibu limehifadhiwa." : "";
      status.setAttribute("aria-label", complete ? "Jibu limehifadhiwa" : "Hakuna jibu bado");
    }

    var storedDrawing = readStored(id + ":drawing");
    var storedText = readStored(id + ":text");
    canvas.dataset.hasDrawing = storedDrawing ? "true" : "false";
    if (storedDrawing) {
      var image = new Image();
      image.addEventListener("load", function () {
        context.drawImage(image, 0, 0, canvas.width, canvas.height);
      });
      image.src = storedDrawing;
    }
    if (storedText !== null) alternative.value = storedText;
    updateStatus();

    canvas.addEventListener("pointerdown", function (event) {
      event.preventDefault();
      drawing = true;
      strokeMade = false;
      canvas.setPointerCapture(event.pointerId);
      var point = canvasPoint(canvas, event);
      context.beginPath();
      context.moveTo(point.x, point.y);
    });

    canvas.addEventListener("pointermove", function (event) {
      if (!drawing) return;
      event.preventDefault();
      var point = canvasPoint(canvas, event);
      context.lineTo(point.x, point.y);
      context.stroke();
      strokeMade = true;
    });

    function finish(event) {
      if (!drawing) return;
      drawing = false;
      if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
      if (strokeMade) {
        canvas.dataset.hasDrawing = "true";
        writeStored(id + ":drawing", canvas.toDataURL("image/png"));
        updateStatus();
      }
    }

    canvas.addEventListener("pointerup", finish);
    canvas.addEventListener("pointercancel", finish);

    clear.addEventListener("click", function () {
      context.clearRect(0, 0, canvas.width, canvas.height);
      canvas.dataset.hasDrawing = "false";
      removeStored(id + ":drawing");
      updateStatus();
      canvas.focus();
    });

    alternative.addEventListener("input", function () {
      writeStored(id + ":text", alternative.value);
      updateStatus();
    });
  }

  function createPracticePanel(sourceImage, section, tasks) {
    if (!tasks.length || document.querySelector(".interactive-practice")) return;

    var sectionId = section.getAttribute("data-section-id") || "page";
    var panel = document.createElement("section");
    panel.className = "interactive-practice";
    panel.setAttribute("aria-labelledby", sectionId + "-practice-title");
    panel.innerHTML =
      '<header class="interactive-practice__header">' +
      '<h2 class="interactive-practice__title" id="' + sectionId + '-practice-title">Eneo la mazoezi</h2>' +
      '<p class="interactive-practice__help">Chora au andika kwenye nafasi zilizo hapa chini. Unaweza pia kuandika jibu kwa kibodi au kwa kifaa cha breli. Majibu yanahifadhiwa kwenye kifaa hiki.</p>' +
      '</header><div class="interactive-practice__grid"></div>';

    var grid = panel.querySelector(".interactive-practice__grid");
    tasks.forEach(function (task, index) {
      var id = sectionId + "-practice-" + String(index + 1).padStart(2, "0");
      var card = document.createElement("article");
      card.className = "practice-card";
      card.dataset.practiceKind = task.kind;
      var height = task.kind === "drawing" ? 420 : 240;
      card.innerHTML =
        '<label class="practice-card__prompt" id="' + id + '-label" for="' + id + '">' + task.prompt + '</label>' +
        '<div class="practice-canvas-wrap"><canvas class="practice-canvas" id="' + id + '" width="960" height="' + height + '" tabindex="0" role="img" aria-labelledby="' + id + '-label" data-has-drawing="false"></canvas></div>' +
        '<div class="practice-card__controls"><button class="practice-clear" type="button">Futa mchoro</button><span class="practice-status" role="status" aria-live="polite"></span></div>' +
        '<label class="practice-alternative-label" for="' + id + '-text">Jibu kwa kuandika au kutumia breli</label>' +
        '<input class="practice-alternative" id="' + id + '-text" type="text" autocomplete="off" spellcheck="false">';
      grid.appendChild(card);
      initialiseCard(card);
    });

    sourceImage.insertAdjacentElement("afterend", panel);
  }

  function initialise() {
    var sourceImage = document.querySelector(".source-facsimile-page");
    var section = document.querySelector(".source-semantic-copy");
    if (!sourceImage || !section) return;
    createPracticePanel(sourceImage, section, collectTasks(section));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialise, { once: true });
  } else {
    initialise();
  }
})();
