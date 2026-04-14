import { Lead, LeadStatus, LeadTemperature } from "../types";

export const MOCK_LEADS: Lead[] = [
  // 1. Empty (new lead)
  {
    id: "lead_1",
    status: "new",
    temperature: "cold",
    score: 10,
    ai_memory: "",
    customer: {
      id: "cust_1",
      full_name: "New User",
      // No email, phone, avatar, or social handle
    },
  },
  // 2. Partial (missing email)
  {
    id: "lead_2",
    status: "contacted",
    temperature: "warm",
    score: 45,
    ai_memory: "User showed interest in pricing but has not provided email yet.",
    customer: {
      id: "cust_2",
      full_name: "Alice Partial",
      phone: "+1-555-0102",
      avatar_url: "https://i.pravatar.cc/150?u=cust_2",
      social_handle: "@alice_p",
      // Missing email
    },
  },
  // 3. Full (rich data)
  {
    id: "lead_3",
    status: "qualified",
    temperature: "hot",
    score: 95,
    ai_memory: "High intent. Budget approved. Decision maker. Ready to close.",
    customer: {
      id: "cust_3",
      full_name: "Bob Fullstack",
      email: "bob.fullstack@example.com",
      phone: "+1-555-0103",
      avatar_url: "https://i.pravatar.cc/150?u=cust_3",
      social_handle: "@bobby_full",
    },
  },
  // 4. Extreme (long texts)
  {
    id: "lead_4",
    status: "proposal",
    temperature: "warm",
    score: 60,
    ai_memory:
      "This user has a very specific set of requirements involving multiple integrations with legacy systems. They mentioned needing support for COBOL, Fortran, and Assembly. The conversation went on for 2 hours about the nuances of mainframe architecture. They are very detailed-oriented and expect a comprehensive proposal covering all edge cases.",
    customer: {
      id: "cust_4",
      full_name: "Maximilian Theodosius Alexander The Third of the House of Longnames",
      email: "maximilian.theodosius.alexander.iii@very-long-domain-name-example.co.uk",
      phone: "+1-555-0104",
      avatar_url: "https://i.pravatar.cc/150?u=cust_4",
      social_handle: "@max_the_third_official_account",
    },
  },
  // 5. Error (invalid state)
  {
    id: "lead_5",
    status: "unknown_status" as LeadStatus, // Forced invalid state for testing error handling
    temperature: "freezing" as LeadTemperature, // Invalid temperature
    score: -100, // Invalid score
    ai_memory: undefined,
    customer: {
      id: "cust_5",
      full_name: "", // Empty name (should be invalid)
      email: "invalid-email", // Malformed email
    },
  },
];
