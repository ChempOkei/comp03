// slider не будет воркать без js, могу примитивно написать js, чтобы всё работало, хотя по заданию не требуется

document.addEventListener('DOMContentLoaded', () => {


    const burger    = document.querySelector('.burger');
    const navMobile = document.querySelector('.nav-mobile');
  
    if (burger && navMobile) {
      burger.addEventListener('click', () => {
        const isOpen = burger.classList.toggle('burger--open');
        navMobile.classList.toggle('nav-mobile--open', isOpen);
        document.body.style.overflow = isOpen ? 'hidden' : '';
        burger.setAttribute('aria-expanded', String(isOpen));
      });
  
      navMobile.addEventListener('click', (e) => {
        if (e.target === navMobile) closeMobileMenu();
      });
  
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeMobileMenu();
      });
  
      navMobile.querySelectorAll('.nav-mobile__link').forEach(link => {
        link.addEventListener('click', closeMobileMenu);
      });
  
      window.addEventListener('resize', () => {
        if (window.matchMedia('(min-width: 1024px)').matches) {
          closeMobileMenu();
        }
      });
    }
  
    function closeMobileMenu() {
      if (!burger) return;
      burger.classList.remove('burger--open');
      navMobile?.classList.remove('nav-mobile--open');
      document.body.style.overflow = '';
      burger.setAttribute('aria-expanded', 'false');
    }
  
  
    const header = document.querySelector('.header');
  
    if (header) {
      const onScroll = () => {
        header.classList.toggle('header--scrolled', window.scrollY > 30);
      };
      window.addEventListener('scroll', onScroll, { passive: true });
      onScroll();
    }
  
  
    const sliderTrack = document.querySelector('.slider__track');
    const slides      = document.querySelectorAll('.slider__slide');
    const dots        = document.querySelectorAll('.slider__dot');
    const prevBtn     = document.querySelector('.slider__btn--prev');
    const nextBtn     = document.querySelector('.slider__btn--next');
  
    if (sliderTrack && slides.length) {
      let current     = 0;
      let autoplay    = null;
      const total     = slides.length;
  
  
      const goTo = (index) => {
        current = ((index % total) + total) % total;
  
        sliderTrack.style.transform = `translateX(-${current * 100}%)`;
  
        slides.forEach((s, i) => s.classList.toggle('is-active', i === current));
  
        dots.forEach((d, i) => {
          const isActive = i === current;
          d.classList.toggle('slider__dot--active', isActive);
          d.setAttribute('aria-selected', String(isActive));
        });
      };
  
  // в теории автоплей должен не так выглядеть потому что по другому реализация легче, но я не умею. Так что, автоплей будет такой ведь мы не на ноде)))
      const startAutoplay = () => {
        stopAutoplay();
        autoplay = setInterval(() => goTo(current + 1), 5000);
      };
  
      const stopAutoplay  = () => clearInterval(autoplay);
  
      prevBtn?.addEventListener('click', () => { goTo(current - 1); startAutoplay(); });
      nextBtn?.addEventListener('click', () => { goTo(current + 1); startAutoplay(); });
  
      dots.forEach((dot, i) => {
        dot.addEventListener('click', () => { goTo(i); startAutoplay(); });
      });
  
      let touchStartX = 0;
      sliderTrack.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
      }, { passive: true });
  
      sliderTrack.addEventListener('touchend', (e) => {
        const diff = touchStartX - e.changedTouches[0].clientX;
        if (Math.abs(diff) > 50) {
          goTo(diff > 0 ? current + 1 : current - 1);
          startAutoplay();
        }
      });
  
      sliderTrack.addEventListener('mouseenter', stopAutoplay);
      sliderTrack.addEventListener('mouseleave', startAutoplay);
  
      goTo(0);
      startAutoplay();
    }
  
  
    const filterToggleBtn   = document.querySelector('.filter-toggle-btn');
    const filterPanelMobile = document.querySelector('.filter-panel-mobile');
  
    if (filterToggleBtn && filterPanelMobile) {
      filterPanelMobile.hidden = true;
      filterToggleBtn.addEventListener('click', () => {
        const isOpen = filterPanelMobile.classList.toggle('is-open');
        filterToggleBtn.setAttribute('aria-expanded', String(isOpen));
        filterPanelMobile.hidden = !isOpen;
      });
    }
  
  
    const searchInput = document.querySelector('.search-form__input');
    const searchHints = document.querySelectorAll('.search-hint-tag');
  
    if (searchInput && searchHints.length) {
      searchHints.forEach(hint => {
        hint.addEventListener('click', () => {
          searchInput.value = hint.textContent.trim();
          searchInput.focus();
        });
      });
    }

  
  
    const themeToggle = document.querySelector('#themeToggle');
    const savedTheme = localStorage.getItem('bg-theme');
  
    if (savedTheme === 'light' || savedTheme === 'dark') {
      applyTheme(savedTheme);
    }
  
    if (themeToggle) {
      themeToggle.checked = savedTheme === 'light';
  
      themeToggle.addEventListener('change', () => {
        const theme = themeToggle.checked ? 'light' : 'dark';
        localStorage.setItem('bg-theme', theme);
        applyTheme(theme);
      });
    }
  
    function applyTheme(theme) {
      if (theme === 'light') {
        document.documentElement.classList.add('theme-light');
      } else {
        document.documentElement.classList.remove('theme-light');
      }
    }
  
  
    const animElems = document.querySelectorAll('[data-anim]');
  
    if (animElems.length && 'IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('anim-fadein');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15 });
  
      animElems.forEach(el => observer.observe(el));
    }
  
  
    const fileInput   = document.querySelector('.file-upload__input');
    const previewWrap = document.querySelector('.file-upload__preview');
    const previewImg  = document.querySelector('.file-upload__preview-img');
    const previewName = document.querySelector('.file-upload__preview-name');
  
    if (fileInput && previewWrap) {
      fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (!file) return;
  
        previewName.textContent = file.name;
  
        if (file.type.startsWith('image/')) {
          const reader = new FileReader();
          reader.onload = (e) => {
            previewImg.src = e.target.result;
            previewImg.style.display = 'block';
          };
          reader.readAsDataURL(file);
        } else {
          previewImg.style.display = 'none';
        }
  
        previewWrap.classList.add('is-visible');
      });
  
      const uploadArea = document.querySelector('.file-upload__area');
      if (uploadArea) {
        uploadArea.addEventListener('dragover', (e) => {
          e.preventDefault();
          uploadArea.classList.add('is-dragover');
        });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('is-dragover'));
        uploadArea.addEventListener('drop', (e) => {
          e.preventDefault();
          uploadArea.classList.remove('is-dragover');
          const file = e.dataTransfer.files[0];
          if (file) {
            const dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
            fileInput.dispatchEvent(new Event('change'));
          }
        });
      }
    }
  
  
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        const target = document.querySelector(anchor.getAttribute('href'));
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          closeMobileMenu();
        }
      });
    });
  
  
  
  
    const currentPath = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav__link, .nav-mobile__link, .footer__nav-link').forEach(link => {
      const href = link.getAttribute('href');
      if (href && href !== '#' && currentPath.includes(href.replace('./', ''))) {
        link.classList.add('nav__link--active');
      }
    });
  
  });
  