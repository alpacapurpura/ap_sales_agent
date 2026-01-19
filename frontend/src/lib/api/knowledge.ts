// Placeholder for API client
// Ideally, this would use axios or fetch to talk to the FastAPI backend
// e.g. GET http://localhost:8000/api/admin/safety-rules

export interface SafetyRule {
    id: string;
    pattern: string;
    replacement: string;
    category: "financial" | "pii" | "business_secret" | "system";
    scope: "BRAND" | "PRODUCT";
    product_id?: string;
    description?: string;
    context_instruction?: string;
    is_active: boolean;
}

export const KnowledgeAPI = {
    getSafetyRules: async (scope: string, productId?: string): Promise<SafetyRule[]> => {
        // Mock implementation
        return [];
    },
    
    createSafetyRule: async (rule: Partial<SafetyRule>) => {
        // Mock implementation
    },
    
    deleteSafetyRule: async (id: string) => {
        // Mock implementation
    }
}
