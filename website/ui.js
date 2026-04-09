(() => {
  const body = document.body;
  const page = body.dataset.page || "";

  const motes = document.createElement("div");
  motes.className = "bg-motes";
  for (let i = 0; i < 28; i += 1) {
    const mote = document.createElement("span");
    const size = 3 + Math.random() * 8;
    mote.style.width = `${size}px`;
    mote.style.height = `${size}px`;
    mote.style.left = `${Math.random() * 100}%`;
    mote.style.bottom = `${-10 - Math.random() * 40}px`;
    mote.style.animationDuration = `${18 + Math.random() * 22}s`;
    mote.style.animationDelay = `${Math.random() * 14}s`;
    mote.style.opacity = `${0.2 + Math.random() * 0.35}`;
    motes.appendChild(mote);
  }
  document.body.appendChild(motes);

  const nav = document.querySelector(".nav-links");
  const menuBtn = document.querySelector(".menu-btn");
  if (nav && menuBtn) {
    menuBtn.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });

    nav.querySelectorAll("a").forEach((link) => {
      if (link.dataset.page === page) {
        link.classList.add("active");
      }

      link.addEventListener("click", () => {
        nav.classList.remove("open");
        menuBtn.setAttribute("aria-expanded", "false");
      });
    });
  }

  document.querySelectorAll(".btn").forEach((button) => {
    button.addEventListener("click", (event) => {
      const rect = button.getBoundingClientRect();
      const ripple = document.createElement("span");
      ripple.className = "ripple";
      ripple.style.left = `${event.clientX - rect.left}px`;
      ripple.style.top = `${event.clientY - rect.top}px`;
      button.appendChild(ripple);
      setTimeout(() => ripple.remove(), 700);
    });
  });

  document.querySelectorAll(".card, .product-card, .download-card").forEach((card) => {
    card.addEventListener("mousemove", (event) => {
      const rect = card.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      const rx = ((y / rect.height) - 0.5) * -5;
      const ry = ((x / rect.width) - 0.5) * 7;
      card.style.transform = `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-4px)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "";
    });
  });

  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll(".reveal").forEach((element) => revealObserver.observe(element));

  const wipe = document.createElement("div");
  wipe.className = "page-wipe";
  document.body.appendChild(wipe);

  const clearWipe = () => wipe.classList.remove("active");
  clearWipe();
  window.addEventListener("pageshow", clearWipe);
  window.addEventListener("popstate", clearWipe);

  document.querySelectorAll("a[data-transition='page']").forEach((link) => {
    const href = link.getAttribute("href") || "";
    if (!href.startsWith("/") || href.startsWith("/api")) {
      return;
    }

    link.addEventListener("click", (event) => {
      if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) {
        return;
      }

      event.preventDefault();
      wipe.classList.add("active");
      setTimeout(() => {
        window.location.href = href;
      }, 180);
      setTimeout(clearWipe, 1200);
    });
  });

  const counters = document.querySelectorAll("[data-count]");
  if (counters.length) {
    const runCounter = (element) => {
      const target = Number(element.dataset.count || "0");
      const suffix = element.dataset.suffix || "";
      const prefix = element.dataset.prefix || "";
      const decimals = Number(element.dataset.decimals || "0");
      const start = performance.now();
      const duration = 1200;

      const tick = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = target * eased;
        element.textContent = `${prefix}${decimals ? value.toFixed(decimals) : Math.floor(value)}${suffix}`;
        if (progress < 1) {
          requestAnimationFrame(tick);
        } else {
          element.textContent = `${prefix}${decimals ? target.toFixed(decimals) : target}${suffix}`;
        }
      };

      requestAnimationFrame(tick);
    };

    let started = false;
    const trigger = document.querySelector(".stats-row") || counters[0];
    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !started) {
          started = true;
          counters.forEach(runCounter);
        }
      });
    }, { threshold: 0.26 });

    counterObserver.observe(trigger);
  }

  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const value = button.dataset.copy || "";
      const original = button.textContent;
      try {
        await navigator.clipboard.writeText(value);
        button.textContent = "Copied";
      } catch {
        button.textContent = "Copy Failed";
      }
      setTimeout(() => {
        button.textContent = original;
      }, 1200);
    });
  });
})();
