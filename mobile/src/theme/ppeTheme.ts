/**
 * Apple Human Interface Guidelines (HIG) Theme for BSL Safety Intelligence.
 * Conforms to Apple iOS Dark Appearance & Industrial Safety Ergonomics:
 *   - Pure true-black canvas (#000000) for OLED power efficiency and deep contrast
 *   - Continuous curvature squircles (18px-24px) for cards and modals
 *   - 9999px capsule pills for all interactive controls and status badges
 *   - Apple System Colors: Blue (#0A84FF), Red (#FF453A), Green (#30D158), Orange (#FF9F0A), Purple (#BF5AF2)
 *   - Minimum touch target: >= 48px (Apple WCAG & Industrial glove compliant)
 *   - Hairline specular borders (rgba(255, 255, 255, 0.12))
 */

export const PPETheme = {
  // Touch Targets (Apple HIG & Glove compliant >= 48pt)
  touchTarget: {
    minHeight: 48,
    minWidth: 48,
    giantButtonSize: 110,
    checkboxSize: 26,
    borderRadius: 20,
    borderWidth: 1,
  },

  // Apple Dark System Palette
  colors: {
    background: '#000000',
    canvas: '#000000',
    surface: '#1c1c1e',
    surfaceElevated: '#2c2c2e',
    surfaceGlass: 'rgba(28, 28, 30, 0.85)',
    border: 'rgba(255, 255, 255, 0.12)',
    borderSubtle: 'rgba(255, 255, 255, 0.08)',
    borderActive: '#0A84FF',

    // Apple Semantic System Colors (Dark Mode)
    appleBlue: '#0A84FF',
    appleRed: '#FF453A',
    appleGreen: '#30D158',
    appleOrange: '#FF9F0A',
    applePurple: '#BF5AF2',
    appleYellow: '#FFD60A',

    // Safety Signal Highlights (Mapped to Apple HIG)
    emergencyRed: '#FF453A',
    emergencyBg: 'rgba(255, 69, 58, 0.15)',
    warningAmber: '#FF9F0A',
    warningBg: 'rgba(255, 159, 10, 0.15)',
    safeEmerald: '#30D158',
    safeBg: 'rgba(48, 209, 88, 0.15)',
    infoSky: '#0A84FF',

    // High Legibility Apple System Text
    textPrimary: '#FFFFFF',
    textSecondary: 'rgba(235, 235, 245, 0.65)',
    textMuted: 'rgba(235, 235, 245, 0.45)',
    textContrastBlack: '#000000',
  },

  // Apple SF Pro Typography Hierarchies
  typography: {
    heroTitle: {
      fontSize: 26,
      fontWeight: '700' as const,
      lineHeight: 32,
      letterSpacing: -0.5,
    },
    sectionTitle: {
      fontSize: 19,
      fontWeight: '600' as const,
      lineHeight: 24,
      letterSpacing: -0.3,
    },
    buttonText: {
      fontSize: 16,
      fontWeight: '600' as const,
      letterSpacing: -0.2,
    },
    bodyLarge: {
      fontSize: 15,
      fontWeight: '400' as const,
      lineHeight: 22,
      letterSpacing: -0.1,
    },
  },

  // Apple Capsule & Squircle button styles
  buttonStyles: {
    giantVoiceButton: {
      width: 110,
      height: 110,
      borderRadius: 55,
      alignItems: 'center' as const,
      justifyContent: 'center' as const,
      backgroundColor: '#0A84FF',
      shadowColor: '#0A84FF',
      shadowOffset: { width: 0, height: 6 },
      shadowOpacity: 0.45,
      shadowRadius: 16,
      elevation: 10,
    },
    gloveCardButton: {
      minHeight: 58,
      paddingHorizontal: 20,
      paddingVertical: 14,
      borderRadius: 20,
      borderWidth: 1,
      borderColor: 'rgba(255, 255, 255, 0.12)',
      backgroundColor: 'rgba(28, 28, 30, 0.85)',
      justifyContent: 'center' as const,
      marginVertical: 6,
    },
  },
};
