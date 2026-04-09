module.exports = async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  return res.redirect(307, "/downloads/MailGuard-Extension.zip");
};
