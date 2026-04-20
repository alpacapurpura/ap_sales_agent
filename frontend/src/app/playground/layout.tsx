import { redirect } from "next/navigation";

/**
 *
 */
export default function PlaygroundLayout({ children }: { children: React.ReactNode }) {
  if (process.env.NODE_ENV === "production") {
    redirect("/");
  }
  return <>{children}</>;
}
