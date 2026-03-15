/**
 * Quiz Sound Manager — procedural sounds via Web Audio API.
 * No external mp3 files needed.
 */

type OscType = OscillatorType; // 'sine' | 'square' | 'triangle' | 'sawtooth'

interface Note {
  freq: number;
  dur: number;
  type?: OscType;
  gain?: number;
  delay?: number;
}

const MUTE_KEY = 'quiz_sound_muted';

export class QuizSoundManager {
  private ctx: AudioContext | null = null;
  private _muted: boolean;

  constructor() {
    this._muted =
      typeof window !== 'undefined'
        ? localStorage.getItem(MUTE_KEY) === 'true'
        : false;
  }

  get muted() {
    return this._muted;
  }

  toggleMute(): boolean {
    this._muted = !this._muted;
    if (typeof window !== 'undefined') {
      localStorage.setItem(MUTE_KEY, String(this._muted));
    }
    return this._muted;
  }

  private getCtx(): AudioContext | null {
    if (typeof window === 'undefined') return null;
    if (!this.ctx) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      this.ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
    return this.ctx;
  }

  private notes(notes: Note[]) {
    if (this._muted) return;
    const ctx = this.getCtx();
    if (!ctx) return;

    const now = ctx.currentTime;
    for (const { freq, dur, type = 'sine', gain = 0.3, delay = 0 } of notes) {
      const osc = ctx.createOscillator();
      const g = ctx.createGain();

      osc.type = type;
      osc.frequency.value = freq;

      g.gain.setValueAtTime(gain, now + delay);
      g.gain.exponentialRampToValueAtTime(0.001, now + delay + dur);

      osc.connect(g);
      g.connect(ctx.destination);

      osc.start(now + delay);
      osc.stop(now + delay + dur);
    }
  }

  /** Lobby — soft welcome chime */
  lobby() {
    this.notes([
      { freq: 523, dur: 0.2, gain: 0.2 }, // C5
      { freq: 659, dur: 0.3, delay: 0.15, gain: 0.2 }, // E5
    ]);
  }

  /** New question appears — attention getter */
  questionAppear() {
    this.notes([
      { freq: 587, dur: 0.12, type: 'triangle', gain: 0.25 }, // D5
      { freq: 784, dur: 0.2, type: 'triangle', delay: 0.1, gain: 0.25 }, // G5
    ]);
  }

  /** Timer tick (< 5 sec) — short click */
  tick() {
    this.notes([{ freq: 800, dur: 0.05, type: 'square', gain: 0.12 }]);
  }

  /** Time expired — low buzzer */
  timeUp() {
    this.notes([{ freq: 200, dur: 0.4, type: 'square', gain: 0.25 }]);
  }

  /** Correct answer — ascending chime */
  correct() {
    this.notes([
      { freq: 523, dur: 0.12, gain: 0.25 }, // C5
      { freq: 659, dur: 0.12, delay: 0.1, gain: 0.25 }, // E5
      { freq: 784, dur: 0.2, delay: 0.2, gain: 0.3 }, // G5
    ]);
  }

  /** Wrong answer — descending buzz */
  incorrect() {
    this.notes([
      { freq: 330, dur: 0.15, type: 'sawtooth', gain: 0.15 }, // E4
      { freq: 262, dur: 0.25, type: 'sawtooth', delay: 0.12, gain: 0.15 }, // C4
    ]);
  }

  /** Streak bonus — ascending sweep */
  streak() {
    if (this._muted) return;
    const ctx = this.getCtx();
    if (!ctx) return;

    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const g = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(400, now);
    osc.frequency.exponentialRampToValueAtTime(1200, now + 0.3);

    g.gain.setValueAtTime(0.2, now);
    g.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

    osc.connect(g);
    g.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.35);
  }

  /** Question result reveal — fast arpeggio */
  result() {
    this.notes([
      { freq: 392, dur: 0.1, type: 'triangle', gain: 0.2 }, // G4
      { freq: 494, dur: 0.1, type: 'triangle', delay: 0.08, gain: 0.2 }, // B4
      { freq: 587, dur: 0.1, type: 'triangle', delay: 0.16, gain: 0.2 }, // D5
      { freq: 784, dur: 0.25, type: 'triangle', delay: 0.24, gain: 0.25 }, // G5
    ]);
  }

  /** Quiz finished — victory fanfare */
  victory() {
    this.notes([
      { freq: 523, dur: 0.15, gain: 0.3 }, // C5
      { freq: 659, dur: 0.15, delay: 0.12, gain: 0.3 }, // E5
      { freq: 784, dur: 0.15, delay: 0.24, gain: 0.3 }, // G5
      { freq: 1047, dur: 0.4, delay: 0.36, gain: 0.35 }, // C6
    ]);
  }

  /** Podium countdown — short beep per number */
  podiumCountdown() {
    this.notes([{ freq: 880, dur: 0.1, type: 'triangle', gain: 0.25 }]); // A5
  }

  /** Podium reveal — extended triumphant fanfare */
  podiumReveal() {
    this.notes([
      { freq: 523, dur: 0.15, gain: 0.3 },                    // C5
      { freq: 659, dur: 0.15, delay: 0.12, gain: 0.3 },       // E5
      { freq: 784, dur: 0.15, delay: 0.24, gain: 0.3 },       // G5
      { freq: 1047, dur: 0.2, delay: 0.36, gain: 0.35 },      // C6
      { freq: 784, dur: 0.12, delay: 0.52, gain: 0.25 },      // G5
      { freq: 1047, dur: 0.12, delay: 0.62, gain: 0.3 },      // C6
      { freq: 1319, dur: 0.5, delay: 0.72, gain: 0.35 },      // E6 (sustained)
    ]);
  }

  /** Power-up activated — ascending sparkle */
  powerupActivate() {
    this.notes([
      { freq: 600, dur: 0.08, type: 'triangle', gain: 0.2 },
      { freq: 900, dur: 0.08, type: 'triangle', delay: 0.06, gain: 0.25 },
      { freq: 1200, dur: 0.15, type: 'triangle', delay: 0.12, gain: 0.3 },
    ]);
  }

  dispose() {
    if (this.ctx) {
      this.ctx.close();
      this.ctx = null;
    }
  }
}
