// Components
export { ContactsPageClient } from "./components/ContactsPageClient";
export { ContactDetailContent } from "./components/ContactDetailContent";
export { ContactFiltersPanel } from "./components/ContactFiltersPanel";
export { IdentityList } from "./components/IdentityList";
export { LifecycleStageChip } from "./components/LifecycleStageChip";
export { ScoreBadge } from "./components/ScoreBadge";
export { SelectedContactsBar } from "./components/SelectedContactsBar";

// Types
export type {
  ContactFilterParams,
  ContactFilterField,
  ContactListItem,
  ContactDetail,
  ContactIdentity,
  PaginatedResponse,
  SelectedContactsBarAction,
  LifecycleStage,
} from "./types";
export { CONTACT_FILTER_FIELDS, contactFilterParamsSchema, lifecycleStageSchema } from "./types";

// API hooks
export { useContactsQuery } from "./api/use-contacts-query";
export type { UseContactsQueryParams } from "./api/use-contacts-query";
export { useContactDetailQuery } from "./api/use-contact-detail-query";
export { useFilterSchemaQuery } from "./api/use-filter-schema-query";
export type { FilterFieldMeta, FilterSchemaResponse } from "./api/use-filter-schema-query";

// Utils
export { parseFiltersFromSearchParams, filtersToSearchParams, clampInt } from "./utils/url-state";
