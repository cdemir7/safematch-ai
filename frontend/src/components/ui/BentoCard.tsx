"use client";

import type { ReactNode } from "react";
import { motion, type HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

export interface BentoCardProps
  extends Omit<HTMLMotionProps<"button">, "title"> {
  icon?: ReactNode;
  title: string;
  description: string;
  selected?: boolean;
}

/**
 * Large, whole-card-clickable option used instead of checkboxes. Selection
 * is communicated with a soft blue-green tinted background and a filled
 * ring rather than a border alone, so the "trust and calm" palette carries
 * through the interaction itself, not just the decoration.
 */
export function BentoCard({
  icon,
  title,
  description,
  selected,
  className,
  ...props
}: BentoCardProps) {
  return (
    <motion.button
      type="button"
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
      aria-pressed={selected}
      className={cn(
        "flex flex-col items-start gap-3 rounded-2xl border p-6 text-left transition-colors",
        selected
          ? "border-primary/40 bg-gradient-to-br from-primary-soft to-success-soft ring-2 ring-primary/30"
          : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50",
        className
      )}
      {...props}
    >
      {icon && (
        <div
          className={cn(
            "flex h-11 w-11 items-center justify-center rounded-xl",
            selected ? "bg-white/80 text-primary" : "bg-slate-100 text-gray"
          )}
        >
          {icon}
        </div>
      )}
      <div>
        <p className="text-base font-semibold text-dark">{title}</p>
        <p className="mt-1 text-sm text-gray">{description}</p>
      </div>
    </motion.button>
  );
}
