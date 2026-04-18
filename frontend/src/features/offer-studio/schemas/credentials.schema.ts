import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Credentials — credenciales duras verificables: título universitario,
 * matrícula profesional, colegiatura, cédula profesional, certificaciones
 * internacionales, acreditaciones sanitarias.
 *
 * Latam: para profesiones reguladas (salud, legal, contable, arquitectura)
 * la verificabilidad pública es TRUST-DEFINING. Colegios profesionales
 * clave por país:
 *   - Perú: CMP (médicos), CIP (ingenieros), CAL/CAP (abogados), COP (odontólogos)
 *   - México: cédula profesional SEP
 *   - Colombia: tarjeta profesional (varía por profesión)
 *   - Argentina: matrículas por colegio (CPACF abogados CABA, CPCCF, etc.)
 *   - Chile: colegio profesional + registro SII
 * Este bloque los aloja y expone link al registro público cuando existe.
 */
export const offerCredentialsSchema: SectionSchema = {
  key: "offer.credentials",
  scope: "offer_level",
  fields: [
    {
      id: "credentials",
      label: "Credenciales verificables",
      type: "array",
      path: "credentials",
      hint: "Cada credencial: tipo, institución, país, año, número de registro, link a verificación pública.",
      itemSchema: {
        description: "Una credencial individual (título, matrícula, certificación).",
        fields: [
          {
            id: "type",
            label: "Tipo de credencial",
            type: "enum",
            path: "type",
            required: true,
            options: [
              { value: "titulo_universitario", label: "Título universitario" },
              { value: "matricula_profesional", label: "Matrícula profesional" },
              { value: "colegiatura", label: "Colegiatura / colegio profesional" },
              { value: "cedula_profesional", label: "Cédula profesional (México)" },
              { value: "especializacion", label: "Especialización / posgrado" },
              { value: "maestria", label: "Maestría" },
              { value: "doctorado", label: "Doctorado" },
              { value: "certificacion_internacional", label: "Certificación internacional" },
              { value: "acreditacion_sanitaria", label: "Acreditación sanitaria / MINSA" },
              { value: "registro_tributario", label: "Registro tributario (SII, SUNAT, SAT, DGII)" },
              { value: "habilitacion", label: "Habilitación profesional" },
              { value: "sello_organismo", label: "Sello de organismo" },
              { value: "otro", label: "Otro" },
            ],
          },
          {
            id: "name",
            label: "Nombre de la credencial",
            type: "text",
            path: "name",
            required: true,
            placeholder: "Médico Cirujano · MBA Finanzas · Certified Scrum Master",
          },
          {
            id: "institution",
            label: "Institución emisora",
            type: "text",
            path: "institution",
            required: true,
            placeholder: "Universidad Peruana Cayetano Heredia · COP · SAT México",
          },
          {
            id: "country",
            label: "País",
            type: "text",
            path: "country",
            placeholder: "Perú, México, Colombia, Argentina, Chile",
          },
          {
            id: "year_obtained",
            label: "Año de obtención",
            type: "text",
            path: "year_obtained",
            placeholder: "2018",
          },
          {
            id: "credential_number",
            label: "Número de registro",
            type: "text",
            path: "credential_number",
            placeholder: "CMP 45781 · Cédula 8321092 · Matrícula T100F123",
            hint: "Solo si es público. Los colegios profesionales permiten verificación con este número.",
          },
          {
            id: "proof_url",
            label: "Link al registro público o diploma",
            type: "url",
            path: "proof_url",
            hint: "Link al padrón del colegio, registro profesional, o foto del diploma. Verificabilidad = trust real.",
          },
          {
            id: "expiry_date",
            label: "Fecha de vencimiento (si aplica)",
            type: "text",
            path: "expiry_date",
            placeholder: "2027-12-31",
            hint: "Certificaciones internacionales suelen expirar. Títulos universitarios no.",
          },
        ],
      },
    },
    {
      id: "regulatory_statements",
      label: "Declaraciones regulatorias",
      type: "textarea",
      path: "regulatory_statements",
      rows: 3,
      placeholder: "Consultorio habilitado por MINSA Perú (Res. N° 12345).\nRegistrado en COFEPRIS México.",
      hint: "Frases oficiales que confirman la habilitación del negocio ante organismos públicos.",
    },
    {
      id: "professional_associations",
      label: "Asociaciones profesionales activas",
      type: "textarea",
      path: "professional_associations",
      rows: 2,
      placeholder: "Miembro activo AAAM — Asociación Argentina de Abogados Mercantilistas\nColegio de Contadores de Lima",
      hint: "Membresías activas suman credibilidad. Una por línea.",
    },
  ],
};
