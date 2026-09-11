(function () {
  "use strict";

  var VIDEO_SELECTOR = 'video[src*="/video/"]';
  var enhancedHandles = new WeakSet();
  var observedControls = new WeakSet();
  var scheduled = false;

  function viewportSize() {
    var viewport = window.visualViewport;
    var size = {
      left: viewport ? viewport.offsetLeft : 0,
      top: viewport ? viewport.offsetTop : 0,
      width: viewport ? viewport.width : window.innerWidth,
      height: viewport ? viewport.height : window.innerHeight
    };
    // Leave the dock and floating read-aloud controls unobstructed at every size.
    Array.prototype.forEach.call(document.querySelectorAll(
      '#nav-container > [role="group"], ' +
      '#interface-container [role="group"][aria-label="Vidhibiti vya kusoma kwa sauti"]'
    ), function (controls) {
      var rect = controls.getBoundingClientRect();
      if (rect.width && rect.height && rect.top > size.top) {
        size.height = Math.min(size.height, rect.top - size.top - 8);
      }
    });
    return size;
  }

  function clamp(value, minimum, maximum) {
    return Math.max(minimum, Math.min(value, maximum));
  }

  function movePlayer(player, x, y) {
    var size = viewportSize();
    var width = player.offsetWidth;
    var height = player.offsetHeight;
    var nextX = clamp(x, size.left, Math.max(size.left, size.left + size.width - width));
    var nextY = clamp(y, size.top, Math.max(size.top, size.top + size.height - height));
    player.style.left = nextX + "px";
    player.style.top = nextY + "px";
    player.style.right = "auto";
    player.style.bottom = "auto";
  }

  function keepPlayerOnScreen(player) {
    window.requestAnimationFrame(function () {
      if (!player.isConnected) return;
      var size = viewportSize();
      player.style.setProperty("--sign-language-available-height", size.height + "px");
      var rect = player.getBoundingClientRect();
      var fullyVisible = rect.left >= size.left && rect.top >= size.top &&
        rect.right <= size.left + size.width && rect.bottom <= size.top + size.height;
      if (!fullyVisible) movePlayer(player, rect.left, rect.top);
    });
  }

  function enhanceHandle(handle, player) {
    if (enhancedHandles.has(handle) || !player || !player.querySelector("video")) return;
    enhancedHandles.add(handle);
    handle.setAttribute("data-sign-language-drag-handle", "");
    player.setAttribute("data-sign-language-player", "");
    var drag = null;

    function start(clientX, clientY) {
      var rect = player.getBoundingClientRect();
      drag = { x: clientX - rect.left, y: clientY - rect.top };
      player.setAttribute("data-sign-language-dragging", "");
    }
    function move(clientX, clientY) {
      if (drag) movePlayer(player, clientX - drag.x, clientY - drag.y);
    }
    function finish() {
      drag = null;
      player.removeAttribute("data-sign-language-dragging");
    }

    handle.addEventListener("pointerdown", function (event) {
      if (event.pointerType === "mouse" && event.button !== 0) return;
      start(event.clientX, event.clientY);
      if (handle.setPointerCapture) handle.setPointerCapture(event.pointerId);
      event.preventDefault();
    });
    handle.addEventListener("pointermove", function (event) {
      if (!drag) return;
      move(event.clientX, event.clientY);
      event.preventDefault();
    });
    handle.addEventListener("pointerup", function (event) {
      if (!drag) return;
      move(event.clientX, event.clientY);
      finish();
      event.preventDefault();
    });
    handle.addEventListener("pointercancel", finish);
    var video = player.querySelector("video");
    if (video) video.addEventListener("loadedmetadata", function () { keepPlayerOnScreen(player); });
    keepPlayerOnScreen(player);
  }

  function revealAuthoredCoverControls() {
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-cover-hidden-sign-language]"),
      function (element) {
        element.removeAttribute("data-cover-hidden-sign-language");
      }
    );
  }

  function install() {
    scheduled = false;
    revealAuthoredCoverControls();
    Array.prototype.forEach.call(document.querySelectorAll(
      '#interface-container [role="group"][aria-label="Vidhibiti vya kusoma kwa sauti"]'
    ), function (controls) {
      var positioner = controls.parentElement;
      while (positioner && window.getComputedStyle(positioner).position !== "fixed") {
        positioner = positioner.parentElement;
      }
      if (positioner && !observedControls.has(positioner)) {
        observedControls.add(positioner);
        // Popovers calculate their anchored position after mounting.
        new MutationObserver(scheduleInstall).observe(positioner, {
          attributes: true, attributeFilter: ["style"]
        });
      }
    });
    Array.prototype.forEach.call(document.querySelectorAll(VIDEO_SELECTOR), function (video) {
      var player = video.parentElement;
      if (!player || window.getComputedStyle(player).position !== "fixed") return;
      var handle = Array.prototype.find.call(player.children, function (child) {
        return child.getAttribute && child.getAttribute("role") === "button";
      });
      if (handle) {
        enhanceHandle(handle, player);
        keepPlayerOnScreen(player);
      }
    });
  }
  function scheduleInstall() {
    if (scheduled) return;
    scheduled = true;
    window.requestAnimationFrame(install);
  }

  new MutationObserver(scheduleInstall).observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["data-cover-hidden-sign-language"]
  });
  window.addEventListener("resize", scheduleInstall);
  window.addEventListener("adt:dock-resize", scheduleInstall);
  window.addEventListener("orientationchange", scheduleInstall);
  if (window.visualViewport) window.visualViewport.addEventListener("resize", scheduleInstall);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleInstall, { once: true });
  } else {
    scheduleInstall();
  }
})();
