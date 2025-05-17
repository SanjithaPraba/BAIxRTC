import * as React from "react"

const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "default" | "outline" | "ghost" | "link"
  }
>(({ className, variant, ...props }, ref) => {
  return <button className={className} ref={ref} {...props} />
})
Button.displayName = "Button"

export { Button }

