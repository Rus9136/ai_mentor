'use client';

import { useEffect, useRef, useState } from 'react';

export type ViewStyle = 'ballAndStick' | 'stick' | 'sphere' | 'line';

interface MoleculeViewerProps {
  cid: number;
  viewStyle: ViewStyle;
  spinning: boolean;
}

const VIEW_STYLES: Record<ViewStyle, Record<string, unknown>> = {
  ballAndStick: { stick: { radius: 0.12 }, sphere: { scale: 0.3 } },
  stick: { stick: { radius: 0.15, colorscheme: 'Jmol' } },
  sphere: { sphere: { colorscheme: 'Jmol' } },
  line: { line: { linewidth: 2, colorscheme: 'Jmol' } },
};

export function MoleculeViewer({ cid, viewStyle, spinning }: MoleculeViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const viewerRef = useRef<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize viewer and load molecule
  useEffect(() => {
    let mounted = true;

    const init = async () => {
      setLoading(true);
      setError(null);

      try {
        // Dynamic import — only runs in browser
        const $3Dmol = await import('3dmol');

        if (!mounted || !containerRef.current) return;

        // Create or reuse viewer
        if (viewerRef.current) {
          viewerRef.current.removeAllModels();
          viewerRef.current.removeAllLabels();
        } else {
          viewerRef.current = $3Dmol.createViewer(containerRef.current, {
            backgroundColor: 'white',
          });
        }

        const viewer = viewerRef.current;

        // Fetch 3D structure from PubChem
        const res = await fetch(
          `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${cid}/SDF?record_type=3d`
        );
        if (!res.ok) throw new Error('PubChem error');
        const sdf = await res.text();

        if (!mounted) return;

        viewer.addModel(sdf, 'sdf');
        viewer.setStyle({}, VIEW_STYLES[viewStyle] || VIEW_STYLES.ballAndStick);
        viewer.zoomTo();
        viewer.render();

        if (spinning) viewer.spin('y', 1);
        else viewer.spin(false);
      } catch {
        if (mounted) setError('Failed to load molecule');
      } finally {
        if (mounted) setLoading(false);
      }
    };

    init();
    return () => { mounted = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cid]);

  // Update view style
  useEffect(() => {
    if (!viewerRef.current) return;
    viewerRef.current.setStyle({}, VIEW_STYLES[viewStyle] || VIEW_STYLES.ballAndStick);
    viewerRef.current.render();
  }, [viewStyle]);

  // Toggle spin
  useEffect(() => {
    if (!viewerRef.current) return;
    if (spinning) viewerRef.current.spin('y', 1);
    else viewerRef.current.spin(false);
  }, [spinning]);

  return (
    <div className="relative w-full h-full">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-muted-foreground">Loading...</span>
          </div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
          <p className="text-sm text-red-500">{error}</p>
        </div>
      )}
      <div
        ref={containerRef}
        className="w-full h-full"
        style={{ minHeight: '300px' }}
      />
    </div>
  );
}
