"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/60 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 disabled:pointer-events-none disabled:opacity-50 select-none active:scale-[0.98]",
  {
    variants: {
      variant: {
        default:
          "bg-gradient-to-r from-indigo-500 to-violet-600 text-white shadow-glow-indigo hover:from-indigo-400 hover:to-violet-500 hover:shadow-[0_0_24px_rgba(99,102,241,0.4)]",
        secondary:
          "bg-zinc-800 border border-zinc-700/60 text-zinc-200 hover:bg-zinc-700/80 hover:text-zinc-50 hover:border-zinc-600/60",
        ghost:
          "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60",
        destructive:
          "bg-red-950/60 border border-red-800/60 text-red-400 hover:bg-red-900/60 hover:text-red-300 hover:border-red-700/60",
        outline:
          "border border-zinc-700/60 bg-transparent text-zinc-300 hover:bg-zinc-800/60 hover:text-zinc-100 hover:border-zinc-600/60",
        link:
          "text-indigo-400 underline-offset-4 hover:underline hover:text-indigo-300 p-0 h-auto",
      },
      size: {
        default: "h-10 px-5 py-2",
        sm: "h-8 px-3.5 py-1.5 text-xs rounded-lg",
        lg: "h-12 px-7 py-3 text-base rounded-xl",
        xl: "h-14 px-8 py-4 text-base rounded-2xl",
        icon: "h-9 w-9 p-0 rounded-lg",
        "icon-sm": "h-7 w-7 p-0 rounded-md",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
