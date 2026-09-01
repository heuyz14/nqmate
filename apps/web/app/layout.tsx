import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "NQ Directional Bias AI",
  description: "Evidence-backed Nasdaq-100 futures research assistant",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
