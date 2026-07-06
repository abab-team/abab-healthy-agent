import { useCallback, useEffect, useState } from "react";
import type { ApiResult } from "@/types/api";

export function useApiResource<T>(loader: () => Promise<ApiResult<T>>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    const result = await loader();
    if (result.ok && result.data) {
      setData(result.data);
    } else {
      setError(result.error?.message ?? "加载失败");
    }
    setLoading(false);
  }, deps);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { data, error, loading, reload };
}
