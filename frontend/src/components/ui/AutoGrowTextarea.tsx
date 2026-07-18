"use client";

import { useRef, useState, type TextareaHTMLAttributes } from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export function AutoGrowTextarea({
  className,
  onChange,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const [isTyping, setIsTyping] = useState(false);

  return (
    <div className="relative">
      <textarea
        ref={ref}
        rows={5}
        className={cn(
          "w-full resize-none rounded-2xl border border-slate-200 bg-white p-5 pr-14 text-base text-dark placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20",
          className
        )}
        onChange={(e) => {
          setIsTyping(e.target.value.length > 0);
          // Keep the textarea height in sync with its content.
          e.target.style.height = "auto";
          e.target.style.height = `${e.target.scrollHeight}px`;
          onChange?.(e);
        }}
        {...props}
      />
      <motion.div
        className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-primary to-success"
        animate={
          isTyping
            ? { opacity: [0.6, 1, 0.6], scale: [1, 1.08, 1] }
            : { opacity: 0.4, scale: 1 }
        }
        transition={
          isTyping ? { duration: 1.6, repeat: Infinity } : { duration: 0.3 }
        }
      >
        <Sparkles className="h-4 w-4 text-white" strokeWidth={2} />
      </motion.div>
    </div>
  );
}
