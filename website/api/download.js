const OWNER = "etherius-AI-security-employee-saas";
const REPO = "etherius";
const FALLBACK = "https://etherius-security-site.vercel.app/";

function pickAsset(assets = []) {
  const preferred = assets.find((asset) => {
    const name = String(asset?.name || "").toLowerCase();
    return name.includes("setup") || name.includes("suite") || name.includes("customer") || name.includes("package");
  });
  return preferred || assets[0];
}

module.exports = async function handler(req, res) {
  try {
    const response = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}/releases/latest`, {
      headers: { "User-Agent": "etherius-site-download" },
    });
    if (!response.ok) throw new Error("latest release lookup failed");
    const release = await response.json();
    const asset = pickAsset(release?.assets || []);
    const downloadUrl = asset?.browser_download_url;
    if (!downloadUrl) throw new Error("download asset missing");
    res.setHeader("Cache-Control", "no-store");
    return res.redirect(307, downloadUrl);
  } catch (error) {
    res.setHeader("Cache-Control", "no-store");
    return res.redirect(302, FALLBACK);
  }
};
