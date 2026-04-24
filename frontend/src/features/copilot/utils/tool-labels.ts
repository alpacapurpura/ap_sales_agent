const TOOL_LABELS_ES: Record<string, string> = {
  extract_from_url: "Analizando página web",
  extract_from_doc: "Leyendo documento",
  read_document: "Leyendo documento",
  propose_field_updates: "Proponiendo cambios",
  search_web: "Buscando en la web",
  generate_copy: "Generando contenido",
  generate_image: "Generando imagen",
  update_field: "Actualizando campo",
  navigate: "Navegando",
};

/**
 *
 */
export function humanizeToolName(tool: string): string {
  if (TOOL_LABELS_ES[tool]) return TOOL_LABELS_ES[tool];
  return tool
    .replace(/^_+/, "")
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((w, i) => (i === 0 ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ");
}
