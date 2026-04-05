(function () {
  var status = document.getElementById("release-status");
  var endpointText = document.getElementById("live-endpoint-text");
  var year = document.getElementById("footer-year");

  if (year) {
    year.textContent = "Copyright " + new Date().getFullYear() + " Etherius. Unified enterprise endpoint defense.";
  }

  if (endpointText) {
    var messages = ["Awaiting activation", "Policy sync ready", "Telemetry channel secure", "AI engine standing by"];
    var idx = 0;
    setInterval(function () {
      idx = (idx + 1) % messages.length;
      endpointText.textContent = messages[idx];
    }, 2400);
  }

  if (status) {
    status.textContent = "Checking secure build channel...";
    fetch("/api/download", { method: "HEAD", cache: "no-store" })
      .then(function (res) {
        if (res.ok || (res.status >= 300 && res.status < 400)) {
          status.textContent = "Secure setup package ready. Includes installer only (no source bundle).";
        } else {
          status.textContent = "Build channel reachable. Contact support if download is interrupted.";
        }
      })
      .catch(function () {
        status.textContent = "Build channel check complete. If download fails, retry in a few seconds.";
      });
  }

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
        }
      });
    },
    { threshold: 0.12 }
  );

  document.querySelectorAll(".reveal").forEach(function (el) {
    observer.observe(el);
  });
})();
