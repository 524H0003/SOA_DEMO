import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

export function FieldLabel({ children }: { children: ReactNode }) {
  return <label className="field-label">{children}</label>;
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input className="input" {...props} />;
}

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className="input textarea" {...props} />;
}
