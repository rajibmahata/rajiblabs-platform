import { useCallback, useRef, useState } from "react";
import { toast } from "./toast";

/**
 * Centralized async action handler for Admin.
 * - Prevents duplicate submissions (button disabled while loading)
 * - Ensures loader never stuck (try → success → error → finally)
 * - Shows success/error toasts via shared bus
 * - Preserves UI state (caller controls refresh)
 *
 * Usage:
 * const { run, isLoading } = useAsyncActions();
 * <button onClick={() => run("save", async () => { await api.put(...) }, { successTitle: "Saved" })} disabled={isLoading("save")}>
 *  {isLoading("save") ? <InlineLoader text="Saving..." /> : "Save"}
 * </button>
 */
export function useAsyncActions() {
  const [loadings, setLoadings] = useState<Record<string, boolean>>({});
  const loadingsRef = useRef<Record<string, boolean>>({});
  const set = (key: string, v: boolean) => {
    loadingsRef.current = { ...loadingsRef.current, [key]: v };
    setLoadings({ ...loadingsRef.current });
    if (!v) {
      // cleanup false entries to keep object small
      const next = { ...loadingsRef.current };
      delete next[key];
      loadingsRef.current = next;
      setLoadings({ ...next });
    }
  };

  const run = useCallback(
    async (
      key: string,
      fn: () => Promise<unknown>,
      opts?: { successTitle?: string; successMsg?: string; errorTitle?: string; loadingText?: string }
    ) => {
      if (loadingsRef.current[key]) return;
      set(key, true);
      try {
        const res = await fn();
        if (opts?.successTitle) toast(opts.successTitle, opts.successMsg || "");
        return res;
      } catch (e: unknown) {
        const msg = String((e as Error)?.message || e).slice(0, 300);
        toast(opts?.errorTitle || "Action failed", msg || "Please try again.");
        throw e;
      } finally {
        set(key, false);
      }
    },
    []
  );

  const isLoadingRef = useCallback((key: string) => !!loadingsRef.current[key], []);
  const isAnyLoading = Object.values(loadings).some(Boolean);

  // For render, use state-driven loadings; for logic, use ref
  return { run, isLoading: (k: string) => !!loadings[k], isLoadingRef, isAnyLoading, loadings };
}
