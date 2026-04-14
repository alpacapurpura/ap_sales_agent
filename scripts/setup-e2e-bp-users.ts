/**
 * One-time setup script: create E2E test users in Clerk for buyer persona tests.
 *
 * Uses the Clerk Backend REST API directly via fetch — no package dependency.
 * Creates 4 test users idempotently. Each gets publicMetadata.tenant_id set
 * to E2E_TENANT_ID so TenantGuard lets them through.
 *
 * Usage:
 *   cd /home/chris/AISALESHT && node --input-type=module < scripts/setup-e2e-bp-users.mjs
 *   OR run via the frontend package (which has dotenv):
 *   cd /home/chris/AISALESHT && node scripts/setup-e2e-bp-users.mjs
 *
 * Actually, just run:
 *   node -e "$(cat scripts/setup-e2e-bp-users.js)"
 *
 * Requires: CLERK_SECRET_KEY and E2E_TENANT_ID in root .env
 */

// This file is TS for IDE support, but executed as Node.js ES module
// Run from the AISALESHT root after sourcing .env:
//   set -a && source .env && set +a && node --experimental-vm-modules scripts/setup-e2e-bp-users.cjs

import { config } from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
config({ path: path.resolve(__dirname, '../.env') });

const CLERK_SECRET_KEY = process.env.CLERK_SECRET_KEY;
const E2E_TENANT_ID = process.env.E2E_TENANT_ID;
const CLERK_API = 'https://api.clerk.com/v1';

if (!CLERK_SECRET_KEY) {
  console.error('❌ CLERK_SECRET_KEY not set');
  process.exit(1);
}
if (!E2E_TENANT_ID) {
  console.error('❌ E2E_TENANT_ID not set');
  process.exit(1);
}

const SHARED_PASSWORD = 'E2eBpTest!2026';

const USERS = [
  {
    email: 'e2e-bp-ideal@nicolify.com',
    username: 'e2e-bp-ideal',
    first_name: 'Ideal',
    last_name: 'E2E',
    description: 'Happy path — detailed, cooperative',
  },
  {
    email: 'e2e-bp-vague@nicolify.com',
    username: 'e2e-bp-vague',
    first_name: 'Vague',
    last_name: 'E2E',
    description: 'Vague user — minimal answers',
  },
  {
    email: 'e2e-bp-expert@nicolify.com',
    username: 'e2e-bp-expert',
    first_name: 'Expert',
    last_name: 'E2E',
    description: 'Expert dumper — all info at once',
  },
  {
    email: 'e2e-bp-confused@nicolify.com',
    username: 'e2e-bp-confused',
    first_name: 'Confused',
    last_name: 'E2E',
    description: 'Contradictory user',
  },
];

async function clerkFetch(method: string, endpoint: string, body?: unknown): Promise<unknown> {
  const res = await fetch(`${CLERK_API}${endpoint}`, {
    method,
    headers: {
      Authorization: `Bearer ${CLERK_SECRET_KEY}`,
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Clerk API error ${res.status}: ${text}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

async function findUserByEmail(email: string): Promise<string | null> {
  const result = await clerkFetch('GET', `/users?email_address=${encodeURIComponent(email)}`) as Array<{ id: string }>;
  if (result.length > 0) return result[0].id;
  return null;
}

async function setupUser(spec: typeof USERS[0]): Promise<void> {
  console.log(`\n📋 ${spec.description}`);

  const existingId = await findUserByEmail(spec.email);

  if (existingId) {
    console.log(`  ✅ Already exists: ${spec.email} (${existingId})`);
    await clerkFetch('PATCH', `/users/${existingId}/metadata`, {
      public_metadata: { tenant_id: E2E_TENANT_ID },
    });
    console.log(`  ✅ Tenant metadata confirmed: ${E2E_TENANT_ID}`);
    return;
  }

  const user = await clerkFetch('POST', '/users', {
    email_address: [spec.email],
    username: spec.username,
    first_name: spec.first_name,
    last_name: spec.last_name,
    password: SHARED_PASSWORD,
    public_metadata: { tenant_id: E2E_TENANT_ID },
  }) as { id: string };

  console.log(`  ✅ Created: ${spec.email} (${user.id})`);
}

async function main(): Promise<void> {
  console.log('🚀 Setting up E2E Buyer Persona test users in Clerk');
  console.log(`   Tenant: ${E2E_TENANT_ID}`);
  console.log(`   Password: ${SHARED_PASSWORD}`);

  for (const spec of USERS) {
    try {
      await setupUser(spec);
    } catch (err) {
      console.error(`  ❌ Failed for ${spec.email}:`, err instanceof Error ? err.message : err);
    }
  }

  console.log('\n✅ Done!');
  console.log(`   Password for all users: ${SHARED_PASSWORD}`);
}

main();
