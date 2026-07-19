import { cn } from "@/lib/utils";

interface ScoreBarProps {
  label: string;
  score: number;
}

function barColor(score: number): string {
  if (score >= 65) return "bg-success";
  if (score >= 40) return "bg-warning";
  return "bg-danger";
}

export function ScoreBar({ label, score }: ScoreBarProps) {
  return (
    <div>
      <div className="flex items-center justify-between text-xs font-medium text-gray">
        <span>{label}</span>
        <span className="text-dark">{Math.round(score)}</span>
      </div>
      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={cn("h-full rounded-full", barColor(score))}
          style={{ width: `${Math.max(0, Math.min(100, score))}%` }}
        />
      </div>
    </div>
  );
}
