(function () {
  "use strict";

  var SVG_NS = "http://www.w3.org/2000/svg";
  var STORAGE_PREFIX = "kuandika-page-ink-v1:";
  var SOURCE_CONTENT_TOP = 110;
  var SOURCE_CONTENT_BOTTOM = 1150;
  var SOURCE_PAGE_HEIGHT = 1280;
  var SOURCE_PDF_HEIGHT = 767.669;

  function storageKey(pageId, suffix) {
    return STORAGE_PREFIX + pageId + ":" + suffix;
  }

  function readStored(key) {
    try {
      return localStorage.getItem(key);
    } catch (_error) {
      return null;
    }
  }

  function writeStored(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (_error) {
      // Drawing still works when local storage is unavailable.
    }
  }

  function removeStored(key) {
    try {
      localStorage.removeItem(key);
    } catch (_error) {
      // The visible canvas can still be cleared.
    }
  }

  function pageNumberFromId(pageId) {
    var match = String(pageId || "").match(/^pg(\d{3})_/);
    return match ? Number(match[1]) : 0;
  }

  function createSvgElement(name, attributes) {
    var element = document.createElementNS(SVG_NS, name);
    Object.keys(attributes).forEach(function (key) {
      element.setAttribute(key, attributes[key]);
    });
    return element;
  }

  function addTocNumberOverlay(stage, pageNumber) {
    var rows = pageNumber === 3 ? [
      ["5", 260, 294, "#ffffff"],
      ["6", 331, 365, "#ffffff"],
      ["7", 432, 467, "#b6e0c7"],
      ["11", 542, 577, "#b6e0c7"],
      ["17", 641, 676, "#b6e0c7"],
      ["27", 739, 774, "#b6e0c7"],
      ["37", 846, 881, "#b6e0c7"],
      ["47", 948, 983, "#b6e0c7"],
      ["55", 1048, 1083, "#b6e0c7"],
    ] : pageNumber === 4 ? [
      ["63", 172, 208, "#b6e0c7"],
      ["72", 282, 317, "#b6e0c7"],
      ["81", 391, 426, "#b6e0c7"],
      ["90", 500, 535, "#b6e0c7"],
      ["98", 650, 685, "#b6e0c7"],
      ["116", 782, 817, "#b6e0c7"],
    ] : [];
    if (!rows.length) return;

    var svg = createSvgElement("svg", {
      class: "toc-number-overlay",
      viewBox: "0 " + String(SOURCE_CONTENT_TOP) + " 930 " +
        String(SOURCE_CONTENT_BOTTOM - SOURCE_CONTENT_TOP),
      "aria-hidden": "true",
      focusable: "false",
    });
    rows.forEach(function (row) {
      svg.appendChild(createSvgElement("rect", {
        x: "755",
        y: String(row[1]),
        width: "58",
        height: "42",
        fill: row[3],
      }));
      var text = createSvgElement("text", {
        x: "802",
        y: String(row[2]),
        "text-anchor": "end",
        fill: "#231f20",
        "font-family": "Sassoon Primary Source, sans-serif",
        "font-size": "30",
        "font-weight": "400",
      });
      text.textContent = row[0];
      svg.appendChild(text);
    });
    stage.appendChild(svg);

    var targets = pageNumber === 3 ? [
      ["Shukurani, ukurasa wa 5", "pg005_sec001.html", 150, 184],
      ["Utangulizi, ukurasa wa 6", "pg006_sec001.html", 196, 230],
      ["Sura ya Kwanza, ukurasa wa 7", "pg007_sec001.html", 235, 286],
      ["Sura ya Pili, ukurasa wa 11", "pg011_sec001.html", 301, 351],
      ["Sura ya Tatu, ukurasa wa 17", "pg017_sec001.html", 360, 410],
      ["Sura ya Nne, ukurasa wa 27", "pg027_sec001.html", 419, 469],
      ["Sura ya Tano, ukurasa wa 37", "pg037_sec001.html", 483, 533],
      ["Sura ya Sita, ukurasa wa 47", "pg047_sec001.html", 544, 594],
      ["Sura ya Saba, ukurasa wa 55", "pg055_sec001.html", 604, 654],
    ] : [
      ["Sura ya Nane, ukurasa wa 63", "pg063_sec001.html", 79, 130],
      ["Sura ya Tisa, ukurasa wa 72", "pg072_sec001.html", 145, 196],
      ["Sura ya Kumi, ukurasa wa 81", "pg081_sec001.html", 210, 261],
      ["Sura ya Kumi na Moja, ukurasa wa 90", "pg090_sec001.html", 276, 327],
      ["Sura ya Kumi na Mbili, ukurasa wa 98", "pg098_sec001.html", 341, 417],
      ["Sura ya Kumi na Tatu, ukurasa wa 116", "pg116_sec001.html", 442, 496],
    ];
    var links = document.createElement("div");
    links.className = "toc-link-layer";
    targets.forEach(function (target) {
      var link = document.createElement("a");
      link.className = "toc-hotspot";
      link.href = target[1];
      link.setAttribute("aria-label", target[0]);
      var cropTopPoints = SOURCE_CONTENT_TOP / SOURCE_PAGE_HEIGHT * SOURCE_PDF_HEIGHT;
      var cropHeightPoints = (SOURCE_CONTENT_BOTTOM - SOURCE_CONTENT_TOP) /
        SOURCE_PAGE_HEIGHT * SOURCE_PDF_HEIGHT;
      link.style.top = ((target[2] - cropTopPoints) / cropHeightPoints * 100) + "%";
      link.style.height = ((target[3] - target[2]) / cropHeightPoints * 100) + "%";
      links.appendChild(link);
    });
    stage.appendChild(links);
  }

  function canvasPoint(canvas, event) {
    var bounds = canvas.getBoundingClientRect();
    return {
      x: (event.clientX - bounds.left) * canvas.width / bounds.width,
      y: (event.clientY - bounds.top) * canvas.height / bounds.height,
    };
  }

  function createButton(label, className) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "page-ink-button" + (className ? " " + className : "");
    button.textContent = label;
    return button;
  }

  function addInkLayer(content, stage, pageId) {
    var canvas = document.createElement("canvas");
    canvas.className = "page-ink-canvas";
    canvas.id = pageId + "-ink-canvas";
    canvas.width = 930;
    canvas.height = 1280;
    canvas.tabIndex = 0;
    canvas.setAttribute("role", "img");
    canvas.setAttribute("aria-label", "Eneo la kuandika, kuchora na kuunganisha nukta moja kwa moja kwenye ukurasa");
    stage.appendChild(canvas);

    var toolbar = document.createElement("div");
    toolbar.className = "page-ink-toolbar";
    toolbar.setAttribute("role", "group");
    toolbar.setAttribute("aria-label", "Zana za kuandika kwenye ukurasa");
    toolbar.setAttribute("aria-controls", canvas.id);

    var toggle = createButton("Anza kuandika", "is-primary");
    toggle.setAttribute("aria-pressed", "false");
    toolbar.appendChild(toggle);

    var colour = document.createElement("input");
    colour.className = "page-ink-colour";
    colour.type = "color";
    colour.value = "#172033";
    colour.setAttribute("aria-label", "Chagua rangi ya kalamu");
    toolbar.appendChild(colour);

    var pen = createButton("Kalamu");
    pen.setAttribute("aria-pressed", "true");
    toolbar.appendChild(pen);

    var eraser = createButton("Kifutio");
    eraser.setAttribute("aria-pressed", "false");
    toolbar.appendChild(eraser);

    var undo = createButton("Tendua");
    toolbar.appendChild(undo);

    var clear = createButton("Futa yote");
    toolbar.appendChild(clear);

    var status = document.createElement("span");
    status.className = "page-ink-status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.textContent = "Bonyeza Anza kuandika, kisha andika juu ya mistari au unganisha nukta.";
    toolbar.appendChild(status);

    var alternative = document.createElement("details");
    alternative.className = "page-ink-alternative";
    var summary = document.createElement("summary");
    summary.textContent = "Jibu mbadala kwa kibodi au breli";
    alternative.appendChild(summary);
    var textarea = document.createElement("textarea");
    textarea.setAttribute("aria-label", "Jibu mbadala la ukurasa huu");
    textarea.value = readStored(storageKey(pageId, "text")) || "";
    alternative.appendChild(textarea);
    toolbar.appendChild(alternative);
    content.insertBefore(toolbar, stage);

    var context = canvas.getContext("2d");
    var drawing = false;
    var erasing = false;
    var strokeMade = false;
    var history = [];
    var drawingKey = storageKey(pageId, "drawing");

    context.lineCap = "round";
    context.lineJoin = "round";
    context.lineWidth = 5;

    function remember() {
      history.push(canvas.toDataURL("image/png"));
      if (history.length > 20) history.shift();
    }

    function restore(dataUrl) {
      context.clearRect(0, 0, canvas.width, canvas.height);
      if (!dataUrl) return;
      var image = new Image();
      image.addEventListener("load", function () {
        context.drawImage(image, 0, 0, canvas.width, canvas.height);
      }, { once: true });
      image.src = dataUrl;
    }

    var storedDrawing = readStored(drawingKey);
    if (storedDrawing) restore(storedDrawing);

    toggle.addEventListener("click", function () {
      var active = toggle.getAttribute("aria-pressed") !== "true";
      toggle.setAttribute("aria-pressed", String(active));
      toggle.textContent = active ? "Acha kuandika" : "Anza kuandika";
      stage.classList.toggle("is-ink-active", active);
      status.textContent = active
        ? "Kalamu imewashwa. Andika, chora au unganisha nukta moja kwa moja kwenye ukurasa."
        : "Uandishi umesitishwa. Ulichofanya kimehifadhiwa.";
      if (active) canvas.focus();
    });

    pen.addEventListener("click", function () {
      erasing = false;
      pen.setAttribute("aria-pressed", "true");
      eraser.setAttribute("aria-pressed", "false");
      status.textContent = "Kalamu imechaguliwa.";
    });

    eraser.addEventListener("click", function () {
      erasing = true;
      pen.setAttribute("aria-pressed", "false");
      eraser.setAttribute("aria-pressed", "true");
      status.textContent = "Kifutio kimechaguliwa.";
    });

    canvas.addEventListener("pointerdown", function (event) {
      event.preventDefault();
      drawing = true;
      strokeMade = false;
      remember();
      canvas.setPointerCapture(event.pointerId);
      var point = canvasPoint(canvas, event);
      context.beginPath();
      context.moveTo(point.x, point.y);
    });

    canvas.addEventListener("pointermove", function (event) {
      if (!drawing) return;
      event.preventDefault();
      var point = canvasPoint(canvas, event);
      context.globalCompositeOperation = erasing ? "destination-out" : "source-over";
      context.strokeStyle = colour.value;
      context.lineWidth = erasing ? 28 : 5;
      context.lineTo(point.x, point.y);
      context.stroke();
      strokeMade = true;
    });

    function finish(event) {
      if (!drawing) return;
      drawing = false;
      if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
      context.globalCompositeOperation = "source-over";
      if (strokeMade) {
        writeStored(drawingKey, canvas.toDataURL("image/png"));
        status.textContent = "Jibu limehifadhiwa kwenye kifaa hiki.";
      } else {
        history.pop();
      }
    }

    canvas.addEventListener("pointerup", finish);
    canvas.addEventListener("pointercancel", finish);

    undo.addEventListener("click", function () {
      var previous = history.pop() || "";
      restore(previous);
      if (previous) writeStored(drawingKey, previous);
      else removeStored(drawingKey);
      status.textContent = "Hatua ya mwisho imetenduliwa.";
    });

    clear.addEventListener("click", function () {
      remember();
      context.clearRect(0, 0, canvas.width, canvas.height);
      removeStored(drawingKey);
      status.textContent = "Uandishi wote wa ukurasa huu umefutwa.";
      canvas.focus();
    });

    textarea.addEventListener("input", function () {
      writeStored(storageKey(pageId, "text"), textarea.value);
    });
  }

  function initialise() {
    var image = document.querySelector(".source-facsimile-page");
    var section = document.querySelector("[data-section-id]");
    if (!image || !section || image.dataset.exactPageReady === "true") return;
    image.dataset.exactPageReady = "true";
    image.draggable = false;

    var pageId = section.getAttribute("data-section-id") || "page";
    var pageNumber = pageNumberFromId(pageId);
    var content = image.closest("#content") || image.parentElement;
    content.classList.add("exact-facsimile-content");

    var stage = document.createElement("div");
    stage.className = "exact-page-stage source-page-cropped";
    image.parentElement.insertBefore(stage, image);
    stage.appendChild(image);
    addTocNumberOverlay(stage, pageNumber);
    if (pageNumber >= 7 && pageNumber <= 120) addInkLayer(content, stage, pageId);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialise, { once: true });
  } else {
    initialise();
  }
})();
