import * as React from "react";
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-react";

export interface SelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div className="relative w-full">
        <select
          className={cn(
            "w-full appearance-none rounded-xl border border-zinc-700/60 bg-zinc-900 px-3.5 py-2.5 pr-9 text-sm text-zinc-100 shadow-sm transition-all",
            "focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "[&>option]:bg-zinc-900 [&>option]:text-zinc-100",
            className
          )}
          ref={ref}
          {...props}
        >
          {children}
        </select>
        <ChevronDown
          size={14}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none"
        />
      </div>
    );
  }
);
Select.displayName = "Select";

export { Select };
