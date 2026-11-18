"use client";

import { useId, useRef } from "react";
import { formatBytes } from "@/lib/format";
import { ui } from "@/lib/ui";

type Props = {
  label: string;
  hint: string;
  accept: string;
  files: File[];
  onChange: (files: File[]) => void;
  multiple?: boolean;
};

// A button opens the picker, so the control matches the rest of the design system.
// The native input stays hidden; keyboard users reach the button and the list.
export function FileField({ label, hint, accept, files, onChange, multiple = false }: Props) {
  const id = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const hintId = `${id}-hint`;
  const labelId = `${id}-label`;

  function pick(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = Array.from(e.target.files ?? []);
    e.target.value = ""; // allow picking the same file again after removing it
    if (picked.length === 0) return;
    if (!multiple) return onChange(picked.slice(0, 1));
    const seen = new Set(files.map((f) => `${f.name}:${f.size}`));
    onChange([...files, ...picked.filter((f) => !seen.has(`${f.name}:${f.size}`))]);
  }

  function remove(index: number) {
    onChange(files.filter((_, i) => i !== index));
  }

  const buttonText =
    files.length === 0
      ? multiple
        ? "Choose PDFs"
        : "Choose file"
      : multiple
        ? "Add more PDFs"
        : "Replace file";

  return (
    <div role="group" aria-labelledby={labelId} className="grid gap-2">
      <span id={labelId} className={ui.field}>{label}</span>
      <span id={hintId} className={ui.hint}>{hint}</span>
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          aria-describedby={hintId}
          className={ui.secondary}
        >
          {buttonText}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={pick}
          tabIndex={-1}
          aria-hidden="true"
          className="hidden"
        />
        <span className="text-caption" aria-live="polite">
          {files.length === 0
            ? "No file chosen"
            : `${files.length} ${files.length === 1 ? "file" : "files"} chosen`}
        </span>
      </div>
      {files.length > 0 && (
        <ul className={`${ui.panel} divide-y divide-rule`}>
          {files.map((f, i) => (
            <li key={`${f.name}:${f.size}:${i}`} className="flex items-center justify-between gap-3 px-3 py-2">
              <span className="min-w-0 truncate">{f.name}</span>
              <span className="flex shrink-0 items-center gap-3">
                <span className="text-caption tabular-nums">{formatBytes(f.size)}</span>
                <button
                  type="button"
                  onClick={() => remove(i)}
                  aria-label={`Remove ${f.name}`}
                  className="text-caption font-medium underline"
                >
                  Remove
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
