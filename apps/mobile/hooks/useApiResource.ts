import { useCallback, useEffect, useState } from "react";
import type { ApiResult } from "@/types/api";

export function useApiResource<T>(loader: () => Promise<ApiResult<T>>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    setErrorCode(null);
    const result = await loader();
    if (result.ok) {
      setData(result.data ?? null);
    } else {
      setError(result.error?.message ?? "加载失败");
      setErrorCode(result.error?.code ?? null);
    }
    setLoading(false);
  }, deps);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { data, error, errorCode, loading, reload };
}
