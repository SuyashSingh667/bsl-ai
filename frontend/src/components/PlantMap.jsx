import React, { useState, useEffect } from "react";
import { getPlantDetails } from "../api";

export default function PlantMap({ incidentZoneId, impactAssessment, plantId = "bsl_bokaro" }) {
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hoveredZone, setHoveredZone] = useState(null);

  useEffect(() => {
    let mounted = true;
    getPlantDetails(plantId)
      .then((data) => {
        if (mounted && data?.zones) {
          setZones(data.zones);
        }
      })
      .catch((err) => {
        console.warn("Could not fetch dynamic plant zones, using defaults", err);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [plantId]);

  if (loading && zones.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 text-center text-slate-400 text-xs">
        Loading plant layout map...
      </div>
    );
  }

  // Calculate coordinates bounds
  const xs = zones.map((z) => z.centroid?.x || 0);
  const ys = zones.map((z) => z.centroid?.y || 0);
  const minX = Math.min(...xs, 0) - 200;
  const maxX = Math.max(...xs, 5000) + 200;
  const minY = Math.min(...ys, -400) - 200;
  const maxY = Math.max(...ys, 1400) + 200;
  const viewBoxWidth = maxX - minX;
  const viewBoxHeight = maxY - minY;

  const originZone = zones.find((z) => z.zone_id === incidentZoneId);
  const affectedZoneIds = new Set(
    (impactAssessment?.affected_zones || []).map((az) => az.zone_id)
  );

  const primaryRadius = impactAssessment?.primary_radius_m || 150;
  const secondaryRadius = impactAssessment?.secondary_radius_m || 350;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg flex flex-col gap-3">
      {/* Map Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <span>🗺️ Plant Spatial Layout & Indicative Footprint</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Advisory / Unvalidated
            </span>
          </h4>
          <p className="text-[11px] text-slate-400">
            Zone highlights & planning buffers. Not a calibrated blast-radius model.
          </p>
        </div>
        {originZone && (
          <div className="text-right">
            <span className="text-[10px] text-slate-400 uppercase font-medium">Incident Origin</span>
            <div className="text-xs font-bold text-red-400 font-mono">
              {originZone.zone_id} — {originZone.name}
            </div>
          </div>
        )}
      </div>

      {/* SVG Container */}
      <div className="relative w-full overflow-hidden bg-slate-950/70 border border-slate-800/80 rounded-lg">
        <svg
          viewBox={`${minX} ${minY} ${viewBoxWidth} ${viewBoxHeight}`}
          className="w-full h-72 md:h-80 select-none cursor-crosshair"
        >
          {/* Subtle Background Grid Lines */}
          <defs>
            <pattern id="grid" width="400" height="400" patternUnits="userSpaceOnUse">
              <path d="M 400 0 L 0 0 0 400" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
            </pattern>
          </defs>
          <rect x={minX} y={minY} width={viewBoxWidth} height={viewBoxHeight} fill="url(#grid)" />

          {/* Indicative Footprint Buffers (around origin zone) */}
          {originZone && (
            <g>
              {/* Secondary Buffer */}
              <circle
                cx={originZone.centroid.x}
                cy={originZone.centroid.y}
                r={secondaryRadius}
                fill="rgba(245, 158, 11, 0.08)"
                stroke="#F59E0B"
                strokeWidth="1.5"
                strokeDasharray="6 4"
              />
              {/* Primary Buffer */}
              <circle
                cx={originZone.centroid.x}
                cy={originZone.centroid.y}
                r={primaryRadius}
                fill="rgba(239, 68, 68, 0.15)"
                stroke="#EF4444"
                strokeWidth="2"
                strokeDasharray="4 2"
              />
            </g>
          )}

          {/* Render Plant Zones */}
          {zones.map((z) => {
            const isOrigin = z.zone_id === incidentZoneId;
            const isAffected = affectedZoneIds.has(z.zone_id) && !isOrigin;
            const r = z.footprint_radius_m || 80;

            let fillColor = "#1E293B";
            let strokeColor = "#334155";
            let textColor = "#94A3B8";

            if (isOrigin) {
              fillColor = "rgba(220, 38, 38, 0.85)";
              strokeColor = "#EF4444";
              textColor = "#FFFFFF";
            } else if (isAffected) {
              fillColor = "rgba(217, 119, 6, 0.75)";
              strokeColor = "#F59E0B";
              textColor = "#FEF3C7";
            } else if (z.phone_restricted) {
              fillColor = "#1E1E2E";
              strokeColor = "#6366F1";
            }

            return (
              <g
                key={z.zone_id}
                onMouseEnter={() => setHoveredZone(z)}
                onMouseLeave={() => setHoveredZone(null)}
                className="cursor-pointer transition-transform hover:scale-105"
              >
                {/* Zone Area Circle */}
                <circle
                  cx={z.centroid?.x || 0}
                  cy={z.centroid?.y || 0}
                  r={r}
                  fill={fillColor}
                  stroke={strokeColor}
                  strokeWidth={isOrigin ? "4" : isAffected ? "2.5" : "1"}
                  className="transition-all duration-200"
                />

                {/* Pulse ring for active incident origin */}
                {isOrigin && (
                  <circle
                    cx={z.centroid?.x || 0}
                    cy={z.centroid?.y || 0}
                    r={r + 30}
                    fill="none"
                    stroke="#EF4444"
                    strokeWidth="1.5"
                    opacity="0.6"
                  />
                )}

                {/* Label text */}
                <text
                  x={z.centroid?.x || 0}
                  y={(z.centroid?.y || 0) + 4}
                  textAnchor="middle"
                  fill={textColor}
                  fontSize={r > 100 ? "34" : "28"}
                  fontWeight="bold"
                  fontFamily="monospace"
                >
                  {z.zone_id}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Hovered Zone Floating Card */}
        {hoveredZone && (
          <div className="absolute bottom-2 left-2 bg-slate-900/90 backdrop-blur-md border border-slate-700 text-slate-200 text-xs px-3 py-2 rounded shadow-xl pointer-events-none">
            <div className="font-bold text-amber-400">
              [{hoveredZone.zone_id}] {hoveredZone.name}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Category: <span className="text-slate-300 capitalize">{hoveredZone.category}</span> | Day Shift:{" "}
              <span className="text-slate-300">{hoveredZone.occupancy?.day ?? "N/A"} workers</span>
            </div>
            {hoveredZone.phone_restricted && (
              <div className="text-[10px] text-indigo-400 font-semibold mt-0.5">
                📵 Phone-Restricted Zone (Intrinsically Safe)
              </div>
            )}
          </div>
        )}
      </div>

      {/* Map Legend & Disclaimer Footer */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400 pt-1">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block ring-2 ring-red-500/30"></span>
            <span>Origin Zone</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block ring-2 ring-amber-500/30"></span>
            <span>Affected Zone</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-700 border border-slate-600 inline-block"></span>
            <span>Plant Zone</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0 border-t-2 border-dashed border-red-400 inline-block"></span>
            <span>Primary Buffer ({primaryRadius}m)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0 border-t-2 border-dashed border-amber-400 inline-block"></span>
            <span>Secondary Buffer ({secondaryRadius}m)</span>
          </div>
        </div>
        <div className="text-[10px] text-slate-400 italic">
          *Indicative footprint only — verify with safety engineer before boundary closure.
        </div>
      </div>
    </div>
  );
}
