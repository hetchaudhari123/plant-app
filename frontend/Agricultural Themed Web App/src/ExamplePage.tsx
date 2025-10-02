"use client";

import React from "react";
import { Button } from "./components/ui/button";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "./components/ui/dialog"; 

export default function ExamplePage() {
  return (
    <div className="p-8">
      <Dialog>
        {/* IMPORTANT: use asChild so DialogTrigger delegates to your Button (no nested <button>) */}
        <DialogTrigger asChild>
          <Button>Open Dialog</Button>
        </DialogTrigger>

        {/* DialogContent will mount when opened */}
        <DialogContent className="bg-white p-6 rounded shadow-lg">
          <DialogHeader>
            <DialogTitle>Test Dialog</DialogTitle>
            <DialogDescription>This is a minimal dialog to test Radix + Button.</DialogDescription>
          </DialogHeader>

          <div className="mt-4">
            <p>Dialog body content. Click Close to dismiss.</p>
          </div>

          <DialogFooter>
            <DialogClose asChild>
              <Button>Close</Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* --- Debug helpers (optional) ---
          1) Force open: <Dialog open> ... </Dialog>
          2) Replace DialogTrigger with a plain trigger to test Radix itself:
             <DialogTrigger><button>Open</button></DialogTrigger>
      */}
    </div>
  );
}
