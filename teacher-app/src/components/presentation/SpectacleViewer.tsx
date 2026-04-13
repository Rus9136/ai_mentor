'use client';

import { useMemo } from 'react';
import {
  Deck,
  Slide,
  SlideLayout,
  Heading,
  Text,
  UnorderedList,
  OrderedList,
  ListItem,
  Appear,
  FlexBox,
  Box,
  Grid,
  Notes,
  DefaultTemplate,
  FullScreen,
  Progress,
  fadeTransition,
} from 'spectacle';
import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from './slide-themes';
import { getMediaUrl } from '@/lib/api/client';

/** Build Spectacle bg props with image + color fallback */
function slideBgProps(theme: SlideThemeConfig, slideType: keyof SlideThemeConfig['bg']) {
  const img = theme.bg[slideType];
  const color = theme.bgColor[slideType];
  return {
    ...(img ? { backgroundImage: `url(${img})` } : {}),
    backgroundColor: color,
    backgroundSize: 'cover' as const,
    backgroundPosition: 'center' as const,
  };
}

interface SpectacleViewerProps {
  slides: SlideData[];
  theme: SlideThemeConfig;
  context?: { subject?: string; grade_level?: number };
}

// Map our theme to Spectacle theme object
function buildSpectacleTheme(t: SlideThemeConfig) {
  return {
    colors: {
      primary: '#1e293b',      // heading text
      secondary: '#475569',     // body text
      tertiary: '#f8fafc',      // slide background (fallback)
      quaternary: '#3b82f6',    // accent
      quinary: '#10b981',       // green accent
    },
    fonts: {
      header: '"Segoe UI", "SF Pro Display", system-ui, sans-serif',
      text: '"Segoe UI", "SF Pro Text", system-ui, sans-serif',
    },
    fontSizes: {
      h1: '56px',
      h2: '44px',
      h3: '32px',
      text: '24px',
      monospace: '20px',
    },
    space: [0, 8, 16, 24, 32, 48, 64],
  };
}

// Background style helper
function bgStyle(imageUrl: string) {
  return {
    backgroundImage: `url(${imageUrl})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
  };
}

// Semi-transparent card style
const card = {
  backgroundColor: 'rgba(255,255,255,0.82)',
  backdropFilter: 'blur(8px)',
  borderRadius: '16px',
  padding: '24px 32px',
  border: '1px solid rgba(0,0,0,0.06)',
};

const cardDark = {
  backgroundColor: 'rgba(0,0,0,0.15)',
  backdropFilter: 'blur(8px)',
  borderRadius: '16px',
  padding: '24px 32px',
};

export function SpectacleViewer({ slides, theme, context }: SpectacleViewerProps) {
  const spectacleTheme = useMemo(() => buildSpectacleTheme(theme), [theme]);

  return (
    <Deck theme={spectacleTheme} transition={fadeTransition} template={<DefaultTemplate />}>
      {slides.map((slide, idx) => renderSlide(slide, idx, theme, context))}
    </Deck>
  );
}

function renderSlide(
  slide: SlideData,
  idx: number,
  theme: SlideThemeConfig,
  context?: { subject?: string; grade_level?: number }
) {
  switch (slide.type) {
    case 'title':
      return renderTitle(slide, idx, theme, context);
    case 'objectives':
      return renderObjectives(slide, idx, theme);
    case 'content':
      return renderContent(slide, idx, theme);
    case 'key_terms':
      return renderKeyTerms(slide, idx, theme);
    case 'quiz':
      return renderQuiz(slide, idx, theme);
    case 'summary':
      return renderSummary(slide, idx, theme);
    default:
      return renderContent(slide, idx, theme);
  }
}

// ─── Title Slide ───────────────────────────────

function renderTitle(
  slide: SlideData,
  idx: number,
  theme: SlideThemeConfig,
  context?: { subject?: string; grade_level?: number }
) {
  const footer = context?.grade_level
    ? `${context.subject || ''}  •  ${context.grade_level} класс`
    : context?.subject || '';

  return (
    <Slide key={idx} {...slideBgProps(theme, 'title')}>
      <FlexBox flexDirection="column" alignItems="flex-start" justifyContent="center" height="100%" padding="0 8%">
        <Heading fontSize="h1" fontWeight="800" color="#3d2b1f" margin="0 0 16px 0">
          {slide.title}
        </Heading>
        {slide.subtitle && (
          <Text fontSize="28px" color="#6b4c3b" margin="0 0 32px 0">
            {slide.subtitle}
          </Text>
        )}
        {footer && (
          <Text fontSize="18px" color="#8b7355" margin="24px 0 0 0" style={{ letterSpacing: '1px', textTransform: 'uppercase' as const }}>
            {footer}
          </Text>
        )}
      </FlexBox>
    </Slide>
  );
}

// ─── Objectives Slide ──────────────────────────

function renderObjectives(slide: SlideData, idx: number, theme: SlideThemeConfig) {
  const items = slide.items || [];
  return (
    <Slide key={idx} {...slideBgProps(theme, 'content')}>
      <FlexBox flexDirection="column" alignItems="flex-start" height="100%" padding="5% 8%">
        <Heading fontSize="h2" fontWeight="700" color="#3d2b1f" margin="0 0 8px 0">
          {slide.title}
        </Heading>
        <Box width="80px" height="4px" backgroundColor="#b45309" style={{ borderRadius: '4px' }} />
        <FlexBox flexDirection="column" flex={1} justifyContent="center" width="100%" margin="24px 0 0 0">
          {items.map((item, i) => (
            <Appear key={i} activeStyle={{ opacity: '1' }} inactiveStyle={{ opacity: '0.3' }}>
              <FlexBox alignItems="center" margin="0 0 12px 0" style={card}>
                <Box
                  width="36px" height="36px"
                  backgroundColor="#b45309"
                  style={{ borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}
                >
                  <Text fontSize="16px" color="white" fontWeight="bold" margin="0">{i + 1}</Text>
                </Box>
                <Text fontSize="22px" color="#1e293b" margin="0 0 0 16px">{item}</Text>
              </FlexBox>
            </Appear>
          ))}
        </FlexBox>
      </FlexBox>
    </Slide>
  );
}

// ─── Content Slide ─────────────────────────────

function renderContent(slide: SlideData, idx: number, theme: SlideThemeConfig) {
  const imageUrl = slide.image_url ? getMediaUrl(slide.image_url) : null;

  return (
    <Slide key={idx} {...slideBgProps(theme, 'content')}>
      <FlexBox flexDirection="column" alignItems="flex-start" height="100%" padding="5% 8%">
        <Heading fontSize="h2" fontWeight="700" color="#3d2b1f" margin="0 0 8px 0">
          {slide.title}
        </Heading>
        <Box width="80px" height="4px" backgroundColor="#b45309" style={{ borderRadius: '4px' }} />

        <FlexBox flex={1} margin="24px 0 0 0" width="100%">
          <Box flex={imageUrl ? 3 : 1} style={card} margin="0">
            <Text fontSize="22px" color="#334155" lineHeight="1.7" margin="0">
              {slide.body}
            </Text>
          </Box>
          {imageUrl && (
            <Box flex={2} margin="0 0 0 24px">
              <img
                src={imageUrl}
                alt={slide.title}
                style={{ width: '100%', borderRadius: '12px', boxShadow: '0 8px 24px rgba(0,0,0,0.15)' }}
              />
            </Box>
          )}
        </FlexBox>
      </FlexBox>
    </Slide>
  );
}

// ─── Key Terms Slide ───────────────────────────

function renderKeyTerms(slide: SlideData, idx: number, theme: SlideThemeConfig) {
  const terms = slide.terms || [];

  return (
    <Slide key={idx} {...slideBgProps(theme, 'terms')}>
      <FlexBox flexDirection="column" alignItems="flex-start" height="100%" padding="5% 8%">
        <Heading fontSize="h2" fontWeight="700" color="#3d2b1f" margin="0 0 8px 0">
          {slide.title}
        </Heading>
        <Box width="80px" height="4px" backgroundColor="#b45309" style={{ borderRadius: '4px' }} />

        <Grid gridTemplateColumns={terms.length >= 4 ? '1fr 1fr' : '1fr'} gridGap="12px" flex={1} width="100%" margin="24px 0 0 0" alignContent="center">
          {terms.map((t, i) => (
            <Appear key={i}>
              <Box style={{ ...card, borderLeft: '4px solid #b45309' }} padding="16px 24px">
                <Text fontSize="20px" fontWeight="bold" color="#92400e" margin="0 0 4px 0">
                  {t.term}
                </Text>
                <Text fontSize="18px" color="#475569" margin="0">
                  {t.definition}
                </Text>
              </Box>
            </Appear>
          ))}
        </Grid>
      </FlexBox>
    </Slide>
  );
}

// ─── Quiz Slide ────────────────────────────────

function renderQuiz(slide: SlideData, idx: number, theme: SlideThemeConfig) {
  const options = slide.options || [];
  const answerIdx = slide.answer ?? -1;
  const letters = ['A', 'B', 'C', 'D', 'E', 'F'];

  return (
    <Slide key={idx} {...slideBgProps(theme, 'content')}>
      <FlexBox flexDirection="column" alignItems="flex-start" height="100%" padding="5% 8%">
        <Heading fontSize="h2" fontWeight="700" color="#3d2b1f" margin="0 0 8px 0">
          {slide.title}
        </Heading>
        <Box width="80px" height="4px" backgroundColor="#059669" style={{ borderRadius: '4px' }} />

        {/* Question */}
        <Box style={{ ...card, borderLeft: '4px solid #059669' }} margin="20px 0 16px 0" width="100%">
          <Text fontSize="24px" fontWeight="600" color="#1e293b" margin="0">
            {slide.question}
          </Text>
        </Box>

        {/* Options */}
        <FlexBox flexDirection="column" flex={1} justifyContent="center" width="100%">
          {options.map((option, i) => {
            const isCorrect = i === answerIdx;
            return (
              <Appear key={i}>
                <FlexBox
                  alignItems="center"
                  margin="0 0 10px 0"
                  style={{
                    ...card,
                    backgroundColor: isCorrect ? 'rgba(209,250,229,0.9)' : 'rgba(255,255,255,0.82)',
                    borderLeft: isCorrect ? '4px solid #059669' : '4px solid transparent',
                  }}
                  padding="12px 20px"
                >
                  <Box
                    width="32px" height="32px"
                    backgroundColor={isCorrect ? '#059669' : '#94a3b8'}
                    style={{ borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}
                  >
                    <Text fontSize="14px" color="white" fontWeight="bold" margin="0">{letters[i]}</Text>
                  </Box>
                  <Text fontSize="20px" color={isCorrect ? '#065f46' : '#334155'} fontWeight={isCorrect ? 'bold' : 'normal'} margin="0 0 0 14px">
                    {option}
                  </Text>
                  {isCorrect && (
                    <Text fontSize="20px" color="#059669" margin="0 0 0 auto">✔</Text>
                  )}
                </FlexBox>
              </Appear>
            );
          })}
        </FlexBox>
      </FlexBox>
    </Slide>
  );
}

// ─── Summary Slide ─────────────────────────────

function renderSummary(slide: SlideData, idx: number, theme: SlideThemeConfig) {
  const items = slide.items || [];

  return (
    <Slide key={idx} {...slideBgProps(theme, 'summary')}>
      <FlexBox flexDirection="column" alignItems="flex-start" height="100%" padding="5% 8%">
        <Heading fontSize="h1" fontWeight="800" color="#3d2b1f" margin="0 0 4px 0">
          {slide.title}
        </Heading>
        <Text fontSize="16px" color="#8b7355" margin="0 0 24px 0" style={{ textTransform: 'uppercase' as const, letterSpacing: '2px' }}>
          Негізгі тұжырымдар
        </Text>

        <FlexBox flexDirection="column" flex={1} justifyContent="center" width="100%">
          {items.map((item, i) => (
            <Appear key={i}>
              <FlexBox alignItems="center" margin="0 0 10px 0" style={card}>
                <Box
                  width="28px" height="28px"
                  backgroundColor="#059669"
                  style={{ borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}
                >
                  <Text fontSize="14px" color="white" fontWeight="bold" margin="0">✓</Text>
                </Box>
                <Text fontSize="20px" color="#1e293b" margin="0 0 0 14px">{item}</Text>
              </FlexBox>
            </Appear>
          ))}
        </FlexBox>
      </FlexBox>
    </Slide>
  );
}
