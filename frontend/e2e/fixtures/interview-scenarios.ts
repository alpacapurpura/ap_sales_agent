/**
 * Scripted scenario definitions for buyer persona interview E2E tests.
 *
 * Each scenario represents a different human user archetype:
 * - A series of scripted responses simulating that user's behavior
 * - Quality thresholds for asserting the resulting persona
 * - Metadata for test labeling
 *
 * Responses are in Spanish (the interview runs in Spanish).
 * Checkpoint confirmations are interleaved where expected.
 */

import type { ScenarioThresholds } from '../fixtures/persona-evaluator';

export interface InterviewScenario {
  id: string;
  name: string;
  description: string;
  personaName: string;
  /** Ordered list of messages the "user" sends during the interview. */
  responses: string[];
  /** Messages to confirm checkpoints when they appear (cycled if multiple checkpoints). */
  checkpointConfirmation: string;
  thresholds: ScenarioThresholds;
}

// ── Scenario 1: The Ideal User ───────────────────────────────────────────────
// Fundadora de coaching para mujeres profesionistas. Conoce bien a sus clientes.
// Respuestas detalladas y cooperativas. Happy path.

export const SCENARIO_IDEAL: InterviewScenario = {
  id: 'ideal',
  name: 'Usuario Ideal',
  description: 'Founder with deep knowledge of their customer — detailed, cooperative responses',
  personaName: 'María Emprendedora',
  responses: [
    'Le quiero llamar María Emprendedora',
    'Son mujeres de 30 a 45 años, viven en Ciudad de México y Monterrey, profesionistas con ingresos de 30 a 50 mil pesos mensuales, estudios universitarios, la mayoría casadas con hijos',
    'Valoran el crecimiento personal y la independencia económica. Creen que merecen ganar más. Consumen Instagram y YouTube. Son perfeccionistas y muy organizadas',
    'Su mayor dolor es sentir que no avanzan profesionalmente a pesar de su preparación. Les frustra ver que otros con menos experiencia ganan más. Lo que realmente quieren es tener un negocio propio que les dé libertad de tiempo y dinero',
    'Dicen que no tienen tiempo, pero la objeción real es miedo al fracaso y al qué dirán. Compran cuando ven testimonios reales de mujeres como ellas. No son mi cliente las que solo buscan dinero rápido sin esfuerzo',
    'Están en Instagram todo el día, buscan en Google cuando tienen un problema específico, y toman decisiones después de ver un webinar o una sesión gratuita de demostración',
  ],
  checkpointConfirmation: 'Perfecto, sigamos con el siguiente bloque',
  thresholds: {
    minCompletenessScore: 45,
    minSectionsPopulated: 5,
  },
};

// ── Scenario 2: The Vague User ───────────────────────────────────────────────
// Emprendedor de servicios. Respuestas mínimas, monosílabos.
// El AI debería hacer preguntas progresivamente más específicas.

export const SCENARIO_VAGUE: InterviewScenario = {
  id: 'vague',
  name: 'Usuario Vago',
  description: 'Solopreneur with minimal, one-word responses — AI should probe deeper',
  personaName: 'Cliente Ideal',
  responses: [
    'Cliente ideal',
    'Gente normal',
    'Jóvenes, creo',
    'No sé, de todo tipo',
    'Sí, eso',
    'Que les falta dinero',
    'No sé qué más decirte',
    'Sí',
    'Redes sociales',
    'Sí, está bien así',
    'Perfecto',
  ],
  checkpointConfirmation: 'Sí, está bien',
  thresholds: {
    minCompletenessScore: 10,
    minSectionsPopulated: 2,
    maxTotalMessages: 35,
  },
};

// ── Scenario 3: Expert Dumper ────────────────────────────────────────────────
// CMO de SaaS B2B. Vuelca toda la información en 1-2 mensajes masivos.
// El AI debería capturar múltiples campos del primer mensaje.

export const SCENARIO_EXPERT: InterviewScenario = {
  id: 'expert',
  name: 'Experto Dumper',
  description: 'CMO who dumps all info at once — AI should extract multiple fields per message',
  personaName: 'Director de Marketing B2B',
  responses: [
    'Mi buyer persona se llama Director de Marketing B2B. Es el Director o VP de Marketing de empresas SaaS B2B de entre 50 y 200 empleados en Latinoamérica, con presupuesto de marketing de 50 a 200 mil USD anuales. Son hombres de 35 a 50 años, tienen MBA, viven en Ciudad de México, Bogotá o Buenos Aires. Valoran profundamente los datos y el ROI, son muy analíticos, consumen podcasts de marketing como Marketing School y Duct Tape Marketing, y leen blogs como HubSpot y Gartner. Su mayor dolor es que no pueden demostrar el ROI de marketing a la junta directiva y se sienten bajo presión constante de mostrar resultados. Lo que realmente desean es un sistema que les dé visibilidad total del pipeline y les ahorre tiempo en reportes. Su objeción principal es que ya tienen demasiadas herramientas y no quieren más complejidad. El trigger que los hace comprar es cuando pierden un deal importante y descubren que fue por falta de visibilidad de datos. Sus anti-patterns son los marketers que quieren resultados sin invertir en data. Están principalmente en LinkedIn, evalúan herramientas en G2 y Capterra, y su journey es: ven un post en LinkedIn, buscan alternativas en Google, piden demo, evalúan durante 3 meses con el equipo técnico, y finalmente aprueban la compra con el CFO.',
    'Sí, está completamente correcto, puedes avanzar',
    'Perfecto, sigamos',
    'Todo correcto, completa la entrevista',
  ],
  checkpointConfirmation: 'Sí, todo correcto, avanza',
  thresholds: {
    minCompletenessScore: 60,
    minSectionsPopulated: 7,
    maxTotalMessages: 15,
  },
};

// ── Scenario 4: Contradictory User ──────────────────────────────────────────
// Ecommerce de moda. Se contradice — el AI debería detectar y resolver.

export const SCENARIO_CONFUSED: InterviewScenario = {
  id: 'confused',
  name: 'Usuario Contradictorio',
  description: 'Ecommerce founder who contradicts themselves — AI should use clarify tool',
  personaName: 'Compradora de Moda',
  responses: [
    'La quiero llamar Compradora de Moda Online',
    // Block 1: demographics — contradiction about age
    'Son mujeres jóvenes de 20 a 30 años que viven en ciudades grandes',
    'Bueno, en realidad pensándolo bien, la mayoría de mis mejores clientes tienen entre 40 y 55 años y son profesionistas establecidas',
    'Exacto, eso es más preciso, las de 40-55',
    // Block 2: psychographics
    'Son muy aspiracionales, les importa la imagen. Nivel socioeconómico alto, gastan sin pensar',
    'Bueno... muchas sí buscan descuentos y ofertas, no son tan de gasto libre',
    'Las que realmente compran son las que buscan calidad, no las de oferta',
    // Blocks 3-5: pain/desire/objections/channels
    'Su dolor es no encontrar ropa de calidad que les quede bien a su tipo de cuerpo y edad',
    'Quieren verse elegantes y contemporáneas sin parecer que se están esforzando demasiado',
    'No tienen objeciones en realidad, a todas les encanta mi ropa',
    'Bueno sí, dicen que es cara y que hay mucha competencia online',
    'El precio es una objeción real, pero cuando ven la calidad lo justifican',
    'Están en Instagram y Pinterest, buscan en Google "ropa para mujeres maduras elegantes", y compran cuando reciben una recomendación de una influencer o amiga',
    'Sí, está bien todo',
  ],
  checkpointConfirmation: 'Sí, con las aclaraciones que diste, está correcto',
  thresholds: {
    minCompletenessScore: 30,
    minSectionsPopulated: 4,
  },
};

// ── Scenario 5: Multi-Persona ────────────────────────────────────────────────
// Agencia de marketing. Crea 2 personas distintas en una misma sesión.
// Verifica que no hay conflicto de sesiones entre personas.

export const SCENARIO_MULTI_PERSONA_FIRST: InterviewScenario = {
  id: 'multi-p1',
  name: 'Multi-Persona (Primera)',
  description: 'First of two personas — quick completion to test session isolation',
  personaName: 'Emprendedor Digital',
  responses: [
    'Primera persona: Emprendedor Digital',
    'Hombres de 28 a 40 años en Latinoamérica, emprendedores de negocios online, ingresos de 2 a 10 mil dólares mensuales',
    'Valoran la libertad y la autonomía. Consumen contenido en YouTube y podcasts. Son autodidactas y optimistas',
    'Su dolor es la incertidumbre de ingresos variables y la soledad del emprendimiento',
    'No tienen tiempo ni dinero para grandes inversiones. Compran cuando confían en el creador del contenido',
    'YouTube, Instagram, grupos de Facebook. Descubren por contenido gratuito, compran después de seguirte por meses',
    'Todo bien, avancemos',
    'Correcto',
  ],
  checkpointConfirmation: 'Correcto, avancemos',
  thresholds: {
    minCompletenessScore: 30,
    minSectionsPopulated: 4,
  },
};

export const SCENARIO_MULTI_PERSONA_SECOND: InterviewScenario = {
  id: 'multi-p2',
  name: 'Multi-Persona (Segunda)',
  description: 'Second persona after first interview completed — tests no session conflict',
  personaName: 'Directora Corporativa',
  responses: [
    'Segunda persona: Directora Corporativa',
    'Mujeres de 35 a 55 años, directoras o gerentes en empresas medianas, ingresos mayores a 80 mil pesos mensuales, en CDMX o Monterrey',
    'Valoran el profesionalismo, los resultados tangibles y el retorno de inversión. Consumen LinkedIn y newsletters especializadas',
    'Dolor: demasiado trabajo y poco tiempo para desarrollar a su equipo. Deseo: resultados sin tener que supervisar cada detalle',
    'Objeción: presupuesto limitado y necesidad de aprobar con el equipo. Trigger: cuando pierden un talento valioso',
    'LinkedIn principalmente, decisión basada en referencias y casos de éxito documentados',
    'Sí, correcto',
  ],
  checkpointConfirmation: 'Sí, correcto',
  thresholds: {
    minCompletenessScore: 30,
    minSectionsPopulated: 4,
  },
};

// ── Scenario 6: Abandonment ──────────────────────────────────────────────────
// Responde 2 preguntas y sale del interview.
// Verifica que la persona shell queda guardada y no hay crash.

export const SCENARIO_ABANDON: InterviewScenario = {
  id: 'abandon',
  name: 'Abandono',
  description: 'User starts interview, answers 2 questions, then exits via Focus bar',
  personaName: 'Persona Incompleta',
  responses: [
    'Quiero llamarla Persona Incompleta',
    'Son adultos de 25 a 45 años en México',
    // Test will exit after these 2 responses — no more scripted messages needed
  ],
  checkpointConfirmation: 'Perfecto',
  thresholds: {
    minCompletenessScore: 0, // Incomplete by design
    minSectionsPopulated: 0,
  },
};

// ── All scenarios ────────────────────────────────────────────────────────────

export const ALL_SCENARIOS = [
  SCENARIO_IDEAL,
  SCENARIO_VAGUE,
  SCENARIO_EXPERT,
  SCENARIO_CONFUSED,
  SCENARIO_MULTI_PERSONA_FIRST,
  SCENARIO_ABANDON,
] as const;
