import { useEffect } from 'react';
import { AlertTriangle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';

interface ConfirmationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  body: string;
  cancelText?: string;
  confirmText?: string;
  primaryButtonColor?: 0 | 1; // 0 = green (safe), 1 = red (destructive)
  onCancel?: () => void;
  onConfirm: () => void;
}

export function ConfirmationModal({
  open,
  onOpenChange,
  title,
  body,
  cancelText = 'Cancel',
  confirmText = 'Confirm',
  primaryButtonColor = 0,
  onCancel,
  onConfirm,
}: ConfirmationModalProps) {
  const isDestructive = primaryButtonColor === 1;

  // Handle keyboard shortcuts
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey) {
        e.preventDefault();
        onConfirm();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onConfirm]);

  const handleCancel = () => {
    onCancel?.();
    onOpenChange(false);
  };

  const handleConfirm = () => {
    onConfirm();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[440px] rounded-2xl shadow-2xl border-border/50 p-0 overflow-hidden gap-0 animate-in fade-in-0 zoom-in-95 duration-200">
        {/* Header Section */}
        <DialogHeader className="px-6 pt-6 pb-4 space-y-3">
          <div className="flex items-start gap-3">
            {isDestructive && (
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 dark:bg-red-950 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
              </div>
            )}
            <div className="flex-1">
              <DialogTitle className="text-left text-[1.25rem] leading-tight text-foreground">
                {title}
              </DialogTitle>
            </div>
          </div>
          <DialogDescription className="text-left text-[0.9375rem] text-muted-foreground leading-relaxed">
            {body}
          </DialogDescription>
        </DialogHeader>

        {/* Footer with Action Buttons */}
        <DialogFooter className="px-6 pb-6 pt-2 flex-row justify-end gap-3 sm:gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={handleCancel}
            className="min-w-[100px] rounded-xl border-2 hover:bg-secondary/80 transition-all duration-200"
          >
            {cancelText}
          </Button>
          <Button
            type="button"
            onClick={handleConfirm}
            className={`min-w-[100px] rounded-xl transition-all duration-200 shadow-md hover:shadow-lg ${
              isDestructive
                ? 'bg-red-600 hover:bg-red-700 text-white dark:bg-red-600 dark:hover:bg-red-700'
                : 'bg-primary hover:bg-primary/90 text-primary-foreground shadow-green-200 dark:shadow-none'
            }`}
          >
            {confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}