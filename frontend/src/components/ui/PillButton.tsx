"use client";

import type { ReactNode } from "react";
import { motion, type HTMLMotionProps } from "framer-motion";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export interface PillButtonProps
  extends Omit<HTMLMotionProps<"button">, "children"> {
  selected?: boolean;
  children?: ReactNode;
}

/**
 * A rounded, tappable choice control used in place of radio buttons /
 * checkboxes throughout the onboarding wizard. Selection state is shown
 * through color + a small check, not a border-only change, so it reads
 * clearly at a glance and on mobile.
 */
export function PillButton({
  selected,
  className,
  children,
  ...props
}: PillButtonProps) {
  return (
    <motion.button
      type="button"
      whileTap={{ scale: 0.96 }}
      aria-pressed={selected}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-5 py-2.5 text-sm font-medium transition-colors",
        selected
          ? "border-primary bg-primary-soft text-primary"
          : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50",
        className
      )}
      {...props}
    >
      {selected && <Check className="h-3.5 w-3.5" strokeWidth={3} />}
      {children}
    </motion.button>
  );
}
