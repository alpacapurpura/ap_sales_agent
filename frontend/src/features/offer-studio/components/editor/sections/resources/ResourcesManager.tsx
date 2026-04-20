"use client";

import { ResourcesForm } from "./ResourcesForm";

import type { ResourcesFormProps } from "./ResourcesForm";

/**
 *
 */
export function ResourcesManager(props: ResourcesFormProps) {
  // In the future, this manager can handle fetching external resources or templates
  // For now, it passes props through to the form
  return <ResourcesForm {...props} />;
}
