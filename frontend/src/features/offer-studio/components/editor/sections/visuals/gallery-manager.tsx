"use client";

import { GalleryForm } from "./gallery-form";

import type { GalleryFormProps } from "./gallery-form";

export function GalleryManager(props: GalleryFormProps) {
  // In the future, this manager can handle fetching brand visuals or stock images
  // For now, it passes props through to the form
  return <GalleryForm {...props} />;
}
