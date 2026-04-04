(function () {
  var status = document.getElementById("release-status");
  if (!status) return;

  fetch("/api/release-status")
    .then(function (res) {
      if (!res.ok) throw new Error("release status unavailable");
      return res.json();
    })
    .then(function (data) {
      var version = data.version || "latest";
      var publishedAt = data.published_at ? new Date(data.published_at).toLocaleDateString() : "recent";
      status.textContent = "Secure build ready: " + version + " (published " + publishedAt + ")";
    })
    .catch(function () {
      status.textContent = "Secure build endpoint is online. Contact sales if download is restricted for your plan.";
    });
})();
