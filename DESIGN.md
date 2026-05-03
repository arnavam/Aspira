---
name: Aspira Executive Interface
colors:
  surface: '#111415'
  surface-dim: '#111415'
  surface-bright: '#373a3b'
  surface-container-lowest: '#0c0f10'
  surface-container-low: '#191c1d'
  surface-container: '#1d2021'
  surface-container-high: '#282a2b'
  surface-container-highest: '#323536'
  on-surface: '#e1e3e4'
  on-surface-variant: '#c8c4d8'
  inverse-surface: '#e1e3e4'
  inverse-on-surface: '#2e3132'
  outline: '#918fa1'
  outline-variant: '#464555'
  surface-tint: '#c4c0ff'
  primary: '#c4c0ff'
  on-primary: '#2200a3'
  primary-container: '#5b4fe8'
  on-primary-container: '#e8e4ff'
  inverse-primary: '#5244de'
  secondary: '#e6c364'
  on-secondary: '#3d2e00'
  secondary-container: '#785d00'
  on-secondary-container: '#fdd977'
  tertiary: '#c1c5e1'
  on-tertiary: '#2a2f45'
  tertiary-container: '#61667f'
  on-tertiary-container: '#e3e5ff'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e3dfff'
  primary-fixed-dim: '#c4c0ff'
  on-primary-fixed: '#120068'
  on-primary-fixed-variant: '#3824c7'
  secondary-fixed: '#ffe08f'
  secondary-fixed-dim: '#e6c364'
  on-secondary-fixed: '#241a00'
  on-secondary-fixed-variant: '#584400'
  tertiary-fixed: '#dde1fe'
  tertiary-fixed-dim: '#c1c5e1'
  on-tertiary-fixed: '#151a2f'
  on-tertiary-fixed-variant: '#41465d'
  background: '#111415'
  on-background: '#e1e3e4'
  surface-variant: '#323536'
typography:
  display-xl:
    fontFamily: Noto Serif
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Noto Serif
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Noto Serif
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: '0'
  body-lg:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-md:
    fontFamily: Manrope
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  label-md:
    fontFamily: Manrope
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Manrope
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-max: 1200px
  gutter: 24px
  margin-page: 40px
  stack-sm: 12px
  stack-md: 24px
  stack-lg: 48px
---

## Brand & Style
The brand personality of this design system is authoritative, sophisticated, and high-stakes. It is designed to facilitate formal AI-driven interviews where the environment must feel as professional and prestigious as a physical executive boardroom. 

The style is a refined hybrid of **Minimalism** and **Glassmorphism**. It prioritizes extreme clarity and focus to reduce candidate anxiety while using translucent, frosted layers to create a sense of physical depth and modern innovation. The interface should feel "quiet" yet technologically advanced, utilizing subtle motion to guide the user's attention without distraction.

## Colors
The palette is rooted in a deep, nocturnal foundation to establish a "theatrical" focus on the interview content.
- **Primary (#5B4FE8):** An electric indigo used exclusively for primary actions, active states, and progress indicators. It represents the "AI intelligence" within the platform.
- **Secondary (#C9A84C):** A warm gold reserved for high-level brand moments, achievement states, or "Premium/Executive" status markers.
- **Surface & Background:** The background is a dense navy (#0D0F1A). Higher-tier surfaces use the tertiary navy (#161B30) with varying levels of transparency.
- **Typography:** Soft white (#F8F9FA) is used for maximum legibility, while a muted silver-blue (#9499B0) is used for secondary metadata to maintain visual hierarchy.

## Typography
This design system utilizes a high-contrast typographic pairing to balance tradition and technology. 
- **Headings:** 'Noto Serif' (serving as the high-fidelity alternative to Playfair) provides an editorial, academic, and formal tone. It should be used for page titles, section headers, and key quotes.
- **Interface & Body:** 'Manrope' (serving as the modern UI choice) is used for all functional elements, inputs, and long-form body text. Its geometric balance ensures readability at small sizes on dark backgrounds.
- **Formatting:** Use generous line heights for body text to maintain an airy, sophisticated feel. Labels should use uppercase styling with slight letter spacing to differentiate them from interactive text.

## Layout & Spacing
The layout follows a **Fixed Grid** model for desktop environments to maintain a "contained" and controlled interview experience. A 12-column grid is used with wide gutters to prevent the UI from feeling cramped.

The spacing rhythm is strictly based on an 8px base unit. 
- **Margins:** Large outer margins (40px+) create a "frame" effect, emphasizing the content as a focal point.
- **Vertical Rhythm:** Use "stack" variables to maintain consistent grouping. Use `stack-lg` to separate major conceptual blocks and `stack-sm` for internal component elements.
- **Alignment:** Content should be centered within the viewport to mimic the eye contact of an in-person interview.

## Elevation & Depth
Depth is communicated through **Glassmorphism** and tonal layering rather than traditional heavy shadows.
- **Layer 0 (Base):** The deep navy background (#0D0F1A).
- **Layer 1 (Cards/Containers):** Tertiary color (#161B30) at 60% opacity with a `20px` backdrop-blur and a subtle 1px inner border (border-white at 10% opacity) to catch the light.
- **Layer 2 (Modals/Popovers):** Higher opacity (80%) with a more pronounced white-to-transparent linear gradient border.
- **Interactions:** When an element is hovered, the backdrop-blur should intensify, and the inner border should transition to the Primary indigo color at low opacity.

## Shapes
The shape language is **Rounded**, striking a balance between the rigidity of a formal environment and the approachability of a modern AI assistant. 
- **Standard UI (Buttons, Inputs):** 0.5rem (8px) radius.
- **Containers (Cards, Video Feeds):** 1rem (16px) radius to create a soft, "contained" look.
- **Interactive States:** Use consistent radii across all elements to maintain a rhythmic visual language. Avoid "Pill" shapes for primary actions to keep the aesthetic professional rather than casual.

## Components
- **Buttons:** Primary buttons use a solid Electric Indigo fill with white text. Secondary buttons use the glass effect with a subtle border. Use a "spring" CSS transition (0.3s) for hover states.
- **Input Fields:** Semi-transparent backgrounds with a 1px bottom border that glows Indigo on focus. The label should float above the field in a smaller 'Manrope' weight.
- **Cards:** Use the frosted glass effect defined in the Elevation section. Ensure a padding of at least 32px to allow the content to breathe.
- **Video Feed Container:** Specifically styled with a Warm Gold thin border if the candidate is "Live" or "Speaking," creating a "premium frame" effect.
- **Chips/Badges:** Small, high-contrast labels with 'Manrope' semibold. Use Indigo for "AI Tags" and Gold for "Verified Skills."
- **Progress Indicators:** Minimalist linear bars using the Electric Indigo color, featuring a subtle "pulse" animation during AI processing states.