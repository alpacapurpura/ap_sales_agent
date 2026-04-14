#!/usr/bin/env node
/**
 * Create E2E test users in Clerk for buyer persona tests.
 *
 * Usage (from repo root):
 *   node scripts/setup-e2e-bp-users.js
 *
 * Or source .env first if variables not in environment:
 *   env $(cat .env | grep -v '^#' | xargs) node scripts/setup-e2e-bp-users.js
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

// ── Load .env manually ───────────────────────────────────────────────────────

function loadEnv(envPath) {
  try {
    const lines = fs.readFileSync(envPath, 'utf8').split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIdx = trimmed.indexOf('=');
      if (eqIdx < 0) continue;
      const key = trimmed.slice(0, eqIdx).trim();
      let val = trimmed.slice(eqIdx + 1).trim();
      // Strip surrounding quotes
      if ((val.startsWith('"') && val.endsWith('"')) ||
          (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      if (!process.env[key]) process.env[key] = val;
    }
  } catch {
    // .env not found — rely on process.env
  }
}

loadEnv(path.resolve(__dirname, '../.env'));

const CLERK_SECRET_KEY = process.env.CLERK_SECRET_KEY;
const E2E_TENANT_ID = process.env.E2E_TENANT_ID;

if (!CLERK_SECRET_KEY) { console.error('❌ CLERK_SECRET_KEY not set'); process.exit(1); }
if (!E2E_TENANT_ID) { console.error('❌ E2E_TENANT_ID not set'); process.exit(1); }

const SHARED_PASSWORD = 'E2eBpTest!2026';
const CLERK_API_HOST = 'api.clerk.com';

// ── Clerk API wrapper ────────────────────────────────────────────────────────

function clerkRequest(method, endpoint, body) {
  return new Promise((resolve, reject) => {
    const bodyStr = body ? JSON.stringify(body) : '';
    const opts = {
      hostname: CLERK_API_HOST,
      path: `/v1${endpoint}`,
      method,
      headers: {
        Authorization: `Bearer ${CLERK_SECRET_KEY}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(bodyStr),
      },
    };
    const req = https.request(opts, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 204) return resolve(null);
        try {
          const parsed = JSON.parse(data);
          if (res.statusCode >= 400) return reject(new Error(`Clerk ${res.statusCode}: ${data}`));
          resolve(parsed);
        } catch {
          reject(new Error(`Parse error: ${data}`));
        }
      });
    });
    req.on('error', reject);
    if (bodyStr) req.write(bodyStr);
    req.end();
  });
}

async function findUserByEmail(email) {
  const result = await clerkRequest('GET', `/users?email_address=${encodeURIComponent(email)}`);
  if (Array.isArray(result) && result.length > 0) return result[0].id;
  // result may be {data: [...]} depending on API version
  if (result && Array.isArray(result.data) && result.data.length > 0) return result.data[0].id;
  return null;
}

const USERS = [
  { email: 'e2e-bp-ideal@nicolify.com', username: 'e2e-bp-ideal', first_name: 'Ideal', last_name: 'E2E', desc: 'Happy path' },
  { email: 'e2e-bp-vague@nicolify.com', username: 'e2e-bp-vague', first_name: 'Vague', last_name: 'E2E', desc: 'Vague user' },
  { email: 'e2e-bp-expert@nicolify.com', username: 'e2e-bp-expert', first_name: 'Expert', last_name: 'E2E', desc: 'Expert dumper' },
  { email: 'e2e-bp-confused@nicolify.com', username: 'e2e-bp-confused', first_name: 'Confused', last_name: 'E2E', desc: 'Contradictory' },
];

async function setupUser(spec) {
  console.log(`\n📋 ${spec.desc}: ${spec.email}`);
  const existingId = await findUserByEmail(spec.email);

  if (existingId) {
    console.log(`  ✅ Already exists (${existingId})`);
    await clerkRequest('PATCH', `/users/${existingId}/metadata`, {
      public_metadata: { tenant_id: E2E_TENANT_ID },
    });
    console.log(`  ✅ tenant_id set to ${E2E_TENANT_ID}`);
    return;
  }

  const user = await clerkRequest('POST', '/users', {
    email_address: [spec.email],
    username: spec.username,
    first_name: spec.first_name,
    last_name: spec.last_name,
    password: SHARED_PASSWORD,
    public_metadata: { tenant_id: E2E_TENANT_ID },
  });

  console.log(`  ✅ Created (${user.id})`);
}

async function main() {
  console.log('🚀 Setting up E2E Buyer Persona test users in Clerk');
  console.log(`   Tenant: ${E2E_TENANT_ID}`);
  console.log(`   Password: ${SHARED_PASSWORD}\n`);

  for (const spec of USERS) {
    try {
      await setupUser(spec);
    } catch (err) {
      console.error(`  ❌ ${spec.email}: ${err.message}`);
    }
  }

  console.log('\n✅ Done!');
}

main().catch(console.error);
