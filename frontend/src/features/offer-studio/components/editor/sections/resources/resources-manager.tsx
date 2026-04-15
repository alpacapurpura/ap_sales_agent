"use client";

import { ResourcesForm } from "./resources-form";

import type { ResourcesFormProps } from "./resources-form";

export function ResourcesManager(props: ResourcesFormProps) {
  // In the future, this manager can handle fetching external resources or templates
  // For now, it passes props through to the form
  return <ResourcesForm {...props} />;
}
