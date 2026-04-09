const TIMEOUT_MS = 4200;

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

  const [rdap, clearbit, wiki, certs, urlhaus, searchResults, officialSnapshot, trustpilotSnapshot, scamadviserSnapshot] = await Promise.all([
    fetchJsonWithTimeout(`https://rdap.org/domain/${encodeURIComponent(senderDomain)}`),
    fetchJsonWithTimeout(`https://autocomplete.clearbit.com/v1/companies/suggest?query=${encodeURIComponent(orgHint)}`),
    fetchJsonWithTimeout(`https://en.wikipedia.org/w/api.php?action=opensearch&search=${encodeURIComponent(orgHint)}&limit=3&namespace=0&format=json`),
    fetchJsonWithTimeout(`https://crt.sh/?q=%25.${encodeURIComponent(senderDomain)}&output=json`),
    fetchUrlHaus(senderDomain),
    Promise.all(queries.map((query) => fetchDuckDuckGo(query))),
    fetchTextSnapshot(`https://r.jina.ai/http://${senderDomain}`),
    fetchTextSnapshot(`https://r.jina.ai/http://www.trustpilot.com/review/${senderDomain}`),
    fetchTextSnapshot(`https://r.jina.ai/http://www.scamadviser.com/check-website/${senderDomain}`)
  ]);

  const searchSignals = analyzeSearchResults(searchResults, senderDomain, orgHint);
  const snapshotSignals = analyzeTextSnapshots({
    senderDomain,
    orgHint,
    officialSnapshot,
    trustpilotSnapshot,
    scamadviserSnapshot
  });
  const domainAgeDays = extractDomainAgeDays(rdap);
  const clearbitMatch = findClearbitMatch(clearbit, senderDomain, orgHint);
  const wikiMatch = findWikiMatch(wiki, orgHint);
  const certCount = Array.isArray(certs) ? Math.min(certs.length, 500) : 0;
  const urlhausMalicious = Boolean(urlhaus?.malicious);

  const inferredOfficial = domainAgeDays >= 3650 && certCount >= 10;
  const officialMatch = Boolean(clearbitMatch || searchSignals.officialMatch || snapshotSignals.officialMatch || inferredOfficial);
  const popularityScore = clampScore(
    (clearbitMatch ? 2 : 0) +
    (wikiMatch ? 1 : 0) +
    (certCount >= 3 ? 1 : 0) +
    searchSignals.popularityScore +
    snapshotSignals.popularityScore
  );

  const reviewPositiveScore = clampScore(searchSignals.reviewPositiveScore + snapshotSignals.reviewPositiveScore + (wikiMatch ? 1 : 0));
  const reviewNegativeScore = clampScore(searchSignals.reviewNegativeScore + snapshotSignals.reviewNegativeScore);
  const lowFootprintPenalty = (!officialMatch && popularityScore === 0 && domainAgeDays >= 0 && domainAgeDays <= 365) ? 2 : 0;
  const suspiciousDomainPenalty = looksSuspiciousDomain(senderDomain) ? 2 : 0;
  const scamSignalScore = clampScore(searchSignals.scamSignalScore + snapshotSignals.scamSignalScore + (urlhausMalicious ? 3 : 0) + lowFootprintPenalty + suspiciousDomainPenalty);

  const sources = dedupeUrls([
    ...searchSignals.sources,
    ...snapshotSignals.sources,
    clearbitMatch?.domain ? `https://${clearbitMatch.domain}` : "",
    wikiMatch?.url || "",
    "https://rdap.org/",
    "https://crt.sh/",
    "https://urlhaus.abuse.ch/"
  ]).slice(0, 8);

  const summary = buildSummary({
    senderDomain,
    domainAgeDays,
    officialMatch,
    popularityScore,
    reviewPositiveScore,
    reviewNegativeScore,
    scamSignalScore,
    urlhausMalicious
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
      sources,
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
    `${senderDomain} linkedin company`
  ];
}

function deriveOrgHint(senderName, senderDomain, subject, body) {
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

function analyzeSearchResults(results, senderDomain, orgHint) {
  const sourceUrls = [];
  const textChunks = [];
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

    textChunks.push(abstractText, heading, related);
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
    scamSignalScore += countKeywordHits(combined, ["scam", "fraud", "phishing", "fake recruiter", "advance fee", "spam"]);
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

  if (input.scamSignalScore >= 3 || input.urlhausMalicious) {
    return `Web research flagged elevated risk: scam/fraud mentions or threat-intel hits were found for ${input.senderDomain} (domain age ${ageText}).`;
  }
  if (input.officialMatch && input.domainAgeDays >= 3650 && input.scamSignalScore <= 1) {
    return `Web research indicates a likely legitimate established organization for ${input.senderDomain} with long domain history (${ageText}) and low fraud signals.`;
  }
  if (input.officialMatch && input.popularityScore >= 3 && input.reviewNegativeScore <= 1) {
    return `Web research indicates a strong legitimate footprint for ${input.senderDomain}: official presence, broad popularity, and low complaint signals (domain age ${ageText}).`;
  }
  return `Web research for ${input.senderDomain} is mixed. Verify high-impact requests manually. Domain age: ${ageText}.`;
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
  const normalized = String(text || "");
  return keywords.reduce((acc, keyword) => acc + (normalized.includes(keyword) ? 1 : 0), 0);
}

function clampScore(value) {
  return Math.max(0, Math.min(5, Number(value || 0)));
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

function analyzeTextSnapshots(input) {
  const officialText = String(input.officialSnapshot || "").toLowerCase();
  const trustpilotText = String(input.trustpilotSnapshot || "").toLowerCase();
  const scamadviserText = String(input.scamadviserSnapshot || "").toLowerCase();
  const hint = String(input.orgHint || "").toLowerCase();
  const senderDomain = String(input.senderDomain || "").toLowerCase();

  const officialMatch = officialText.includes(senderDomain) || (hint && officialText.includes(hint));
  const popularityScore = [
    officialText.includes(senderDomain),
    trustpilotText.includes(senderDomain),
    scamadviserText.includes(senderDomain)
  ].filter(Boolean).length;

  const reviewPositiveScore =
    countKeywordHits(trustpilotText, ["excellent", "great", "verified company", "trustscore", "review"]) +
    countKeywordHits(officialText, ["about us", "careers", "investors"]);

  const reviewNegativeScore =
    countKeywordHits(trustpilotText, ["poor", "bad", "complaint", "negative"]) +
    countKeywordHits(scamadviserText, ["suspicious", "low trust", "warning"]);

  const scamSignalScore =
    countKeywordHits(scamadviserText, ["scam", "phishing", "fraud", "unsafe", "malicious"]) +
    countKeywordHits(trustpilotText, ["scam", "fraud"]);

  return {
    officialMatch,
    popularityScore: clampScore(popularityScore),
    reviewPositiveScore: clampScore(reviewPositiveScore),
    reviewNegativeScore: clampScore(reviewNegativeScore),
    scamSignalScore: clampScore(scamSignalScore),
    sources: [
      `https://${senderDomain}`,
      `https://www.trustpilot.com/review/${senderDomain}`,
      `https://www.scamadviser.com/check-website/${senderDomain}`
    ]
  };
}
