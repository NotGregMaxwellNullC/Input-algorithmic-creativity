import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ["'Geist Mono'", "ui-monospace", "monospace"],
        sans: ["'Geist'", "ui-sans-serif", "system-ui"],
      },
    },
  },
  plugins: [],
};

export default config;
