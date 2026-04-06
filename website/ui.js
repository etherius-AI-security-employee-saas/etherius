(() => {
  const body = document.body;
  const page = body.dataset.page || "";

  const nav = document.querySelector(".nav-links");
  const menuBtn = document.querySelector(".menu-btn");
  if (nav && menuBtn) {
    menuBtn.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });

    nav.querySelectorAll("a").forEach((a) => {
      if (a.dataset.page === page) {
        a.classList.add("active");
      }
      a.addEventListener("click", () => {
        nav.classList.remove("open");
        menuBtn.setAttribute("aria-expanded", "false");
      });
    });
  }

  const cursor = document.createElement("div");
  cursor.className = "cursor-glow";
  document.body.appendChild(cursor);

  let hideTimer = null;
  window.addEventListener("pointermove", (e) => {
    cursor.style.opacity = "1";
    cursor.style.left = `${e.clientX}px`;
    cursor.style.top = `${e.clientY}px`;
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      cursor.style.opacity = "0";
    }, 400);
  }, { passive: true });

  document.querySelectorAll(".btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const rect = btn.getBoundingClientRect();
      const ripple = document.createElement("span");
      ripple.className = "ripple";
      ripple.style.left = `${e.clientX - rect.left}px`;
      ripple.style.top = `${e.clientY - rect.top}px`;
      btn.appendChild(ripple);
      setTimeout(() => ripple.remove(), 650);
    });
  });

  document.querySelectorAll(".card, .download-card").forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const rx = ((y / rect.height) - 0.5) * -5;
      const ry = ((x / rect.width) - 0.5) * 8;
      card.style.transform = `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-2px)`;
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
  }, { threshold: 0.14 });

  document.querySelectorAll(".reveal").forEach((el) => revealObserver.observe(el));

  const wipe = document.createElement("div");
  wipe.className = "page-wipe";
  document.body.appendChild(wipe);

  const resetWipe = () => {
    wipe.classList.remove("active");
  };

  // Back/forward cache can restore the page with classes intact.
  // Always clear transition overlay on restore/load.
  resetWipe();
  window.addEventListener("pageshow", resetWipe);
  window.addEventListener("popstate", resetWipe);

  document.querySelectorAll("a[data-transition='page']").forEach((link) => {
    const href = link.getAttribute("href") || "";
    if (!href.startsWith("/") || href.startsWith("/api")) {
      return;
    }
    link.addEventListener("click", (e) => {
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) {
        return;
      }
      e.preventDefault();
      wipe.classList.add("active");
      setTimeout(() => {
        window.location.href = href;
      }, 180);
      // Safety fallback in case navigation is interrupted.
      setTimeout(resetWipe, 1200);
    });
  });

  const counters = document.querySelectorAll("[data-count]");
  if (counters.length) {
    const runCounter = (el) => {
      const target = Number(el.dataset.count || "0");
      const suffix = el.dataset.suffix || "";
      const decimals = Number(el.dataset.decimals || "0");
      const prefix = el.dataset.prefix || "";
      const duration = 1150;
      const start = performance.now();

      const tick = (now) => {
        const p = Math.min((now - start) / duration, 1);
        const val = target * (1 - Math.pow(1 - p, 3));
        el.textContent = `${prefix}${decimals ? val.toFixed(decimals) : Math.floor(val)}${suffix}`;
        if (p < 1) {
          requestAnimationFrame(tick);
        } else {
          el.textContent = `${prefix}${decimals ? target.toFixed(decimals) : target}${suffix}`;
        }
      };

      requestAnimationFrame(tick);
    };

    let done = false;
    const statSection = document.querySelector(".stats-row") || counters[0];
    const statObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !done) {
          done = true;
          counters.forEach(runCounter);
        }
      });
    }, { threshold: 0.26 });

    statObserver.observe(statSection);
  }

  const copyBtn = document.querySelector("[data-copy]");
  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      const value = copyBtn.dataset.copy || "";
      try {
        await navigator.clipboard.writeText(value);
        const original = copyBtn.textContent;
        copyBtn.textContent = "Copied";
        setTimeout(() => {
          copyBtn.textContent = original;
        }, 1000);
      } catch {
        copyBtn.textContent = "Copy Failed";
      }
    });
  }

  const featureButtons = document.querySelectorAll("[data-feature-title]");
  if (featureButtons.length) {
    const titleEl = document.getElementById("focus-title");
    const bodyEl = document.getElementById("focus-body");
    featureButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        if (!titleEl || !bodyEl) return;
        titleEl.textContent = btn.dataset.featureTitle || "Feature";
        bodyEl.textContent = btn.dataset.featureBody || "";
      });
    });
  }
})();
