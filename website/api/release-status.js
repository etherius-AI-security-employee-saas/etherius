const OWNER = "etherius-AI-security-employee-saas";
const REPO = "etherius";

module.exports = async function handler(req, res) {
  try {
    const response = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}/releases/latest`, {
      headers: { "User-Agent": "etherius-site-release-status" },
    });
    if (!response.ok) throw new Error("release status lookup failed");
    const release = await response.json();
    res.setHeader("Cache-Control", "s-maxage=300, stale-while-revalidate=300");
    return res.status(200).json({
      version: release?.tag_name || "latest",
      published_at: release?.published_at || null,
      assets: Array.isArray(release?.assets) ? release.assets.length : 0,
    });
  } catch (error) {
    res.setHeader("Cache-Control", "no-store");
    return res.status(200).json({
      version: "latest",
      published_at: null,
      assets: 0,
    });
  }
};
