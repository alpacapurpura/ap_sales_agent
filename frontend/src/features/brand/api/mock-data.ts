import { BrandSettings } from "../types";

export const MOCK_BRAND_SETTINGS: BrandSettings = {
    identity: {
        brand_name: "TechNova Solutions",
        industry: "Tecnología e Innovación"
    },
    strategy: {
        value_proposition: "Transformamos negocios mediante soluciones de IA ética y sostenible.",
        target_audience: "Empresas medianas y grandes en sector financiero y salud.",
        differentiation: "Enfoque propietario en IA explicable y soporte 24/7.",
        offerings: [
            "Consultoría de IA",
            "Automatización de Procesos",
            "Análisis Predictivo"
        ],
        unique_value_proposition: "IA que puedes entender y controlar.",
        competitors: [
            { id: "1", name: "Legacy Corp", differentiation: "Más lentos, tecnología antigua" },
            { id: "2", name: "FastAI Inc", differentiation: "Rápidos pero sin soporte personalizado" }
        ],
        methodology_name: "Ciclo Nova",
        methodology_description: "Un proceso iterativo de 4 pasos para garantizar resultados.",
        methodology_pillars: [
            { id: "1", title: "Descubrimiento", description: "Entendemos tu negocio a fondo." },
            { id: "2", title: "Diseño", description: "Arquitectura a medida." },
            { id: "3", title: "Implementación", description: "Desarrollo ágil y seguro." },
            { id: "4", title: "Optimización", description: "Mejora continua basada en datos." }
        ]
    },
    story: {
        origin_story: "Fundada en 2020 por tres ingenieros que querían democratizar la IA.",
        mission: "Hacer que la inteligencia artificial sea accesible y segura para todos.",
        vision: "Un mundo donde la tecnología potencia la creatividad humana sin reemplazarla.",
        milestones: [
            { id: "1", year: "2020", title: "Fundación en un garaje." },
            { id: "2", year: "2021", title: "Primer cliente Fortune 500." },
            { id: "3", year: "2023", title: "Expansión a Europa." }
        ]
    },
    team: [
        {
            id: "1",
            name: "Ana García",
            role: "CEO & Co-fundadora",
            bio: "Visionaria tecnológica con 15 años de experiencia en Silicon Valley.",
            is_primary_voice: true,
            headshot_url: "https://i.pravatar.cc/150?u=ana",
            communication_style: "Inspirador y directo",
            personal_linkedin: "https://linkedin.com/in/anagarcia",
            gallery: []
        },
        {
            id: "2",
            name: "Carlos Ruiz",
            role: "CTO",
            bio: "Arquitecto de sistemas experto en escalabilidad.",
            is_primary_voice: false,
            headshot_url: "https://i.pravatar.cc/150?u=carlos",
            gallery: []
        }
    ],
    visuals: {
        primary_color: "#3b82f6",
        accent_color: "#10b981",
        background_color: "#ffffff",
        text_primary_color: "#1f2937",
        text_on_primary: "#ffffff",
        font_heading: "Inter",
        font_body: "Roboto",
        style_preset: "modern",
        design_style: "Minimalista y Tecnológico",
        usage_guidelines: [
            "Usar el logo siempre con espacio de respeto.",
            "No combinar más de 3 colores principales."
        ],
        logo_url: "https://placehold.co/400x100?text=TechNova",
        images: [
            "https://placehold.co/600x400?text=Office",
            "https://placehold.co/600x400?text=Meeting"
        ],
        logos: {
            primary: "https://placehold.co/400x100?text=TechNova+Primary",
            secondary: "https://placehold.co/100x100?text=TN",
            dark_mode: "https://placehold.co/400x100?text=TechNova+Dark",
            light_mode: "https://placehold.co/400x100?text=TechNova+Light"
        }
    },
    contact: {
        support_email: "soporte@technova.com",
        sales_email: "ventas@technova.com",
        phone: "+34 912 345 678",
        whatsapp: "+34 600 000 000",
        address: "Calle Innovación 123, Madrid, España",
        social_linkedin: "https://linkedin.com/company/technova",
        social_twitter: "https://twitter.com/technova",
        social_instagram: "https://instagram.com/technova",
        testimonials_url: "https://technova.com/casos-exito"
    },
    testimonials: [
        {
            id: "1",
            type: "text",
            content: "TechNova transformó nuestra operativa en tiempo récord.",
            author_name: "Luis Méndez",
            author_role: "Director de Operaciones, Banco Futuro",
            rating: 5,
            author_avatar: "https://i.pravatar.cc/150?u=luis"
        },
        {
            id: "2",
            type: "text",
            content: "Increíble equipo y tecnología de punta.",
            author_name: "María López",
            author_role: "CEO, StartUp X",
            rating: 4
        }
    ],
    authority_vault: [
        {
            id: "1",
            entity_name: "Forbes",
            type: "press",
            context: "Mención en 'Top 50 Startups de IA'",
            proof_url: "https://forbes.com/article/technova",
            logo_url: "https://placehold.co/200x100?text=Forbes"
        },
        {
            id: "2",
            entity_name: "ISO 27001",
            type: "certification",
            context: "Certificación de seguridad de la información",
            proof_url: "https://iso.org/cert/12345"
        }
    ]
};
