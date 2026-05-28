import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors select-none",
  {
    variants: {
      variant: {
        default:
          "bg-zinc-800/80 border-zinc-700/60 text-zinc-300",
        secondary:
          "bg-zinc-900/80 border-zinc-800/60 text-zinc-400",
        success:
          "bg-emerald-950/70 border-emerald-800/50 text-emerald-300",
        warning:
          "bg-amber-950/70 border-amber-800/50 text-amber-300",
        info:
          "bg-blue-950/70 border-blue-800/50 text-blue-300",
        interview:
          "bg-violet-950/70 border-violet-800/50 text-violet-300",
        offer:
          "bg-emerald-950/70 border-emerald-700/50 text-emerald-200",
        destructive:
          "bg-red-950/70 border-red-900/50 text-red-400",
        indigo:
          "bg-indigo-950/70 border-indigo-800/50 text-indigo-300",
        outline:
          "bg-transparent border-zinc-700/60 text-zinc-400",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
