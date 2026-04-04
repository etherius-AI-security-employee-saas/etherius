(function () {
  var status = document.getElementById("release-status");
  var packageLink = document.getElementById("download-package");
  var mainLink = document.getElementById("download-main");

  var fallback =
    "https://github.com/etherius-AI-security-employee-saas/etherius/releases/latest/download/Etherius-Customer-Package.zip";

  function setLink(url) {
    packageLink.setAttribute("href", url);
    mainLink.setAttribute("href", url);
  }

  setLink(fallback);

  fetch("https://api.github.com/repos/etherius-AI-security-employee-saas/etherius/releases/latest")
    .then(function (res) {
      if (!res.ok) throw new Error("No public release yet");
      return res.json();
    })
    .then(function (release) {
      if (!release || !release.assets || !release.assets.length) {
        throw new Error("Release assets missing");
      }

      var preferred = release.assets.find(function (asset) {
        var name = (asset.name || "").toLowerCase();
        return name.indexOf("customer") >= 0 || name.indexOf("package") >= 0;
      });

      var asset = preferred || release.assets[0];
      var url = asset.browser_download_url || fallback;
      setLink(url);
      status.textContent = "Latest build ready: " + release.tag_name + " (" + asset.name + ")";
    })
    .catch(function () {
      status.textContent = "Download service is using the default secure package endpoint.";
    });
})();
