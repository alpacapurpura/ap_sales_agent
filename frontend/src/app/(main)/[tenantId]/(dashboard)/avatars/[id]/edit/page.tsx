"use client";

import { useParams, useSearchParams } from "next/navigation";

import { AvatarEditView } from "@/features/brand/components/views/AvatarEditView";

export default function EditAvatarPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  return (
    <AvatarEditView
      avatarId={params?.id as string}
      callbackUrl={searchParams?.get("callbackUrl") ?? null}
    />
  );
}
