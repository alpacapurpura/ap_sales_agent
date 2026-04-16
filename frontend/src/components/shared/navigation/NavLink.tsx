"use client";

import { Loader2 } from "lucide-react";
import Link, { type LinkProps } from "next/link";
import { forwardRef, type AnchorHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

import { useNavigation } from "./NavigationContext";

interface NavLinkProps
  extends Omit<AnchorHTMLAttributes<HTMLAnchorElement>, keyof LinkProps>, LinkProps {
  showLoadingIcon?: boolean;
  loadingClassName?: string;
}

export const NavLink = forwardRef<HTMLAnchorElement, NavLinkProps>(function NavLink(
  { href, onClick, className, showLoadingIcon, loadingClassName, children, ...rest },
  ref,
) {
  const { isNavigating, pendingHref, navigate } = useNavigation();
  const hrefString = typeof href === "string" ? href : (href.pathname ?? "");
  const isThisLoading = isNavigating && pendingHref === hrefString;

  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (isNavigating) {
      e.preventDefault();
      return;
    }
    onClick?.(e);
    if (e.defaultPrevented) return;
    // Skip for modified clicks (new tab, etc.) — let browser handle natively
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    navigate(hrefString);
  };

  return (
    <Link
      ref={ref}
      href={href}
      onClick={handleClick}
      className={cn(
        className,
        isNavigating && "pointer-events-none",
        isThisLoading && loadingClassName,
      )}
      aria-busy={isThisLoading || undefined}
      {...rest}
    >
      {children}
      {showLoadingIcon && isThisLoading && (
        <Loader2 className="ml-auto h-4 w-4 animate-spin shrink-0" />
      )}
    </Link>
  );
});
