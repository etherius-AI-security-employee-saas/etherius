const TIMEOUT_MS = 2800;
const MAX_RESEARCH_SOURCES = 12;
const TRUSTED_ENTERPRISE_DOMAINS = [
  "google.com",
  "microsoft.com",
  "linkedin.com",
  "github.com",
  "amazon.com",
  "apple.com",
  "adobe.com",
  "oracle.com",
  "salesforce.com",
  "deloitte.com",
  "accenture.com",
  "tcs.com",
  "infosys.com",
  "wipro.com"
];

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ message: "Method not allowed" });
  }

  const senderDomain = normalizeDomain(String(req.body?.senderDomain || ""));
  const senderName = String(req.body?.senderName || "").trim();
  const subject = String(req.body?.subject || "").trim();
  const body = String(req.body?.body || "").trim();

  if (!senderDomain) {
    return res.status(400).json({ message: "senderDomain is required" });
  }

  const orgHint = deriveOrgHint(senderName, senderDomain, subject, body);
  const queries = buildResearchQueries(senderDomain, orgHint);
  const sourceTargets = buildSourceTargets(senderDomain, orgHint).slice(0, MAX_RESEARCH_SOURCES);

  const [rdap, clearbit, wiki, certs, urlhaus, searchResults, sourceEvidence] = await Promise.all([
    fetchJsonWithTimeout(`https://rdap.org/domain/${encodeURIComponent(senderDomain)}`),
    fetchJsonWithTimeout(`https://autocomplete.clearbit.com/v1/companies/suggest?query=${encodeURIComponent(orgHint)}`),
    fetchJsonWithTimeout(`https://en.wikipedia.org/w/api.php?action=opensearch&search=${encodeURIComponent(orgHint)}&limit=3&namespace=0&format=json`),
    fetchJsonWithTimeout(`https://crt.sh/?q=%25.${encodeURIComponent(senderDomain)}&output=json`),
    fetchUrlHaus(senderDomain),
    Promise.all(queries.map((query) => fetchDuckDuckGo(query))),
    Promise.all(sourceTargets.map((target) => fetchSourceEvidence(target, senderDomain, orgHint)))
  ]);

  const searchSignals = analyzeSearchResults(searchResults, senderDomain, orgHint);
  const sourceSignals = analyzeSourceEvidence(sourceEvidence);
  const domainAgeDays = extractDomainAgeDays(rdap);
  const clearbitMatch = findClearbitMatch(clearbit, senderDomain, orgHint);
  const wikiMatch = findWikiMatch(wiki, orgHint);
  const certCount = Array.isArray(certs) ? Math.min(certs.length, 600) : 0;
  const urlhausMalicious = Boolean(urlhaus?.malicious);

  const inferredOfficial = domainAgeDays >= 3650 && certCount >= 10;
  const officialMatch = Boolean(
    clearbitMatch ||
    searchSignals.officialMatch ||
    sourceSignals.officialMatches >= 2 ||
    TRUSTED_ENTERPRISE_DOMAINS.some((trusted) => senderDomain === trusted || senderDomain.endsWith(`.${trusted}`)) ||
    inferredOfficial
  );

  const popularityScore = clampScore(
    (clearbitMatch ? 2 : 0) +
    (wikiMatch ? 1 : 0) +
    (certCount >= 3 ? 1 : 0) +
    searchSignals.popularityScore +
    sourceSignals.popularityHits
  );

  const reviewPositiveScore = clampScore(
    searchSignals.reviewPositiveScore +
    sourceSignals.reviewPositiveHits +
    (wikiMatch ? 1 : 0)
  );

  const reviewNegativeScore = clampScore(
    searchSignals.reviewNegativeScore +
    sourceSignals.reviewNegativeHits
  );

  const lowFootprintPenalty = (!officialMatch && popularityScore <= 1 && domainAgeDays >= 0 && domainAgeDays <= 365) ? 2 : 0;
  const suspiciousDomainPenalty = looksSuspiciousDomain(senderDomain) ? 2 : 0;
  const scamSignalScore = clampScore(
    searchSignals.scamSignalScore +
    sourceSignals.scamHits +
    (urlhausMalicious ? 3 : 0) +
    lowFootprintPenalty +
    suspiciousDomainPenalty
  );

  const trustedEnterpriseBoost = (officialMatch && domainAgeDays >= 3650 && scamSignalScore <= 1) ? 2 : 0;
  const trustedDomainBoost = isTrustedEnterpriseDomain(senderDomain) ? 12 : 0;
  const legitimacyScore = clamp100(
    45 +
    (officialMatch ? 20 : 0) +
    Math.min(popularityScore * 5, 20) +
    Math.min(reviewPositiveScore * 4, 16) -
    Math.min(reviewNegativeScore * 5, 20) -
    Math.min(scamSignalScore * 9, 36) +
    trustedEnterpriseBoost +
    trustedDomainBoost
  );

  const sources = dedupeUrls([
    ...searchSignals.sources,
    ...sourceSignals.reachableSources,
    clearbitMatch?.domain ? `https://${clearbitMatch.domain}` : "",
    wikiMatch?.url || "",
    "https://rdap.org/",
    "https://crt.sh/",
    "https://urlhaus.abuse.ch/"
  ]).slice(0, 16);

  const summary = buildSummary({
    senderDomain,
    domainAgeDays,
    officialMatch,
    popularityScore,
    scamSignalScore,
    urlhausMalicious,
    legitimacyScore,
    trustedDomain: isTrustedEnterpriseDomain(senderDomain),
    suspiciousDomain: looksSuspiciousDomain(senderDomain),
    sourcesAttempted: sourceTargets.length,
    sourcesReachable: sourceSignals.reachableCount
  });

  return res.status(200).json({
    report: {
      senderDomain,
      domainAgeDays,
      officialMatch,
      popularityScore,
      reviewPositiveScore,
      reviewNegativeScore,
      scamSignalScore,
      legitimacyScore,
      sources,
      sourcesAttempted: sourceTargets.length,
      sourcesReachable: sourceSignals.reachableCount,
      summary
    }
  });
};

function buildResearchQueries(senderDomain, orgHint) {
  return [
    `${orgHint} official website`,
    `${orgHint} trustpilot reviews`,
    `${orgHint} glassdoor reviews`,
    `${orgHint} scam complaints`,
    `${senderDomain} phishing reports`,
    `${senderDomain} linkedin company`,
    `${senderDomain} reddit reviews`,
    `${orgHint} is legit`
  ];
}

function buildSourceTargets(senderDomain, orgHint) {
  const encodedDomain = encodeURIComponent(senderDomain);
  const encodedHint = encodeURIComponent(orgHint);
  return [
    { label: "Official Site", url: `http://${senderDomain}` },
    { label: "Wikipedia", url: `http://en.wikipedia.org/wiki/${encodedHint}` },
    { label: "LinkedIn", url: `http://www.linkedin.com/company/${encodedHint}` },
    { label: "Crunchbase", url: `http://www.crunchbase.com/organization/${encodedHint}` },
    { label: "Glassdoor", url: `http://www.glassdoor.com/Reviews/${encodedHint}-Reviews-EI_IE.htm` },
    { label: "Indeed", url: `http://www.indeed.com/cmp/${encodedHint}/reviews` },
    { label: "Trustpilot", url: `http://www.trustpilot.com/review/${encodedDomain}` },
    { label: "ScamAdviser", url: `http://www.scamadviser.com/check-website/${encodedDomain}` },
    { label: "G2", url: `http://www.g2.com/search?query=${encodedHint}` },
    { label: "Sitejabber", url: `http://www.sitejabber.com/search?query=${encodedHint}` },
    { label: "Reddit", url: `http://www.reddit.com/search/?q=${encodedHint}` },
    { label: "BBB", url: `http://www.bbb.org/search?find_text=${encodedHint}` }
  ];
}

function deriveOrgHint(senderName, senderDomain, subject, body) {
  const senderNameClean = String(senderName || "").trim();
  const genericSenderName = /^(hr|hr team|human resources|recruiter|talent|hiring team|admin|support|team)$/i.test(senderNameClean);
  if (!senderNameClean || genericSenderName) {
    return senderDomain.split(".")[0].replace(/[-_]/g, " ").slice(0, 64) || senderDomain;
  }

  const raw = [senderName, subject, body].join(" ");
  const cleaned = raw
    .replace(/[^a-zA-Z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const match = cleaned.match(/\b([A-Z][a-zA-Z0-9&.-]{2,}\s?(?:[A-Z][a-zA-Z0-9&.-]{1,})?)\b/);
  if (match && match[1]) {
    return match[1].slice(0, 64);
  }

  return senderDomain.split(".")[0].replace(/[-_]/g, " ").slice(0, 64) || senderDomain;
}

async function fetchSourceEvidence(target, senderDomain, orgHint) {
  const proxyUrl = `https://r.jina.ai/${target.url}`;
  const content = await fetchTextSnapshot(proxyUrl);
  const text = String(content || "").toLowerCase();
  const reachable = text.length > 80;
  const orgToken = String(orgHint || "").toLowerCase();
  const officialMention = reachable && text.includes(senderDomain);
  const reviewPositiveHits = countKeywordHits(text, ["verified", "legitimate", "trusted", "well known", "established", "official"]);
  const reviewNegativeHits = countKeywordHits(text, ["complaint", "negative", "lawsuit", "warning", "bad review", "unsafe"]);
  const scamHits = countKeywordHits(text, [
    "reported scam",
    "fraud complaint",
    "phishing campaign",
    "blacklisted domain",
    "malicious domain",
    "advance fee scam",
    "impersonation attack"
  ]);

  return {
    label: target.label,
    url: target.url.replace(/^http:\/\//, "https://"),
    reachable,
    officialMention,
    reviewPositiveHits,
    reviewNegativeHits,
    scamHits
  };
}

async function fetchDuckDuckGo(query) {
  return fetchJsonWithTimeout(`https://api.duckduckgo.com/?q=${encodeURIComponent(query)}&format=json&no_redirect=1&skip_disambig=1`);
}

async function fetchUrlHaus(domain) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
    const response = await fetch("https://urlhaus-api.abuse.ch/v1/host/", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: `host=${encodeURIComponent(domain)}`,
      signal: controller.signal
    });
    clearTimeout(timeout);
    if (!response.ok) {
      return null;
    }
    const payload = await response.json();
    return {
      malicious: payload?.query_status === "ok" && Number(payload?.urls) > 0
    };
  } catch (_error) {
    return null;
  }
}

async function fetchJsonWithTimeout(url) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
    const response = await fetch(url, { signal: controller.signal, headers: { "User-Agent": "Etherius-Company-Intel/1.0" } });
    clearTimeout(timeout);
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch (_error) {
    return null;
  }
}

async function fetchTextSnapshot(url) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
    const response = await fetch(url, { signal: controller.signal, headers: { "User-Agent": "Etherius-Company-Intel/1.0" } });
    clearTimeout(timeout);
    if (!response.ok) {
      return "";
    }
    return await response.text();
  } catch (_error) {
    return "";
  }
}

function analyzeSearchResults(results, senderDomain, orgHint) {
  const sourceUrls = [];
  let officialMatch = false;
  let popularityScore = 0;
  let reviewPositiveScore = 0;
  let reviewNegativeScore = 0;
  let scamSignalScore = 0;

  (Array.isArray(results) ? results : []).forEach((item) => {
    if (!item) {
      return;
    }
    const abstractText = String(item.AbstractText || "");
    const heading = String(item.Heading || "");
    const abstractUrl = String(item.AbstractURL || "");
    const related = flattenRelatedTopics(item.RelatedTopics || []);

    if (abstractUrl) {
      sourceUrls.push(abstractUrl);
    }

    const combined = `${abstractText} ${heading} ${related}`.toLowerCase();
    const officialDomain = normalizeDomain(extractDomain(abstractUrl));
    if (officialDomain && (officialDomain === senderDomain || senderDomain.endsWith(`.${officialDomain}`) || officialDomain.endsWith(`.${senderDomain}`))) {
      officialMatch = true;
    }

    if (combined.includes(orgHint.toLowerCase()) || combined.includes(senderDomain)) {
      popularityScore += 1;
    }
    reviewPositiveScore += countKeywordHits(combined, ["trusted", "legitimate", "official", "verified", "established"]);
    reviewNegativeScore += countKeywordHits(combined, ["complaint", "issue", "negative review", "warning"]);
    scamSignalScore += countKeywordHits(combined, [
      "reported scam",
      "fraud complaint",
      "phishing campaign",
      "blacklisted domain",
      "advance fee scam",
      "fake recruiter scam"
    ]);
  });

  return {
    officialMatch,
    popularityScore: clampScore(popularityScore),
    reviewPositiveScore: clampScore(reviewPositiveScore),
    reviewNegativeScore: clampScore(reviewNegativeScore),
    scamSignalScore: clampScore(scamSignalScore),
    sources: dedupeUrls(sourceUrls)
  };
}

function analyzeSourceEvidence(items) {
  const list = Array.isArray(items) ? items : [];
  const reachable = list.filter((item) => item?.reachable);
  return {
    reachableCount: reachable.length,
    officialMatches: reachable.filter((item) => item.officialMention).length,
    popularityHits: clampScore(
      reachable.length >= 8 ? 5 :
      reachable.length >= 6 ? 4 :
      reachable.length >= 4 ? 3 :
      reachable.length >= 2 ? 2 :
      reachable.length >= 1 ? 1 : 0
    ),
    reviewPositiveHits: clampScore(reachable.reduce((acc, item) => acc + Number(item.reviewPositiveHits || 0), 0)),
    reviewNegativeHits: clampScore(reachable.reduce((acc, item) => acc + Number(item.reviewNegativeHits || 0), 0)),
    scamHits: clampScore(reachable.reduce((acc, item) => acc + Number(item.scamHits || 0), 0)),
    reachableSources: dedupeUrls(reachable.map((item) => item.url))
  };
}

function flattenRelatedTopics(topics) {
  const out = [];
  const queue = Array.isArray(topics) ? topics.slice(0, 12) : [];
  while (queue.length) {
    const next = queue.shift();
    if (!next) {
      continue;
    }
    if (next.Text) {
      out.push(String(next.Text));
    }
    if (Array.isArray(next.Topics)) {
      queue.push(...next.Topics.slice(0, 8));
    }
  }
  return out.join(" ");
}

function findClearbitMatch(clearbitPayload, senderDomain, orgHint) {
  if (!Array.isArray(clearbitPayload)) {
    return null;
  }
  const hint = orgHint.toLowerCase();
  return clearbitPayload.find((entry) => {
    const domain = normalizeDomain(String(entry?.domain || ""));
    const name = String(entry?.name || "").toLowerCase();
    if (!domain) {
      return false;
    }
    return domain === senderDomain || senderDomain.endsWith(`.${domain}`) || name.includes(hint);
  }) || null;
}

function findWikiMatch(wikiPayload, orgHint) {
  if (!Array.isArray(wikiPayload) || wikiPayload.length < 4) {
    return null;
  }
  const titles = Array.isArray(wikiPayload[1]) ? wikiPayload[1] : [];
  const urls = Array.isArray(wikiPayload[3]) ? wikiPayload[3] : [];
  const hint = orgHint.toLowerCase();
  for (let i = 0; i < Math.min(titles.length, urls.length, 3); i += 1) {
    if (String(titles[i] || "").toLowerCase().includes(hint)) {
      return { title: titles[i], url: urls[i] };
    }
  }
  return null;
}

function extractDomainAgeDays(rdapPayload) {
  const events = Array.isArray(rdapPayload?.events) ? rdapPayload.events : [];
  const registration = events.find((event) => /registration/i.test(String(event?.eventAction || "")));
  const date = registration?.eventDate ? new Date(registration.eventDate) : null;
  if (!date || Number.isNaN(date.getTime())) {
    return -1;
  }
  return Math.max(0, Math.floor((Date.now() - date.getTime()) / 86400000));
}

function buildSummary(input) {
  const years = input.domainAgeDays > 0 ? Math.floor(input.domainAgeDays / 365) : 0;
  const ageText = input.domainAgeDays < 0
    ? "domain age unavailable"
    : years > 0 ? `${years}+ years` : `${input.domainAgeDays} days`;
  const coverage = `${input.sourcesReachable}/${input.sourcesAttempted}`;

  if (input.scamSignalScore >= 3 || input.urlhausMalicious || (input.suspiciousDomain && input.legitimacyScore <= 30)) {
    return `Clear answer: likely high risk/fake. Research coverage ${coverage}. Scam/fraud indicators were found for ${input.senderDomain} (domain age ${ageText}).`;
  }
  if (input.trustedDomain && input.scamSignalScore <= 1) {
    return `Clear answer: likely legitimate organization. Research coverage ${coverage}. ${input.senderDomain} matches a trusted enterprise profile with low fraud signals (domain age ${ageText}).`;
  }
  if (input.officialMatch && input.legitimacyScore >= 75 && input.scamSignalScore <= 1) {
    return `Clear answer: likely legitimate organization. Research coverage ${coverage}. ${input.senderDomain} shows official footprint with low fraud signals (domain age ${ageText}).`;
  }
  return `Clear answer: needs manual verification. Research coverage ${coverage}. Mixed trust signals were found for ${input.senderDomain} (domain age ${ageText}).`;
}

function normalizeDomain(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/^https?:\/\//, "")
    .replace(/^www\./, "")
    .replace(/\/.*$/, "");
}

function extractDomain(urlValue) {
  try {
    return new URL(urlValue).hostname;
  } catch (_error) {
    return "";
  }
}

function countKeywordHits(text, keywords) {
  const normalized = String(text || "").toLowerCase();
  return keywords.reduce((acc, keyword) => acc + (normalized.includes(keyword) ? 1 : 0), 0);
}

function clampScore(value) {
  return Math.max(0, Math.min(5, Number(value || 0)));
}

function clamp100(value) {
  return Math.max(0, Math.min(100, Math.round(Number(value || 0))));
}

function dedupeUrls(urls) {
  return [...new Set((Array.isArray(urls) ? urls : []).map((item) => String(item || "").trim()).filter(Boolean))];
}

function looksSuspiciousDomain(domain) {
  const normalized = normalizeDomain(domain);
  if (!normalized) {
    return false;
  }
  const riskyTlds = [".xyz", ".top", ".click", ".live", ".buzz", ".cam", ".shop"];
  if (riskyTlds.some((tld) => normalized.endsWith(tld))) {
    return true;
  }
  if (/(secure|verify|update|login|pay|intern|hr|career|wallet)/i.test(normalized) && /[0-9-]/.test(normalized)) {
    return true;
  }
  return false;
}

function isTrustedEnterpriseDomain(domain) {
  const normalized = normalizeDomain(domain);
  return TRUSTED_ENTERPRISE_DOMAINS.some((trusted) => normalized === trusted || normalized.endsWith(`.${trusted}`));
}
