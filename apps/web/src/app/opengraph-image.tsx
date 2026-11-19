import { ImageResponse } from "next/og";

export const alt = "Milaan, GSTR-2B reconciliation for CA firms";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%", height: "100%", display: "flex", flexDirection: "column",
          justifyContent: "space-between", padding: 80, background: "#23306b", color: "#f7f8f6",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 20, fontSize: 44, fontWeight: 700 }}>
          <svg width="80" height="48" viewBox="0 0 40 24">
            <circle cx="13" cy="12" r="9" fill="none" stroke="#f7f8f6" strokeWidth="3" />
            <circle cx="27" cy="12" r="9" fill="none" stroke="#f7f8f6" strokeWidth="3" />
          </svg>
          Milaan
        </div>
        <div style={{ display: "flex", fontSize: 68, fontWeight: 700, lineHeight: 1.1, maxWidth: 980 }}>
          Match every GSTR-2B invoice to the books before you claim credit
        </div>
        <div style={{ display: "flex", fontSize: 28, opacity: 0.75 }}>
          Verdicts by rules. Reasons by Gemini. Decisions by your team.
        </div>
      </div>
    ),
    size,
  );
}
