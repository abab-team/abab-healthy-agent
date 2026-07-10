import { colors } from "@/constants/colors";

/** Product-facing visual tokens shared by the mobile v2 screens. */
export const theme = {
  colors: {
    ...colors,
    canvas: "#F7FAF8",
    ink: "#162B28",
    subtle: "#71817E",
    tealSoft: "#E8F8F3",
    blueSoft: "#EEF7FF",
    coralSoft: "#FFF1ED",
    lavenderSoft: "#F3F0FF",
    line: "#E6EFEB"
  },
  radius: {
    sm: 12,
    md: 18,
    lg: 24,
    pill: 999
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20,
    xxl: 28
  },
  type: {
    overline: 12,
    body: 14,
    bodySmall: 12,
    title: 24,
    section: 18
  }
} as const;
