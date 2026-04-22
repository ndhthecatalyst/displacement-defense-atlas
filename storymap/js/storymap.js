/* =========================================================
   Below the Line — StoryMap
   Minimal scroll interactions (no dependencies)
   -------------------------------------------------------
   1. Scroll progress bar (top of viewport)
   2. Nav active-state highlighting via IntersectionObserver
   3. Smooth scroll respecting prefers-reduced-motion
   ========================================================= */
(function () {
  'use strict';

  var progress = document.getElementById('smProgress');
  var navLinks = document.querySelectorAll('.sm-nav-list a');
  var sections = document.querySelectorAll('section[data-chapter]');

  // ---- 1. Progress bar -----------------------------------
  function updateProgress() {
    if (!progress) return;
    var doc = document.documentElement;
    var max = (doc.scrollHeight - doc.clientHeight) || 1;
    var pct = Math.min(100, Math.max(0, (window.scrollY / max) * 100));
    progress.style.width = pct.toFixed(2) + '%';
  }

  var ticking = false;
  window.addEventListener('scroll', function () {
    if (!ticking) {
      window.requestAnimationFrame(function () {
        updateProgress();
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });
  updateProgress();

  // ---- 2. Nav active-state via IntersectionObserver ------
  if ('IntersectionObserver' in window && navLinks.length && sections.length) {
    var linkById = {};
    navLinks.forEach(function (a) {
      var id = (a.getAttribute('href') || '').replace('#', '');
      if (id) linkById[id] = a;
    });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var id = entry.target.id;
        navLinks.forEach(function (a) { a.classList.remove('is-active'); });
        if (linkById[id]) linkById[id].classList.add('is-active');
      });
    }, {
      // Trigger when the chapter's top third is in view
      rootMargin: '-40% 0px -55% 0px',
      threshold: 0
    });

    sections.forEach(function (s) { io.observe(s); });
  }

  // ---- 3. Smooth scroll with reduced-motion respect ------
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  navLinks.forEach(function (a) {
    a.addEventListener('click', function (e) {
      var href = a.getAttribute('href') || '';
      if (href.charAt(0) !== '#') return;
      var target = document.getElementById(href.slice(1));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({
        behavior: reduce ? 'auto' : 'smooth',
        block: 'start'
      });
      // Update hash without jumping
      if (history.replaceState) history.replaceState(null, '', href);
    });
  });
})();
