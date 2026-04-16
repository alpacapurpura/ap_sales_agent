"use client";

import { GalleryForm } from "./GalleryForm";

import type { GalleryFormProps } from "./GalleryForm";

export function GalleryManager(props: GalleryFormProps) {
  // In the future, this manager can handle fetching brand visuals or stock images
  // For now, it passes props through to the form
  return <GalleryForm {...props} />;
}
