"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { useTranslation } from "@/hooks/useTranslation";
import { ROUTES } from "@/lib/constants";

const MESSAGE_INTERVAL_MS = 1400;

export function Step8LoadingResult() {
  const t = useTranslation();
  const router = useRouter();
  const messages = t.onboarding.step8.loadingMessages;
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((i) => (i + 1) % messages.length);
    }, MESSAGE_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [messages.length]);

  useEffect(() => {
    // Skeleton wiring only: once the backend call resolves, this redirect
    // moves the user to /results with real data instead of a fixed delay.
    const timeout = setTimeout(() => {
      router.push(ROUTES.results);
    }, MESSAGE_INTERVAL_MS * messages.length);
    return () => clearTimeout(timeout);
  }, [messages.length, router]);

  return (
    <div className="mx-auto flex max-w-md flex-col items-center text-center">
      <motion.div
        className="h-14 w-14 rounded-full border-4 border-slate-200 border-t-primary"
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      />

      <div className="mt-6 h-6">
        <AnimatePresence mode="wait">
          <motion.p
            key={messageIndex}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3 }}
            className="text-sm font-medium text-gray"
          >
            {messages[messageIndex]}
          </motion.p>
        </AnimatePresence>
      </div>
    </div>
  );
}
