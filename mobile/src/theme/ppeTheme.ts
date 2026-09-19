/**
 * Industrial PPE & Leather Gloves Ergonomic Theme.
 * Designed for frontline workers in heavy metallurgical plants:
 *   - Minimum touch target: 64px (accessible with heavy welding/aluminized gloves)
 *   - High-contrast color ratios (> 7:1) for bright furnace glare or dim basements
 *   - Thumb-zone ergonomics (anchoring critical actions to the lower 60% of viewport)
 *   - Voice-first giant trigger buttons
 */

export const PPETheme = {
  // Touch Targets (Glove compliant)
  touchTarget: {
    minHeight: 64,
    minWidth: 64,
    giantButtonSize: 110,
    checkboxSize: 32,
    borderRadius: 14,
    borderWidth: 2,
  },

  // High Contrast Industrial Palette
  colors: {
    background: '#070d18',
    surface: '#0f172a',
    surfaceElevated: '#1e293b',
    border: '#334155',
    borderActive: '#38bdf8',

    // Safety High-Vis Highlights
    emergencyRed: '#ef4444',
    emergencyBg: 'rgba(239, 68, 68, 0.18)',
    warningAmber: '#f59e0b',
    warningBg: 'rgba(245, 158, 11, 0.18)',
    safeEmerald: '#10b981',
    safeBg: 'rgba(16, 185, 129, 0.18)',
    infoSky: '#38bdf8',

    // High Legibility Text
    textPrimary: '#ffffff',
    textSecondary: '#cbd5e1',
    textMuted: '#94a3b8',
    textContrastBlack: '#000000',
  },

  // Font Hierarchies
  typography: {
    heroTitle: {
      fontSize: 24,
      fontWeight: '900' as const,
      lineHeight: 30,
      letterSpacing: 0.5,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: '800' as const,
      lineHeight: 24,
    },
    buttonText: {
      fontSize: 17,
      fontWeight: '800' as const,
      letterSpacing: 0.5,
    },
    bodyLarge: {
      fontSize: 15,
      fontWeight: '600' as const,
      lineHeight: 22,
    },
  },

  // Glove-friendly button styles
  buttonStyles: {
    giantVoiceButton: {
      width: 110,
      height: 110,
      borderRadius: 55,
      alignItems: 'center' as const,
      justifyContent: 'center' as const,
      elevation: 8,
      shadowColor: '#10b981',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.5,
      shadowRadius: 10,
    },
    gloveCardButton: {
      minHeight: 70,
      paddingHorizontal: 18,
      paddingVertical: 14,
      borderRadius: 14,
      borderWidth: 2,
      justifyContent: 'center' as const,
      marginVertical: 6,
    },
  },
};
