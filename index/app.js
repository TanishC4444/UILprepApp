(function () {
  document.documentElement.classList.add('js');

  const toggle = document.querySelector('[data-nav-toggle]');
  const nav = document.querySelector('[data-site-nav]');

  if (toggle && nav) {
    const closeMenu = () => {
      toggle.setAttribute('aria-expanded', 'false');
      nav.classList.remove('open');
      document.body.classList.remove('menu-open');
    };

    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('open', open);
      document.body.classList.toggle('menu-open', open);
    });

    nav.addEventListener('click', (event) => {
      if (event.target.closest('a')) closeMenu();
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        closeMenu();
        toggle.focus();
      }
    });

    window.addEventListener('resize', () => {
      if (window.innerWidth > 900) closeMenu();
    });
  }

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const reveals = document.querySelectorAll('.reveal');

  reveals.forEach((element, index) => {
    element.style.transitionDelay = `${Math.min(index % 4, 3) * 70}ms`;
  });

  if (reducedMotion || !('IntersectionObserver' in window)) {
    reveals.forEach((element) => element.classList.add('is-visible'));
  } else {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px' });
    reveals.forEach((element) => observer.observe(element));
  }

  const search = document.querySelector('[data-event-search]');
  const gradeFilter = document.querySelector('[data-grade-filter]');
  const cards = [...document.querySelectorAll('[data-event-card]')];
  const count = document.querySelector('[data-result-count]');
  const empty = document.querySelector('[data-empty-state]');

  if (cards.length && search && gradeFilter) {
    const updateEvents = () => {
      const query = search.value.trim().toLowerCase();
      const grade = gradeFilter.value;
      let visible = 0;

      cards.forEach((card) => {
        const haystack = `${card.dataset.name} ${card.textContent}`.toLowerCase();
        const grades = (card.dataset.grades || '').split(',');
        const matchesSearch = !query || haystack.includes(query);
        const matchesGrade = !grade || grades.includes(grade);
        const show = matchesSearch && matchesGrade;
        card.hidden = !show;
        if (show) visible += 1;
      });

      if (count) count.textContent = `${visible} event${visible === 1 ? '' : 's'} shown`;
      if (empty) empty.classList.toggle('visible', visible === 0);
    };

    search.addEventListener('input', updateEvents);
    gradeFilter.addEventListener('change', updateEvents);
    updateEvents();
  }

  const alignmentLinks = window.UIL_ALIGNMENT_LINKS || {};
  document.querySelectorAll('[data-conference]').forEach((link) => {
    const resolved = alignmentLinks[link.dataset.conference];
    if (resolved) link.href = resolved;
  });

  const hero = document.querySelector('[data-hero]');
  const meetBoard = document.querySelector('[data-meet-board]');
  if (hero && meetBoard && !reducedMotion && window.matchMedia('(pointer:fine)').matches) {
    hero.addEventListener('pointermove', (event) => {
      const bounds = hero.getBoundingClientRect();
      const x = ((event.clientX - bounds.left) / bounds.width - 0.5) * 10;
      const y = ((event.clientY - bounds.top) / bounds.height - 0.5) * 10;
      meetBoard.style.setProperty('--board-x', `${x}px`);
      meetBoard.style.setProperty('--board-y', `${y}px`);
    });
    hero.addEventListener('pointerleave', () => {
      meetBoard.style.setProperty('--board-x', '0px');
      meetBoard.style.setProperty('--board-y', '0px');
    });
  }
})();
