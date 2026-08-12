(function () {
  "use strict";

  var STORE_PREFIX = "kuandika-inline-practice-v2:";
  var instructionPattern = /\b(Chora|Fuatisha|Andika|Nakili|Jaza|Tunga|Panga|Unganisha)\b/i;

  function cleanText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

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
      // Drawing still works when browser storage is unavailable.
    }
  }

  function removeStored(id) {
    try {
      window.localStorage.removeItem(storageKey(id));
    } catch (_error) {
      // The visible canvas can still be cleared.
    }
  }

  function kindForPrompt(prompt) {
    if (/\bFuatisha\b/i.test(prompt)) return "tracing";
    if (/\b(Andika|Nakili|Jaza|Tunga|Panga|Unganisha)\b/i.test(prompt)) return "writing";
    return "drawing";
  }

  function ensureId(element, fallback) {
    if (!element.id) element.id = fallback;
    return element.id;
  }

  function canvasPoint(canvas, event) {
    var rect = canvas.getBoundingClientRect();
    return {
      x: (event.clientX - rect.left) * (canvas.width / rect.width),
      y: (event.clientY - rect.top) * (canvas.height / rect.height),
    };
  }

  function initialiseTools(tools) {
    var canvas = tools.querySelector("canvas");
    var clear = tools.querySelector(".inline-practice-clear");
    var response = tools.querySelector(".inline-practice-status");
    var alternative = tools.querySelector(".inline-practice-alternative");
    var context = canvas.getContext("2d");
    var drawing = false;
    var strokeMade = false;
    var id = canvas.id;

    context.lineCap = "round";
    context.lineJoin = "round";
    context.lineWidth = 6;
    context.strokeStyle = "#172033";

    function updateStatus() {
      var complete = canvas.dataset.hasDrawing === "true" || alternative.value.trim() !== "";
      response.value = complete ? "Jibu limekamilika" : "";
      response.classList.toggle("is-complete", complete);
    }

    var storedDrawing = readStored(id + ":drawing");
    var storedText = readStored(id + ":text");
    canvas.dataset.hasDrawing = storedDrawing ? "true" : "false";
    if (storedDrawing) {
      var storedImage = new Image();
      storedImage.addEventListener("load", function () {
        context.drawImage(storedImage, 0, 0, canvas.width, canvas.height);
      });
      storedImage.src = storedDrawing;
    }
    if (storedText !== null) alternative.value = storedText;
    updateStatus();

    canvas.addEventListener("pointerdown", function (event) {
      event.preventDefault();
      event.stopPropagation();
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
      event.stopPropagation();
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

    clear.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      context.clearRect(0, 0, canvas.width, canvas.height);
      canvas.dataset.hasDrawing = "false";
      removeStored(id + ":drawing");
      updateStatus();
      canvas.focus();
    });

    alternative.addEventListener("click", function (event) {
      event.stopPropagation();
    });
    alternative.addEventListener("input", function () {
      writeStored(id + ":text", alternative.value);
      updateStatus();
    });
  }

  function createTools(section, options) {
    var id = options.id;
    var label = cleanText(options.label) || "Zoezi la kuchora na kuandika.";
    var labelId = options.labelledBy || id + "-prompt";
    var tools = document.createElement("div");
    tools.className = "inline-practice-tools";
    tools.dataset.practiceKind = options.kind || "drawing";
    tools.dataset.inlinePractice = id;
    tools.setAttribute("role", "group");
    tools.setAttribute("aria-labelledby", labelId);

    if (!options.labelledBy) {
      var prompt = document.createElement("p");
      prompt.className = "inline-practice-prompt";
      prompt.id = labelId;
      prompt.textContent = label;
      tools.appendChild(prompt);
    }

    var canvasWrap = document.createElement("div");
    canvasWrap.className = "inline-practice-canvas-wrap";
    var canvas = document.createElement("canvas");
    canvas.className = "inline-practice-canvas";
    canvas.id = id;
    canvas.width = 720;
    canvas.height = options.kind === "drawing" ? 420 : 300;
    canvas.tabIndex = 0;
    canvas.setAttribute("role", "img");
    canvas.setAttribute("aria-labelledby", labelId);
    canvas.dataset.practiceStorage = id;
    canvas.dataset.hasDrawing = "false";
    canvasWrap.appendChild(canvas);
    tools.appendChild(canvasWrap);

    var actions = document.createElement("div");
    actions.className = "inline-practice-actions";
    var clear = document.createElement("button");
    clear.className = "inline-practice-clear";
    clear.type = "button";
    clear.textContent = "Futa mchoro";
    actions.appendChild(clear);

    var responseLabel = document.createElement("label");
    responseLabel.className = "inline-practice-status-label";
    responseLabel.htmlFor = id + "-response";
    responseLabel.textContent = "Hali ya jibu";
    actions.appendChild(responseLabel);
    var response = document.createElement("input");
    response.className = "inline-practice-status";
    response.id = id + "-response";
    response.type = "text";
    response.readOnly = true;
    response.placeholder = "Chora, andika au tumia breli";
    response.setAttribute("aria-label", "Hali ya jibu kwa " + label);
    actions.appendChild(response);
    tools.appendChild(actions);

    var alternativeLabel = document.createElement("label");
    alternativeLabel.className = "inline-practice-alternative-label";
    alternativeLabel.htmlFor = id + "-alternative";
    alternativeLabel.textContent = "Jibu kwa kuandika au kutumia breli";
    tools.appendChild(alternativeLabel);
    var alternative = document.createElement("input");
    alternative.className = "inline-practice-alternative";
    alternative.id = id + "-alternative";
    alternative.type = "search";
    alternative.autocomplete = "off";
    alternative.spellcheck = false;
    alternative.setAttribute("aria-describedby", labelId);
    alternative.dataset.practiceStorage = id + "-alternative";
    tools.appendChild(alternative);

    section.classList.add("has-integrated-practice");
    if (options.kind === "drawing" || options.kind === "tracing") {
      section.classList.add("has-integrated-drawing");
    }
    initialiseTools(tools);
    return tools;
  }

  function addImageTools(section, image, options) {
    if (!image || image.dataset.inlinePracticeAdded === "true") return null;
    image.dataset.inlinePracticeAdded = "true";
    var tools = createTools(section, options);
    var option = image.closest("label.activity-option");
    if (option && option.parentElement) {
      var card = document.createElement("div");
      card.className = "integrated-object-card";
      option.parentElement.insertBefore(card, option);
      card.appendChild(option);
      card.appendChild(tools);
    } else {
      image.insertAdjacentElement("afterend", tools);
    }
    return tools;
  }

  function addPageSeven(section) {
    var prompt = section.querySelector('[data-id="pg007_n0008"]');
    var promptText = cleanText(prompt && prompt.textContent) || "Chora michoro hii:";
    if (prompt) prompt.dataset.inlinePromptProcessed = "true";

    var horizontal = section.querySelector('[data-id="pg007_n0009"]');
    if (horizontal) {
      horizontal.textContent = "— — — — — —";
      horizontal.parentElement.classList.add("practice-pattern-sample");
      horizontal.parentElement.insertAdjacentElement("afterend", createTools(section, {
        id: "pg007-inline-horizontal",
        label: promptText + " mistari ya mlalo.",
        kind: "drawing",
      }));
    }

    var vertical = section.querySelector('[data-id="pg007_n0010"]');
    if (vertical) {
      vertical.parentElement.classList.add("practice-pattern-sample");
      vertical.parentElement.insertAdjacentElement("afterend", createTools(section, {
        id: "pg007-inline-vertical",
        label: promptText + " mistari ya wima.",
        kind: "drawing",
      }));
    }

    section.querySelectorAll("img[data-id]").forEach(function (image, index) {
      addImageTools(section, image, {
        id: "pg007-inline-pattern-" + String(index + 1).padStart(2, "0"),
        label: "Chora mchoro wa " + (index + 3) + ": " + cleanText(image.alt),
        kind: "drawing",
      });
    });
  }

  function addImageLesson(section, pageId, promptId, kind) {
    var prompt = section.querySelector('[data-id="' + promptId + '"]');
    var promptText = cleanText(prompt && prompt.textContent);
    if (prompt) prompt.dataset.inlinePromptProcessed = "true";
    var images = Array.from(section.querySelectorAll("img[data-id]"));
    if (images.length) {
      var outerGrid = images[0].closest(".grid");
      var ancestorGrid = outerGrid && outerGrid.parentElement && outerGrid.parentElement.closest(".grid");
      while (ancestorGrid && section.contains(ancestorGrid)) {
        outerGrid = ancestorGrid;
        ancestorGrid = outerGrid.parentElement && outerGrid.parentElement.closest(".grid");
      }
      if (outerGrid) outerGrid.classList.add("integrated-drawing-grid");
    }
    images.forEach(function (image, index) {
      var name = cleanText(image.alt).replace(/[.]$/, "");
      addImageTools(section, image, {
        id: pageId + "-inline-image-" + String(index + 1).padStart(2, "0"),
        label: promptText + " " + (index + 1) + ": " + name + ".",
        kind: kind,
      });
    });
  }

  function addPageTen(section) {
    var tracePrompt = section.querySelector('[data-id="pg010_n0005"]');
    var drawPrompt = section.querySelector('[data-id="pg010_n0006"]');
    if (tracePrompt) tracePrompt.dataset.inlinePromptProcessed = "true";
    if (drawPrompt) drawPrompt.dataset.inlinePromptProcessed = "true";

    var image = section.querySelector('[data-id="pg010_im001"]');
    if (image) {
      var holder = image.parentElement;
      var list = document.createElement("div");
      list.className = "pattern-slice-list";
      for (var index = 0; index < 5; index += 1) {
        var card = document.createElement("section");
        card.className = "pattern-slice-card";
        var figure = document.createElement("div");
        figure.className = "pattern-slice-figure";
        var slice = image.cloneNode(false);
        slice.removeAttribute("data-id");
        slice.alt = "";
        slice.setAttribute("aria-hidden", "true");
        slice.style.transform = "translateY(-" + (index * 20) + "%)";
        figure.appendChild(slice);
        card.appendChild(figure);
        card.appendChild(createTools(section, {
          id: "pg010-inline-trace-" + String(index + 1).padStart(2, "0"),
          label: "Fuatisha mchoro wa " + (index + 1) + ".",
          kind: "tracing",
        }));
        list.appendChild(card);
      }
      holder.hidden = true;
      holder.insertAdjacentElement("afterend", list);
    }

    var repeatedIds = ["pg010_n0008", "pg010_n0009", "pg010_n0010", "pg010_n0011", "pg010_n0012", "pg010_n0013", "pg010_n0014"];
    repeatedIds.forEach(function (textId, index) {
      var sample = section.querySelector('[data-id="' + textId + '"]');
      if (!sample) return;
      sample.dataset.sequencePracticeAdded = "true";
      sample.parentElement.insertAdjacentElement("afterend", createTools(section, {
        id: "pg010-inline-draw-" + String(index + 6).padStart(2, "0"),
        label: "Chora mchoro wa " + (index + 6) + ".",
        kind: "drawing",
      }));
    });
  }

  function isRepeatedSequence(text) {
    var compact = cleanText(text).replace(/\s+/g, "");
    if (compact.length < 5 || compact.length > 100) return false;
    var unique = new Set(compact.toLowerCase().split(""));
    return unique.size === 1 && /[a-z0-9]/i.test(compact.charAt(0));
  }

  function addSequenceTools(section, pageId) {
    var count = 0;
    section.querySelectorAll("[data-id]").forEach(function (element) {
      if (element.dataset.sequencePracticeAdded === "true") return;
      var text = cleanText(element.textContent);
      if (!isRepeatedSequence(text)) return;
      if (element.closest(".inline-practice-tools")) return;
      element.dataset.sequencePracticeAdded = "true";
      count += 1;
      var character = text.replace(/\s+/g, "").charAt(0);
      var host = element.parentElement;
      host.insertAdjacentElement("afterend", createTools(section, {
        id: pageId + "-inline-sequence-" + String(count).padStart(2, "0"),
        label: "Fuatisha au andika " + character + ".",
        kind: "tracing",
      }));
    });
  }

  function isBetween(node, start, end) {
    var afterStart = Boolean(start.compareDocumentPosition(node) & Node.DOCUMENT_POSITION_FOLLOWING);
    var beforeEnd = !end || Boolean(node.compareDocumentPosition(end) & Node.DOCUMENT_POSITION_FOLLOWING);
    return afterStart && beforeEnd;
  }

  function insertBeforeNextPrompt(section, prompt, nextPrompt, tools) {
    if (nextPrompt) {
      var ancestors = [];
      var current = prompt;
      while (current && current !== section) {
        ancestors.push(current);
        current = current.parentElement;
      }
      ancestors.push(section);
      var nextAncestors = [];
      current = nextPrompt;
      while (current && current !== section) {
        nextAncestors.push(current);
        current = current.parentElement;
      }
      nextAncestors.push(section);
      var common = ancestors.find(function (node) { return nextAncestors.indexOf(node) !== -1; }) || section;
      var branch = nextPrompt;
      while (branch.parentElement && branch.parentElement !== common) branch = branch.parentElement;
      common.insertBefore(tools, branch);
      return;
    }

    var topBranch = prompt;
    while (topBranch.parentElement && topBranch.parentElement !== section) topBranch = topBranch.parentElement;
    if (topBranch.nextElementSibling) section.insertBefore(tools, topBranch.nextElementSibling);
    else section.appendChild(tools);
  }

  function addInstructionTools(section, pageId) {
    var prompts = Array.from(section.querySelectorAll("[data-id]")).filter(function (element) {
      var text = cleanText(element.textContent);
      return !element.closest(".inline-practice-tools") &&
        element.dataset.inlinePromptProcessed !== "true" &&
        text.length > 2 && text.length <= 180 && instructionPattern.test(text);
    });

    prompts.forEach(function (prompt, index) {
      var nextPrompt = prompts[index + 1] || null;
      var promptText = cleanText(prompt.textContent);
      var segmentControls = Array.from(section.querySelectorAll('input[type="text"][data-activity-item], input[type="search"][data-activity-item], textarea[data-activity-item]')).filter(function (control) {
        return isBetween(control, prompt, nextPrompt);
      });
      if (segmentControls.length) return;

      var segmentTools = Array.from(section.querySelectorAll(".inline-practice-tools")).filter(function (tools) {
        return isBetween(tools, prompt, nextPrompt);
      });
      if (segmentTools.length) return;

      var segmentImages = Array.from(section.querySelectorAll("img[data-id]")).filter(function (image) {
        return isBetween(image, prompt, nextPrompt) && image.dataset.inlinePracticeAdded !== "true";
      });
      if (segmentImages.length > 1 || (segmentImages.length === 1 && /\b(Chora|Fuatisha)\b.*\b(picha|mchoro|michoro)\b/i.test(promptText))) {
        segmentImages.forEach(function (image, imageIndex) {
          addImageTools(section, image, {
            id: pageId + "-inline-prompt-" + String(index + 1).padStart(2, "0") + "-image-" + String(imageIndex + 1).padStart(2, "0"),
            label: promptText + " " + cleanText(image.alt),
            kind: kindForPrompt(promptText),
          });
        });
        return;
      }

      var promptId = ensureId(prompt, pageId + "-inline-prompt-label-" + String(index + 1).padStart(2, "0"));
      var tools = createTools(section, {
        id: pageId + "-inline-prompt-" + String(index + 1).padStart(2, "0"),
        label: promptText,
        labelledBy: promptId,
        kind: kindForPrompt(promptText),
      });
      insertBeforeNextPrompt(section, prompt, nextPrompt, tools);
    });
  }

  function initialise() {
    var section = document.querySelector(".source-semantic-copy");
    if (!section || section.dataset.integratedPracticeReady === "true") return;
    section.dataset.integratedPracticeReady = "true";
    var pageId = section.getAttribute("data-section-id") || "page";

    if (pageId === "pg007_sec001") addPageSeven(section);
    if (pageId === "pg008_sec001") addImageLesson(section, "pg008", "pg008_n0005", "tracing");
    if (pageId === "pg009_sec001") addImageLesson(section, "pg009", "pg009_n0002", "drawing");
    if (pageId === "pg010_sec001") addPageTen(section);

    addSequenceTools(section, pageId);
    addInstructionTools(section, pageId);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialise, { once: true });
  } else {
    initialise();
  }
})();
