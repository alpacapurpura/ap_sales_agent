/**
 * GLOBAL MOCK CONFIGURATION
 * 
 * This file centralizes the mock data toggle for the entire application.
 * It allows switching between Real API and Mock Data for development purposes.
 * 
 * @const ENABLE_MOCKS
 * - true: Use Mock Data (local fixtures)
 * - false: Use Real API (backend connection)
 * 
 * NOTE: This is forced to FALSE in production builds to prevent accidental mock usage.
 */

const IS_DEVELOPMENT = process.env.NODE_ENV === "development";

// GLOBAL SWITCH: Change this manually to toggle between MOCK and REAL data in dev.
// You can also control this via env variable NEXT_PUBLIC_ENABLE_MOCKS="true"
const MANUAL_SWITCH = false; 

export const ENABLE_MOCKS = IS_DEVELOPMENT && (
    MANUAL_SWITCH || 
    process.env.NEXT_PUBLIC_ENABLE_MOCKS === "true"
);

if (ENABLE_MOCKS && typeof window !== "undefined") {
    console.warn(
        "%c⚠️ APPLICATION RUNNING IN MOCK MODE ⚠️\nData is being simulated locally.", 
        "background: #f59e0b; color: black; padding: 4px; border-radius: 4px; font-weight: bold;"
    );
}
