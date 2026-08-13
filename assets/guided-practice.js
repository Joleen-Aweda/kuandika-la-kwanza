(function () {
  "use strict";

  var SVG_NS = "http://www.w3.org/2000/svg";
  var STORE_PREFIX = "kuandika-guided-practice-v1:";
  var SOURCE_CONTENT_TOP = 110;
  var SOURCE_CONTENT_BOTTOM = 1150;
  var instructionPattern = /\b(Chora|Fuatisha|Andika|Nakili|Jaza|Tunga|Panga|Unganisha|Kamilisha|Oanisha|Taja)\b/i;

  function cleanText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function slug(value) {
    return cleanText(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  }

  function storageKey(pageId, cardId, suffix) {
    return STORE_PREFIX + pageId + ":" + cardId + ":" + suffix;
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
      // The exercise remains usable if storage is unavailable.
    }
  }

  function removeStored(key) {
    try {
      localStorage.removeItem(key);
    } catch (_error) {
      // The visible response can still be cleared.
    }
  }

  function isBetween(node, start, end) {
    var afterStart = Boolean(start.compareDocumentPosition(node) & Node.DOCUMENT_POSITION_FOLLOWING);
    var beforeEnd = !end || Boolean(node.compareDocumentPosition(end) & Node.DOCUMENT_POSITION_FOLLOWING);
    return afterStart && beforeEnd;
  }

  function isRepeatedSequence(value) {
    var compact = cleanText(value).replace(/\s+/g, "");
    if (compact.length < 5 || compact.length > 120) return false;
    var unique = new Set(compact.toLowerCase().split(""));
    return unique.size === 1 && /[a-z0-9|\-]/i.test(compact.charAt(0));
  }

  function promptKind(prompt) {
    if (/\b(Fuatisha|Unganisha|Oanisha)\b/i.test(prompt)) return "tracing";
    if (/\bChora\b/i.test(prompt)) return "drawing";
    return "writing";
  }

  function shortTargetFromPrompt(prompt) {
    var match = prompt.match(/\bherufi\s+ya\s+(?:irabu|konsonanti)\s+([a-z]{1,4})\b/i);
    if (match) return match[1];
    match = prompt.match(/\bherufi\s+mwambatano\s+([a-z]{1,4})\b/i);
    if (match) return match[1];
    match = prompt.match(/\b(?:silabi|irabu|konsonanti)\s+([a-z]{1,4})(?:\b|[.])/i);
    if (match && !/^(za|ya|hii|hizi)$/i.test(match[1])) return match[1];
    match = prompt.match(/\bherufi\s+([a-z]{1,4})(?:\b|[.])/i);
    if (match && !/^(za|ya|hii|hizi|ndogo|kubwa)$/i.test(match[1])) return match[1];
    return "";
  }

  function targetFromControl(control) {
    var label = cleanText(control.getAttribute("aria-label"));
    var match = label.match(/\bherufi\s+([a-z]{1,4})\b/i);
    if (match && !/^(za|ya|hii|hizi)$/i.test(match[1])) return match[1];
    match = label.match(/\b(?:silabi|neno)\s+([a-z]{1,18})\b/i);
    return match ? match[1] : "";
  }

  function collectTargets(prompt, nodes, controls) {
    var targets = [];
    var fromPrompt = shortTargetFromPrompt(prompt);
    if (fromPrompt) targets.push(fromPrompt);

    controls.forEach(function (control) {
      var value = targetFromControl(control);
      if (value) targets.push(value);
    });

    if (/\b(herufi|irabu|konsonanti|silabi)\b/i.test(prompt)) {
      nodes.forEach(function (node) {
        var text = cleanText(node.textContent);
        if (/^[a-z]{1,4}$/i.test(text) && !/^(somo|hii|hizi|kwa)$/i.test(text)) targets.push(text);
      });
    }

    return Array.from(new Set(targets)).slice(0, 12);
  }

  function collectModelText(prompt, nodes) {
    if (!/\b(Nakili|Andika)\b/i.test(prompt) || !/\b(maneno|sentensi|majina)\b/i.test(prompt)) return "";
    var values = [];
    nodes.forEach(function (node) {
      var text = cleanText(node.textContent);
      if (!text || text === prompt || instructionPattern.test(text)) return;
      if (text.length >= 2 && text.length <= 90 && !/^\d+[.)]?$/i.test(text)) values.push(text);
    });
    return Array.from(new Set(values)).slice(0, 3).join("   ");
  }

  function modelBeforeControl(prompt, control, nodes) {
    var candidates = nodes.filter(function (node) {
      if (!isBetween(node, prompt, control)) return false;
      var text = cleanText(node.textContent);
      return text && text.length <= 120 && !instructionPattern.test(text) && !/^\d+[.)]?$/i.test(text);
    });
    return candidates.length ? cleanText(candidates[candidates.length - 1].textContent) : "";
  }

  function definitionsForControls(prompt, promptText, controls, nodes) {
    return controls.map(function (control, index) {
      var modelText = modelBeforeControl(prompt, control, nodes);
      var controlLabel = cleanText(control.getAttribute("aria-label"));
      var label = modelText
        ? promptText.replace(/:\s*$/, "") + ": " + modelText
        : (controlLabel || promptText) + " " + String(index + 1) + ".";
      return {
        kind: "writing",
        label: label,
        targets: [],
        modelText: modelText,
      };
    });
  }

  function repeatTargets(targets) {
    if (!targets.length) return "";
    if (targets.length > 1) return targets.join("   ");
    var target = targets[0];
    var count = target.length > 2 ? 5 : 6;
    return Array(count).fill(target).join("   ");
  }

  function makeSvg(name, attributes) {
    var element = document.createElementNS(SVG_NS, name);
    Object.keys(attributes).forEach(function (key) {
      element.setAttribute(key, attributes[key]);
    });
    return element;
  }

  function repeatedTargetTokens(targets) {
    if (!targets.length) return [];
    if (targets.length > 1) return targets.slice();
    var count = targets[0].length > 2 ? 5 : 6;
    return Array(count).fill(targets[0]);
  }

  function addHandwrittenLowercaseA(svg, centre, dotted) {
    var path = makeSvg("path", {
      d: "M " + String(centre - 14) + " 103 " +
        "C " + String(centre - 10) + " 103 " + String(centre - 8) + " 95 " + String(centre - 7) + " 88 " +
        "C " + String(centre - 7) + " 80 " + String(centre - 2) + " 75 " + String(centre + 5) + " 75 " +
        "C " + String(centre + 12) + " 75 " + String(centre + 15) + " 80 " + String(centre + 15) + " 88 " +
        "C " + String(centre + 15) + " 97 " + String(centre + 11) + " 103 " + String(centre + 5) + " 103 " +
        "C " + String(centre - 2) + " 103 " + String(centre - 7) + " 98 " + String(centre - 7) + " 88 " +
        "M " + String(centre + 14) + " 76 " +
        "C " + String(centre + 13) + " 85 " + String(centre + 13) + " 97 " + String(centre + 17) + " 103",
      fill: "none",
      stroke: dotted ? "#6b6b6b" : "#292524",
      "stroke-width": dotted ? "2.2" : "2.4",
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
    });
    if (dotted) path.setAttribute("stroke-dasharray", "1 5");
    svg.appendChild(path);
  }

  function addHandwritingTokens(svg, targets, dotted) {
    var tokens = repeatedTargetTokens(targets);
    if (!tokens.length) return;
    var margin = tokens.length > 6 ? 42 : 55;
    var step = tokens.length > 1 ? (900 - margin * 2) / (tokens.length - 1) : 0;
    var fontSize = tokens.length > 6 ? "44" : "54";

    tokens.forEach(function (token, index) {
      var centre = tokens.length === 1 ? 450 : margin + index * step;
      if (token === "a") {
        addHandwrittenLowercaseA(svg, centre, dotted);
        return;
      }
      var text = makeSvg("text", {
        x: String(centre),
        y: "103",
        "text-anchor": "middle",
        fill: dotted ? "none" : "#292524",
        stroke: dotted ? "#6b6b6b" : "none",
        "stroke-width": dotted ? "2.1" : "0",
        "stroke-dasharray": dotted ? "3 5" : "none",
        "stroke-linecap": "round",
        "font-family": "Sassoon Primary Source, sans-serif",
        "font-size": fontSize,
        "font-style": "normal",
        "font-weight": "400",
      });
      text.textContent = token;
      svg.appendChild(text);
    });
  }

  function addDottedTarget(template, targets) {
    var display = repeatTargets(targets);
    if (!display) return;
    var svg = makeSvg("svg", {
      viewBox: "0 0 900 180",
      preserveAspectRatio: "none",
      "aria-hidden": "true",
      focusable: "false",
    });
    addHandwritingTokens(svg, targets, true);
    template.appendChild(svg);
  }

  function addSolidTextModel(parent, display, compact, targets) {
    if (!display) return;
    var svg = makeSvg("svg", {
      viewBox: "0 0 900 180",
      preserveAspectRatio: "none",
      "aria-hidden": "true",
      focusable: "false",
      class: "guided-practice-model-svg",
    });
    if (!compact && targets && targets.length) {
      addHandwritingTokens(svg, targets, false);
      parent.appendChild(svg);
      return;
    }

    var text = makeSvg("text", {
      x: compact ? "32" : "450",
      y: "103",
      "text-anchor": compact ? "start" : "middle",
      fill: "#292524",
      "font-family": "Sassoon Primary Source, sans-serif",
      "font-size": compact ? "38" : "54",
      "font-style": "normal",
      "font-weight": "400",
    });
    var hasJoinedTarget = display.trim().split(/\s+/).some(function (part) {
      return part.length > 1;
    });
    if (!compact && display.length <= 36 && !hasJoinedTarget) {
      text.setAttribute("textLength", "820");
      text.setAttribute("lengthAdjust", "spacing");
    }
    text.textContent = display;
    svg.appendChild(text);
    parent.appendChild(svg);
  }

  function addDottedImageTemplate(template, source) {
    var output = document.createElement("canvas");
    output.className = "guided-practice-dotted-image";
    output.width = 900;
    output.height = 400;
    output.setAttribute("aria-hidden", "true");
    template.appendChild(output);

    var image = new Image();
    image.addEventListener("load", function () {
      var scratch = document.createElement("canvas");
      scratch.width = output.width;
      scratch.height = output.height;
      var scratchContext = scratch.getContext("2d", { willReadFrequently: true });
      scratchContext.fillStyle = "#fff";
      scratchContext.fillRect(0, 0, scratch.width, scratch.height);
      var scale = Math.min((scratch.width * .84) / image.naturalWidth, (scratch.height * .84) / image.naturalHeight);
      var width = image.naturalWidth * scale;
      var height = image.naturalHeight * scale;
      var left = (scratch.width - width) / 2;
      var top = (scratch.height - height) / 2;
      scratchContext.drawImage(image, left, top, width, height);
      var pixels = scratchContext.getImageData(0, 0, scratch.width, scratch.height).data;

      function darkness(x, y) {
        var offset = (y * scratch.width + x) * 4;
        var alpha = pixels[offset + 3] / 255;
        var luminance = .2126 * pixels[offset] + .7152 * pixels[offset + 1] + .0722 * pixels[offset + 2];
        return (255 - luminance) * alpha;
      }

      var context = output.getContext("2d");
      context.fillStyle = "#5b6268";
      for (var y = 5; y < scratch.height - 5; y += 6) {
        for (var x = 5; x < scratch.width - 5; x += 6) {
          var horizontal = Math.abs(darkness(x + 3, y) - darkness(x - 3, y));
          var vertical = Math.abs(darkness(x, y + 3) - darkness(x, y - 3));
          var centre = darkness(x, y);
          if (horizontal + vertical > 72 || centre > 155) {
            context.beginPath();
            context.arc(x, y, 1.65, 0, Math.PI * 2);
            context.fill();
          }
        }
      }
    }, { once: true });
    image.src = source;
  }

  function addImage(parent, source, alt) {
    var image = document.createElement("img");
    image.src = source;
    image.alt = alt || "";
    if (!alt) image.setAttribute("aria-hidden", "true");
    parent.appendChild(image);
  }

  function canvasPoint(canvas, event) {
    var bounds = canvas.getBoundingClientRect();
    return {
      x: (event.clientX - bounds.left) * canvas.width / bounds.width,
      y: (event.clientY - bounds.top) * canvas.height / bounds.height,
    };
  }

  function createButton(label) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "guided-practice-button";
    button.textContent = label;
    return button;
  }

  function initialiseCanvas(card, pageId, cardId) {
    var canvas = card.querySelector("canvas");
    var pen = card.querySelector('[data-action="pen"]');
    var eraser = card.querySelector('[data-action="eraser"]');
    var undo = card.querySelector('[data-action="undo"]');
    var clear = card.querySelector('[data-action="clear"]');
    var status = card.querySelector(".guided-practice-status");
    var alternative = card.querySelector("textarea");
    var context = canvas.getContext("2d");
    var drawing = false;
    var erasing = false;
    var changed = false;
    var history = [];
    var drawingKey = storageKey(pageId, cardId, "drawing");
    var textKey = storageKey(pageId, cardId, "text");

    context.lineCap = "round";
    context.lineJoin = "round";

    function restore(dataUrl) {
      context.clearRect(0, 0, canvas.width, canvas.height);
      if (!dataUrl) return;
      var image = new Image();
      image.addEventListener("load", function () {
        context.drawImage(image, 0, 0, canvas.width, canvas.height);
      }, { once: true });
      image.src = dataUrl;
    }

    function remember() {
      history.push(canvas.toDataURL("image/png"));
      if (history.length > 20) history.shift();
    }

    var stored = readStored(drawingKey);
    if (stored) restore(stored);
    alternative.value = readStored(textKey) || "";

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
      remember();
      drawing = true;
      changed = false;
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
      context.strokeStyle = "#172033";
      context.lineWidth = erasing ? 28 : 5;
      context.lineTo(point.x, point.y);
      context.stroke();
      changed = true;
    });

    function finish(event) {
      if (!drawing) return;
      drawing = false;
      if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
      context.globalCompositeOperation = "source-over";
      if (changed) {
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
      status.textContent = "Jibu la sehemu hii limefutwa.";
      canvas.focus();
    });

    alternative.addEventListener("input", function () {
      writeStored(textKey, alternative.value);
    });
  }

  function addModel(card, definition) {
    if (definition.modelImage) {
      var imageModel = document.createElement("div");
      imageModel.className = "guided-practice-model guided-practice-model-image";
      addImage(imageModel, definition.modelImage.src, definition.modelImage.alt);
      card.appendChild(imageModel);
      return;
    }

    var display = definition.modelText || repeatTargets(definition.targets || []);
    if (!display || definition.kind === "tracing") return;
    var model = document.createElement("div");
    model.className = "guided-practice-model is-lined";
    addSolidTextModel(
      model,
      display,
      Boolean(definition.modelText || display.length > 45),
      definition.targets || []
    );
    card.appendChild(model);
  }

  function createCard(pageId, definition, index) {
    var cardId = definition.id || pageId + "-guided-" + String(index + 1).padStart(3, "0");
    var card = document.createElement("section");
    card.className = "guided-practice-card";
    card.dataset.practiceKind = definition.kind;
    card.dataset.hasTarget = String(Boolean((definition.targets || []).length));
    card.dataset.hasImage = String(Boolean(definition.modelImage || definition.traceImage));
    card.dataset.guidedPractice = cardId;

    var prompt = document.createElement("h3");
    prompt.className = "guided-practice-prompt";
    prompt.id = cardId + "-prompt";
    var number = document.createElement("span");
    number.className = "guided-practice-index";
    number.textContent = String(index + 1);
    number.setAttribute("aria-hidden", "true");
    prompt.appendChild(number);
    prompt.appendChild(document.createTextNode(definition.label));
    card.appendChild(prompt);

    var board = document.createElement("div");
    board.className = "guided-practice-board";
    var largeBoard = Boolean(definition.traceImage) ||
      (definition.kind === "drawing" && !(definition.targets || []).length);
    board.classList.add(largeBoard ? "is-large-board" : "is-writing-board");
    if (!largeBoard) board.classList.add("is-lined");

    var template = document.createElement("div");
    template.className = "guided-practice-template";
    if (definition.traceImage) {
      addDottedImageTemplate(template, definition.traceImage.src);
    } else if (definition.kind === "tracing") {
      addDottedTarget(template, definition.targets || []);
    }
    board.appendChild(template);

    var canvas = document.createElement("canvas");
    canvas.className = "guided-practice-canvas";
    canvas.id = cardId + "-canvas";
    canvas.width = 900;
    canvas.height = largeBoard ? 400 : 180;
    canvas.tabIndex = 0;
    canvas.setAttribute("role", "img");
    canvas.setAttribute("aria-labelledby", prompt.id);
    board.appendChild(canvas);
    card.appendChild(board);

    var actions = document.createElement("div");
    actions.className = "guided-practice-actions";
    var pen = createButton("Kalamu");
    pen.dataset.action = "pen";
    pen.setAttribute("aria-pressed", "true");
    actions.appendChild(pen);
    var eraser = createButton("Kifutio");
    eraser.dataset.action = "eraser";
    eraser.setAttribute("aria-pressed", "false");
    actions.appendChild(eraser);
    var undo = createButton("Tendua");
    undo.dataset.action = "undo";
    actions.appendChild(undo);
    var clear = createButton("Futa jibu");
    clear.dataset.action = "clear";
    actions.appendChild(clear);
    var status = document.createElement("span");
    status.className = "guided-practice-status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.textContent = definition.kind === "tracing"
      ? "Unganisha nukta au fuatisha mfano kwa kalamu."
      : "Andika au chora ndani ya sehemu ya jibu.";
    actions.appendChild(status);
    card.appendChild(actions);

    var alternative = document.createElement("details");
    alternative.className = "guided-practice-alternative";
    var summary = document.createElement("summary");
    summary.textContent = "Jibu mbadala kwa kibodi au breli";
    alternative.appendChild(summary);
    var textarea = document.createElement("textarea");
    textarea.setAttribute("aria-label", "Jibu mbadala: " + definition.label);
    alternative.appendChild(textarea);
    card.appendChild(alternative);

    initialiseCanvas(card, pageId, cardId);
    return card;
  }

  function imageDefinition(promptText, image, kind, index) {
    var alt = cleanText(image.alt).replace(/[.]$/, "");
    var label = promptText;
    if (alt) label += " " + alt + ".";
    var definition = {
      kind: kind,
      label: label,
      targets: [],
    };
    if (kind === "tracing") {
      definition.traceImage = { src: image.src, alt: alt };
    } else {
      definition.modelImage = { src: image.src, alt: alt };
      if (kind === "drawing") definition.traceImage = { src: image.src, alt: alt };
    }
    return definition;
  }

  function definitionsForPrompt(prompt, nextPrompt, section, pageId) {
    var promptText = cleanText(prompt.textContent);
    var kind = promptKind(promptText);
    var allTextNodes = Array.from(section.querySelectorAll("[data-id]")).filter(function (node) {
      return node !== prompt && node.tagName !== "IMG" && isBetween(node, prompt, nextPrompt);
    });
    var controls = Array.from(section.querySelectorAll("input[data-activity-item], textarea[data-activity-item]")).filter(function (node) {
      var type = String(node.getAttribute("type") || "text").toLowerCase();
      return type !== "checkbox" && type !== "radio" && isBetween(node, prompt, nextPrompt);
    });
    var images = Array.from(section.querySelectorAll("img[data-id]")).filter(function (node) {
      return isBetween(node, prompt, nextPrompt);
    });
    var sequences = allTextNodes.map(function (node) { return cleanText(node.textContent); }).filter(isRepeatedSequence);
    var targets = collectTargets(promptText, allTextNodes, controls);
    var modelText = collectModelText(promptText, allTextNodes);
    var definitions = [];

    if (pageId === "pg007_sec001") {
      definitions.push({ kind: "drawing", label: promptText + " Mistari ya mlalo.", targets: ["-"] });
      definitions.push({ kind: "drawing", label: promptText + " Mistari ya wima.", targets: ["|"] });
      images.forEach(function (image, index) {
        definitions.push(imageDefinition(promptText, image, "drawing", index + 2));
      });
      return definitions;
    }

    if (sequences.length) {
      sequences.forEach(function (sequence, index) {
        var character = sequence.replace(/\s+/g, "").charAt(0);
        definitions.push({
          kind: kind === "tracing" ? "tracing" : "writing",
          label: promptText + " Mfano wa " + character + ".",
          targets: [character],
          id: pageId + "-sequence-" + String(index + 1).padStart(2, "0"),
        });
      });
      return definitions;
    }

    if (images.length && /\b(picha|mchoro|michoro|nukta|alama|umbo|maumbo)\b/i.test(promptText)) {
      images.forEach(function (image, index) {
        definitions.push(imageDefinition(promptText, image, kind, index));
      });
      return definitions;
    }

    if (images.length && /\bherufi\b/i.test(promptText) && targets.length) {
      definitions.push({
        kind: kind,
        label: promptText,
        targets: targets,
        modelImage: { src: images[0].src, alt: cleanText(images[0].alt) },
      });
      return definitions;
    }

    if (images.length && /\b(Andika|Nakili|Taja)\b/i.test(promptText)) {
      images.forEach(function (image, index) {
        definitions.push(imageDefinition(promptText, image, "writing", index));
      });
      return definitions;
    }

    if (controls.length > 1 &&
        /\b(sentensi|majina|maneno|nafasi|majibu|alama)\b/i.test(promptText) &&
        !/\bherufi\s+za\b/i.test(promptText)) {
      return definitionsForControls(prompt, promptText, controls, allTextNodes);
    }

    definitions.push({
      kind: kind,
      label: promptText,
      targets: targets,
      modelText: modelText,
    });
    return definitions;
  }

  function collectPromptGroups(section, pageId) {
    var prompts = Array.from(section.querySelectorAll("[data-id]")).filter(function (node) {
      var text = cleanText(node.textContent);
      return node.tagName !== "IMG" && text.length > 2 && text.length <= 220 && instructionPattern.test(text);
    });
    return prompts.map(function (prompt, index) {
      var nextPrompt = prompts[index + 1] || null;
      return {
        prompt: prompt,
        text: cleanText(prompt.textContent),
        definitions: definitionsForPrompt(prompt, nextPrompt, section, pageId),
      };
    });
  }

  function syntheticDefinition(text) {
    var target = shortTargetFromPrompt(text);
    return {
      kind: promptKind(text),
      label: text,
      targets: target ? [target] : [],
      modelText: "",
    };
  }

  function createSourceBand(source, start, end) {
    var safeStart = Math.max(0, Math.min(1279, Math.round(start)));
    var safeEnd = Math.max(safeStart + 1, Math.min(1280, Math.round(end)));
    var band = document.createElement("div");
    band.className = "guided-source-band";
    band.style.aspectRatio = "930 / " + String(safeEnd - safeStart);
    var svg = makeSvg("svg", {
      viewBox: "0 " + String(safeStart) + " 930 " + String(safeEnd - safeStart),
      preserveAspectRatio: "xMidYMid meet",
      "aria-hidden": "true",
      focusable: "false",
    });
    var image = makeSvg("image", {
      href: source,
      x: "0",
      y: "0",
      width: "930",
      height: "1280",
      preserveAspectRatio: "none",
    });
    svg.appendChild(image);
    band.appendChild(svg);
    return band;
  }

  function createCluster(pageId, entry, definitions, groupIndex) {
    var cluster = document.createElement("section");
    cluster.className = "guided-practice-cluster";
    cluster.setAttribute("aria-label", "Sehemu ya jibu: " + entry.text);
    var imageAnswers = definitions.every(function (definition) {
      return Boolean(definition.modelImage || definition.traceImage);
    });
    if (definitions.length > 1 && pageId !== "pg007_sec001" && imageAnswers) {
      cluster.classList.add("has-multiple-answers");
    }
    definitions.forEach(function (definition, definitionIndex) {
      if (!definition.id) {
        definition.id = pageId + "-guided-" + slug(definition.label).slice(0, 36) + "-" +
          String(groupIndex + 1).padStart(3, "0") + "-" + String(definitionIndex + 1).padStart(2, "0");
      }
      cluster.appendChild(createCard(
        pageId,
        definition,
        definitions.length > 1 ? definitionIndex : groupIndex
      ));
    });
    return cluster;
  }

  function interleavePractice(stage, image, pageId, layout, groups) {
    var flow = document.createElement("div");
    flow.className = "guided-source-flow";
    var previousEnd = SOURCE_CONTENT_TOP;

    layout.entries.forEach(function (entry, index) {
      var nextEntry = layout.entries[index + 1];
      var requestedEnd = nextEntry ? Number(nextEntry.start) : SOURCE_CONTENT_BOTTOM;
      var entryEnd = Number(entry.end) || previousEnd + 24;
      var sourceEnd = Math.min(
        SOURCE_CONTENT_BOTTOM,
        Math.max(previousEnd + 1, entryEnd, requestedEnd)
      );
      if (sourceEnd > previousEnd) {
        flow.appendChild(createSourceBand(image.src, previousEnd, sourceEnd));
      }

      var group = entry.domIndex === null ? null : groups[Number(entry.domIndex)];
      var definitions = group && group.definitions.length
        ? group.definitions
        : [syntheticDefinition(entry.text)];
      flow.appendChild(createCluster(pageId, entry, definitions, index));
      previousEnd = sourceEnd;
    });

    stage.classList.add("has-guided-practice");
    stage.appendChild(flow);
    var content = stage.closest("#content");
    if (content) content.classList.add("has-guided-practice");
  }

  async function loadLayout() {
    var response = await fetch("./content/guided-practice-layout.json");
    if (!response.ok) throw new Error("Imeshindikana kupakia mpangilio wa sehemu za majibu.");
    return response.json();
  }

  async function initialise() {
    var section = document.querySelector(".source-semantic-copy[data-section-id]");
    var stage = document.querySelector(".exact-page-stage");
    if (!section || !stage || section.dataset.guidedPracticeReady === "true") return;
    section.dataset.guidedPracticeReady = "true";

    var titleMeta = document.querySelector('meta[name="title-id"]');
    var pageId = cleanText(titleMeta && titleMeta.getAttribute("content")) ||
      section.getAttribute("data-section-id") || "page";
    var pageNumber = Number((pageId.match(/^pg(\d{3})_/) || [0, 0])[1]);
    if (pageNumber < 7 || pageNumber > 120) return;

    var image = stage.querySelector(".source-facsimile-page");
    var layouts = await loadLayout();
    var pageLayout = layouts[pageId];
    if (!image || !pageLayout || !pageLayout.entries || !pageLayout.entries.length) return;
    interleavePractice(stage, image, pageId, pageLayout, collectPromptGroups(section, pageId));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initialise().catch(function (error) { console.error(error); });
    }, { once: true });
  } else {
    initialise().catch(function (error) { console.error(error); });
  }
})();
