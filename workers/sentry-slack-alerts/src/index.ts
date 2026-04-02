export interface Env {
  SLACK_WEBHOOK_URL: string;
  SENTRY_WEBHOOK_SECRET: string;
}

interface SentryTag {
  key: string;
  value: string;
}

interface SentryProject {
  id: string;
  name: string;
  slug: string;
}

interface SentryIssue {
  id: string;
  title: string;
  culprit: string;
  permalink: string;
  shortId: string;
  status: string;
  count: string;
  userCount: number;
  firstSeen: string;
  lastSeen: string;
  tags: SentryTag[];
  priority: string;
  project: SentryProject;
}

interface SentryWebhookPayload {
  action: string;
  data: {
    issue: SentryIssue;
  };
}

// ── Helpers ────────────────────────────────────────────────────────────────

function getTag(tags: SentryTag[], key: string): string | undefined {
  return tags.find((t) => t.key === key)?.value;
}

function hexToBuffer(hex: string): ArrayBuffer {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.slice(i, i + 2), 16);
  }
  return bytes.buffer;
}

async function verifySignature(
  secret: string,
  body: string,
  signature: string,
): Promise<boolean> {
  if (!signature) return false;
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"],
  );
  return crypto.subtle.verify("HMAC", key, hexToBuffer(signature), enc.encode(body));
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("es-ES", {
    timeZone: "UTC",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }) + " UTC";
}

// ── Slack message builders ─────────────────────────────────────────────────

function buildFullMessage(issue: SentryIssue): object {
  const priority = issue.priority ?? "medium";
  const emoji = priority === "critical" ? "🔴" : priority === "high" ? "🟠" : "🟡";
  const color = priority === "critical" || priority === "high" ? "#E03131" : "#F59F00";

  const tenantId = getTag(issue.tags, "tenant_id");
  const provider = getTag(issue.tags, "provider");
  const failureType = getTag(issue.tags, "failure_type");
  const environment = getTag(issue.tags, "environment") ?? "production";

  const tagParts: string[] = [`*env:* ${environment}`];
  if (tenantId) tagParts.push(`*tenant:* \`${tenantId}\``);
  if (provider) tagParts.push(`*provider:* ${provider}`);
  if (failureType) tagParts.push(`*failure_type:* \`${failureType}\``);

  const isRevoked = failureType === "connection_revoked";
  const headerText = isRevoked
    ? `${emoji} *Credencial muerta — ${issue.project.name}*`
    : `${emoji} *[${priority.toUpperCase()}] ${issue.title}*`;

  return {
    attachments: [
      {
        color,
        blocks: [
          {
            type: "section",
            text: {
              type: "mrkdwn",
              text: `${headerText}\n_${issue.culprit || issue.shortId}_`,
            },
          },
          {
            type: "section",
            fields: [
              { type: "mrkdwn", text: `*Proyecto:*\n${issue.project.name}` },
              { type: "mrkdwn", text: `*Ocurrencias:*\n${issue.count}x` },
              { type: "mrkdwn", text: `*Primer aviso:*\n${formatDate(issue.firstSeen)}` },
              { type: "mrkdwn", text: `*Último:*\n${formatDate(issue.lastSeen)}` },
            ],
          },
          {
            type: "section",
            text: { type: "mrkdwn", text: tagParts.join("  |  ") },
          },
          {
            type: "actions",
            elements: [
              {
                type: "button",
                text: { type: "plain_text", text: "Ver en Sentry" },
                url: issue.permalink,
                style: "danger",
              },
            ],
          },
        ],
      },
    ],
  };
}

function buildCompactMessage(issue: SentryIssue): object {
  return {
    attachments: [
      {
        color: "#F59F00",
        blocks: [
          {
            type: "section",
            text: {
              type: "mrkdwn",
              text: `🟡 *[MEDIUM]* <${issue.permalink}|${issue.title}> — ${issue.project.name}`,
            },
          },
        ],
      },
    ],
  };
}

// ── Worker entry point ─────────────────────────────────────────────────────

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    const body = await request.text();

    // Verify Sentry HMAC-SHA256 signature
    const signature = request.headers.get("sentry-hook-signature") ?? "";
    const valid = await verifySignature(env.SENTRY_WEBHOOK_SECRET, body, signature);
    if (!valid) {
      return new Response("Unauthorized", { status: 401 });
    }

    let payload: SentryWebhookPayload;
    try {
      payload = JSON.parse(body) as SentryWebhookPayload;
    } catch {
      return new Response("Bad Request", { status: 400 });
    }

    const { action, data } = payload;
    const issue = data?.issue;

    // Only process newly created issues
    if (!issue || action !== "created") {
      return new Response("OK", { status: 200 });
    }

    const priority = issue.priority ?? "medium";
    const failureType = getTag(issue.tags, "failure_type");
    const isHighPriority = priority === "high" || priority === "critical";
    const isConnectionRevoked = failureType === "connection_revoked";

    let slackPayload: object;

    if (isHighPriority || isConnectionRevoked) {
      slackPayload = buildFullMessage(issue);
    } else if (priority === "medium") {
      slackPayload = buildCompactMessage(issue);
    } else {
      // Low priority — silently ignore
      return new Response("OK", { status: 200 });
    }

    const slackRes = await fetch(env.SLACK_WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(slackPayload),
    });

    if (!slackRes.ok) {
      const errText = await slackRes.text();
      console.error(`Slack webhook failed (${slackRes.status}):`, errText);
      return new Response("Slack error", { status: 502 });
    }

    return new Response("OK", { status: 200 });
  },
};
