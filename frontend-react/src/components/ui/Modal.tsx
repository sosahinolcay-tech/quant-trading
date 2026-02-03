import type { ReactNode } from "react";

type ModalProps = {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
};

export function Modal({ open, onClose, children }: ModalProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-xl border border-border bg-card p-4 shadow-glass">
        <div className="flex justify-end">
          <button onClick={onClose} className="text-xs text-muted hover:text-text">
            Esc
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
